"""Read-only, provenance-preserving education. Never changes safety or workout state."""
import hashlib
import json
import re
from functools import lru_cache
from .media_assets import data_dir
from . import knowledge_model

@lru_cache(maxsize=4)
def _read(path,mtime):
    with open(path) as f:return json.load(f)

def read(name):
    p=data_dir()/'knowledge'/name
    return _read(str(p),p.stat().st_mtime_ns)

def knowledge():return read('muscles-and-order.json')

def muscle(term):
    term=term.strip().lower();k=knowledge()
    found=next((m for m in k['muscles'] if term in [m['id'],*m['aliases']]),None)
    if not found:return None
    return {**found,'sources':[k['sources'][s] for s in found['sources']], 'provenance':k['provenance']}

def order(items=None):
    k=knowledge();o=k['ordering']
    return {**o,'sources':[k['sources'][s] for s in o['sources']],
            'planned_exercises':[{'position':i+1,'exercise_id':e['exercise_id'],'name':e['name']} for i,e in enumerate(items or [])],
            'mode':'deterministic_policy','state_changed':False}

def exercise(row):
    d=row['data'];m=muscle(d.get('target',''))
    return {'exercise_id':row['id'],'name':row['name'],'primary_target':d.get('target'),
            'secondary_targets':d.get('secondary_muscles',[]),'muscle_function':m,
            'equipment':d.get('equipment'),'instructions':d.get('instruction_steps',{}).get('en',[]),
            'source':{'name':row.get('source','exercise catalog'),'commit':row.get('source_commit'),'record_hash':row.get('source_hash')},
            'provenance':'Target labels and instructions retrieved from the source record; not neural predictions.',
            'note':'A target label describes the source exercise category. It does not prove muscle activation percentages, expected results or suitability for you.'}

@lru_cache(maxsize=6)
def _file_hash(path,mtime,size):
    with open(path,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def digest(path):
    stat=path.stat()
    return _file_hash(str(path),stat.st_mtime_ns,stat.st_size)

def model_status():
    try:
        r=read('training-report.json');p=data_dir()/'knowledge'/'exercise-model.json'
        if digest(p)!=r['model_sha256']:raise ValueError('Model checksum mismatch')
        if digest(data_dir()/'exercises.json')!=r['source_sha256']:raise ValueError('Source dataset changed; retrain before serving suggestions')
        knowledge_model.validate(read('exercise-model.json'))
        if r['source_sha256']!=read('exercise-model.json')['source_sha256']:raise ValueError('Model/report source mismatch')
        return {'status':'trained_experimental','version':r['version'],'source_count':r['source_count'],
                'partition_counts':{k:v['count'] for k,v in r['partitions'].items()},'test_accuracy':r['metrics']['test']['accuracy'],
                'test_macro_f1':r['metrics']['test']['macro_f1_supported_classes'],'limitations':r['limitations']}
    except (OSError,ValueError,KeyError,TypeError):
        return {'status':'unavailable','note':'Source lookup remains available; no model prediction will be invented.'}

def classify(name):
    if model_status()['status']!='trained_experimental':return {'status':'unavailable','suggestions':[]}
    try:return knowledge_model.predict(read('exercise-model.json'),name)
    except (ValueError,KeyError,TypeError):return {'status':'unavailable','suggestions':[]}

def answer(message,rows,items=None):
    """Bounded educational intents, not a general-purpose language model."""
    text=' '.join(knowledge_model.words(message))
    if re.search(r'\b(first|order|sequence|then)\b',text):
        o=order(items);lines=[o['principle']]+[f"{i+1}. {s['stage']}: {s['instruction']}" for i,s in enumerate(o['steps'])]
        if items:lines.append('Your saved main-work order: '+' → '.join(e['name'] for e in items)+'. This is your existing plan; this answer does not reorder it.')
        lines.append('Sources: '+'; '.join(s['url'] for s in o['sources']))
        return {'reply':'\n\n'.join(lines),'mode':'sourced_knowledge','knowledge':o}
    # Longest full exercise name wins over an incidental muscle word.
    exact=sorted([r for r in rows if ' '+ ' '.join(knowledge_model.words(r['name']))+' ' in ' '+text+' '],key=lambda r:len(r['name']),reverse=True)
    if exact:
        e=exercise(exact[0]);m=e['muscle_function'];reply=f"{e['name']}: the source lists {e['primary_target']} as its primary target."
        if e['secondary_targets']:reply+=' Secondary targets: '+', '.join(e['secondary_targets'])+'.'
        if m:reply+=' '+m['function']
        reply+=' Open this exact exercise in Library for the animation and step-by-step instructions. '+e['note']
        if m:reply+='\nSource: '+m['sources'][0]['url']
        return {'reply':reply,'mode':'sourced_knowledge','knowledge':e}
    for m in sorted(knowledge()['muscles'],key=lambda m:max(map(len,[m['id'],*m['aliases']])),reverse=True):
        if any(' '+alias+' ' in ' '+text+' ' for alias in [m['id'],*m['aliases']]):
            info=muscle(m['id']);examples=[r['name'] for r in rows if r['data'].get('target')==m['id']][:3]
            reply=info['function']
            if examples:reply+=' Catalog examples: '+', '.join(examples)+'. These are reference examples, not a prescribed workout.'
            reply+='\nSource: '+info['sources'][0]['url']
            return {'reply':reply,'mode':'sourced_knowledge','knowledge':info}
    return None
