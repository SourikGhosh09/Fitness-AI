"""Run one Notion synchronizer beside the API, never inside a mobile app/function."""
import argparse, contextlib, errno, hashlib, json, os, tempfile, time, uuid
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import HTTPError, URLError
from sqlalchemy import select, insert, update, delete, text
from . import db, notion_sync

class NotionError(RuntimeError):
    def __init__(self, status):
        self.status = status
        super().__init__('Notion request failed; check private worker status')

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None

class NotionClient:
    def __init__(self, token=None, source=None, sleep=time.sleep):
        self.token = token or os.getenv('NOTION_TOKEN')
        self.source = str(uuid.UUID(source or os.environ['NOTION_DATA_SOURCE_ID']))
        if not self.token: raise ValueError('NOTION_TOKEN is not configured')
        self.sleep = sleep
        self.opener = build_opener(NoRedirect())

    def request(self, method, path, payload=None):
        # Fixed HTTPS origin, no redirects and no caller-provided URLs.
        raw = json.dumps(payload,allow_nan=False).encode() if payload is not None else None
        for attempt in range(4):
            self.sleep(.35)
            req = Request('https://api.notion.com/v1/'+path, data=raw, method=method,
                headers={'Authorization':'Bearer '+self.token,'Notion-Version':'2025-09-03','Content-Type':'application/json'})
            try:
                with self.opener.open(req,timeout=20) as response:
                    body = response.read(8*1024*1024+1)
                    if len(body)>8*1024*1024: raise NotionError('response_too_large')
                    return json.loads(body)
            except HTTPError as exc:
                if exc.code not in (429,500,502,503,504) or attempt==3: raise NotionError(exc.code) from None
                try: delay = float(exc.headers.get('Retry-After',2**attempt))
                except (ValueError,TypeError): delay = 2**attempt
                if delay>60: raise NotionError('rate_limited') from None
                self.sleep(max(0,delay))
            except (URLError,TimeoutError):
                if attempt==3: raise NotionError('network') from None
                self.sleep(2**attempt)

    def pages(self):
        pages = {}; cursor = None; seen = set()
        for _ in range(500):
            body = {'page_size':100}
            if cursor: body['start_cursor']=cursor
            result = self.request('POST','data_sources/'+self.source+'/query',body)
            if not isinstance(result.get('results'),list) or not isinstance(result.get('has_more'),bool): raise NotionError('invalid_page')
            for page in result['results']:
                if page.get('object')!='page': raise NotionError('unexpected_object')
                ident = str(uuid.UUID(page['id']))
                # A concurrent edit during pagination is retried, never guessed.
                if ident in pages and pages[ident] != page: raise NotionError('changing_snapshot')
                pages[ident]=page
            if not result['has_more']: return list(pages.values())
            cursor = result.get('next_cursor')
            if not cursor or cursor in seen: raise NotionError('invalid_cursor')
            seen.add(cursor)
        raise NotionError('scan_limit_exceeded')

    def purge(self, page_id):
        page_id=str(uuid.UUID(page_id))
        page=self.request('GET','pages/'+page_id)
        props={}
        # Clear collection properties as well as trashing the page. Notion's
        # own history/backups may retain versions; never call this hard erasure.
        for name,p in page.get('properties',{}).items():
            kind=p.get('type')
            if kind in ('rich_text','title'): props[name]={kind:[]}
            elif kind in ('number','date','select'): props[name]={kind:None}
            elif kind=='checkbox': props[name]={kind:False}
        self.request('PATCH','pages/'+page_id,{'properties':props,'in_trash':True})

@contextlib.contextmanager
def worker_lock(database):
    if database.dialect.name=='postgresql':
        with database.connect() as c:
            if not c.execute(text('SELECT pg_try_advisory_lock(518823417)')).scalar():
                yield False; return
            try: yield True
            finally: c.execute(text('SELECT pg_advisory_unlock(518823417)'))
    elif database.dialect.name=='sqlite':
        key=hashlib.sha256(str(database.url).encode()).hexdigest()[:20]
        with open(os.path.join(tempfile.gettempdir(),'fitness-notion-'+key+'.lock'),'a+b') as f:
            if os.name=='nt':
                import msvcrt
                # Windows locks a byte range; all workers use the first byte.
                f.seek(0,os.SEEK_END)
                if not f.tell(): f.write(b'\0'); f.flush()
                f.seek(0)
                lock=lambda: msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
                unlock=lambda: msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                lock=lambda: fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
                unlock=lambda: fcntl.flock(f,fcntl.LOCK_UN)
            try: lock()
            except OSError as exc:
                if exc.errno not in (errno.EACCES,errno.EAGAIN,errno.EDEADLK): raise
                yield False; return
            try: yield True
            finally: unlock()
    else: raise ValueError('Notion worker requires PostgreSQL or local SQLite')

def save_state(database, values):
    with database.begin() as c:
        old=c.execute(select(db.notion_worker_state.c.data).where(db.notion_worker_state.c.id=='global')).scalar_one_or_none()
        data={**(old or {}),**values}
        if old is not None: c.execute(update(db.notion_worker_state).where(db.notion_worker_state.c.id=='global').values(data=data))
        else: c.execute(insert(db.notion_worker_state).values(id='global',data=data))

def cycle(database, client):
    with worker_lock(database) as acquired:
        if not acquired: return {'status':'another_worker_running'}
        try:
            # Capture current consent generation BEFORE making external requests.
            with database.connect() as c:
                links={r['user_id']:r['code'] for r in c.execute(select(db.notion_links).where(db.notion_links.c.enabled==True)).mappings()}
            pages=client.pages()
            with database.begin() as c: result=notion_sync.apply_snapshot(c,pages,links)
            with database.connect() as c: purges=list(c.execute(select(db.notion_purges.c.id)).scalars())
            cleanup_errors=0
            for page_id in purges:
                try: client.purge(page_id)
                except (NotionError,ValueError):
                    cleanup_errors+=1
                    with database.begin() as c: c.execute(update(db.notion_purges).where(db.notion_purges.c.id==page_id).values(attempts=db.notion_purges.c.attempts+1))
                else:
                    with database.begin() as c: c.execute(delete(db.notion_purges).where(db.notion_purges.c.id==page_id))
            result.update(status='cleanup_pending' if cleanup_errors else 'ok',last_success_at=time.time(),cleanup_pending=cleanup_errors,error=None,configured=True)
            save_state(database,result)
            return result
        except Exception as exc:
            save_state(database,{'status':'retrying','last_attempt_at':time.time(),'error':str(exc.status) if isinstance(exc,NotionError) else type(exc).__name__})
            raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--once',action='store_true');p.add_argument('--interval-seconds',type=int,default=300)
    a=p.parse_args()
    if not 60<=a.interval_seconds<=86400: p.error('interval must be 60..86400 seconds')
    try: client=NotionClient(); database=db.make_engine()
    except (ValueError,KeyError): p.exit(2,'Configure NOTION_TOKEN and NOTION_DATA_SOURCE_ID on the server. No credential belongs in the app.\n')
    while True:
        try: print(json.dumps(cycle(database,client)),flush=True)
        except Exception as exc:
            print(json.dumps({'status':'retrying','error_type':type(exc).__name__}),flush=True)
            if a.once: raise SystemExit(1)
        if a.once: return
        time.sleep(a.interval_seconds)
if __name__=='__main__':main()
