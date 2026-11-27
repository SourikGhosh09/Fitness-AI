// Pure logbook helpers: dates, timers, totals, export text. No React or native imports.
export type LogSet={kind:'reps'|'seconds';weight_kg:number|null;reps:number|null;rir:number|null;done:boolean;completed_at:number|null;rest_seconds:number|null};
export type LogExercise={exercise_id:string|null;name:string;target:string;baseline:string;notes:string;rest_seconds:number;sets:LogSet[]};
export type LogCheck={text:string;done:boolean};
export type LogSession={
 version:number;title:string;status:'planned'|'in_progress'|'completed';started_at:number|null;ended_at:number|null;paused_seconds:number;
 body_weight_kg:number|null;sleep_hours:number|null;energy:number|null;soreness_pre:number|null;pain_pre:number|null;soreness_post:number|null;pain_post:number|null;
 difficulty:string;technique:string;notes:string;exercises:LogExercise[];warmup:LogCheck[];stretch:LogCheck[];cooldown:LogCheck[];
 cardio:{activity:string;target:string;minutes:number|null};
};
export type LogSummary={date:string;title:string;status:string;sets_total:number;sets_done:number;volume_kg:number};

const pad=(n:number)=>String(n).padStart(2,'0');
export function localDate(d:Date=new Date()){return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())}`;}
export function isIsoDate(v:string){
 if(!/^\d{4}-\d{2}-\d{2}$/.test(v))return false;
 const [y,m,d]=v.split('-').map(Number) as [number,number,number];
 const t=new Date(Date.UTC(y,m-1,d));
 return t.getUTCFullYear()===y&&t.getUTCMonth()===m-1&&t.getUTCDate()===d;
}
export function shiftDate(iso:string,days:number){
 if(!isIsoDate(iso))throw new Error('Invalid date');
 const [y,m,d]=iso.split('-').map(Number) as [number,number,number];
 const t=new Date(Date.UTC(y,m-1,d+days));
 return `${t.getUTCFullYear()}-${pad(t.getUTCMonth()+1)}-${pad(t.getUTCDate())}`;
}
export function weekStart(iso:string){
 const [y,m,d]=iso.split('-').map(Number) as [number,number,number];
 const dow=(new Date(Date.UTC(y,m-1,d)).getUTCDay()+6)%7; // Monday = 0
 return shiftDate(iso,-dow);
}
export function weekDates(iso:string){const s=weekStart(iso);return Array.from({length:7},(_,i)=>shiftDate(s,i));}
const names=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'];
export function dayLabel(iso:string){const i=weekDates(iso).indexOf(iso);return `${names[i]} ${Number(iso.slice(8))}`;}

export function formatClock(total:number){
 const s=Math.max(0,Math.floor(Number.isFinite(total)?total:0));
 const h=Math.floor(s/3600),m=Math.floor(s%3600/60),r=s%60;
 return h?`${h}:${pad(m)}:${pad(r)}`:`${m}:${pad(r)}`;
}
/** Seconds left for a countdown that ends at `endsAt` (epoch seconds). Based on the clock, so backgrounding cannot drift it. */
export function remaining(endsAt:number,now:number){return Math.max(0,Math.ceil(endsAt-now));}
/** Active training time in seconds. Uses stored epoch seconds so it survives app restarts. */
export function elapsedSeconds(s:Pick<LogSession,'started_at'|'ended_at'|'paused_seconds'>,now:number,pausedSince:number|null=null){
 if(s.started_at===null)return 0;
 const end=s.ended_at??pausedSince??now;
 return Math.max(0,Math.floor(end-s.started_at)-s.paused_seconds);
}
export function parseNum(text:string,min=0,max=1000):number|null{
 const t=text.trim().replace(',','.');
 if(t==='')return null;
 const n=Number(t);
 return Number.isFinite(n)?Math.min(max,Math.max(min,n)):null;
}
export function numText(n:number|null){return n===null||n===undefined?'':String(n);}

export function emptySession(title='Workout'):LogSession{
 return {version:0,title,status:'planned',started_at:null,ended_at:null,paused_seconds:0,body_weight_kg:null,sleep_hours:null,energy:null,soreness_pre:null,pain_pre:null,soreness_post:null,pain_post:null,difficulty:'',technique:'',notes:'',exercises:[],warmup:[],stretch:[],cooldown:[],cardio:{activity:'',target:'',minutes:null}};
}
export function newSet(prev?:LogSet,kind:'reps'|'seconds'='reps'):LogSet{
 return {kind:prev?.kind??kind,weight_kg:prev?.weight_kg??null,reps:prev?.reps??null,rir:prev?.rir??null,done:false,completed_at:null,rest_seconds:null};
}
export function newExercise(name:string,exerciseId:string|null=null):LogExercise{
 return {exercise_id:exerciseId,name:name.trim().slice(0,120),target:'',baseline:'',notes:'',rest_seconds:90,sets:[newSet(),newSet(),newSet()]};
}
/** Mark a set done or undone. Returns the new session and the rest seconds to start (0 = none). */
export function setDone(s:LogSession,ei:number,si:number,done:boolean,now:number):{session:LogSession;rest:number}{
 const ex=s.exercises[ei];const set=ex?.sets[si];
 if(!ex||!set)return {session:s,rest:0};
 const exercises=s.exercises.map((e,i)=>i!==ei?e:{...e,sets:e.sets.map((x,j)=>j!==si?x:{...x,done,completed_at:done?now:null})});
 let status=s.status;let started=s.started_at;
 if(done&&status==='planned'){status='in_progress';started=started??now;}
 const last=ex.sets.every((x,j)=>j===si?true:x.done);
 const rest=done&&!last?(set.rest_seconds??ex.rest_seconds):0;
 return {session:{...s,exercises,status,started_at:started},rest};
}
export function stats(s:LogSession){
 const sets=s.exercises.flatMap(e=>e.sets.map(x=>({...x})));
 const done=sets.filter(x=>x.done);
 const volume=done.reduce((a,x)=>a+(x.kind==='reps'?(x.weight_kg??0)*(x.reps??0):0),0);
 return {total:sets.length,done:done.length,volume:Math.round(volume*100)/100};
}
/** Request body for PUT /logs/{date}: only fields the API accepts. */
export function toPayload(l:LogSession&Record<string,unknown>):LogSession{
 const {date:_d,updated_at:_u,previous:_p,...rest}=l as any;
 return rest as LogSession;
}
export function sessionText(date:string,s:LogSession){
 const st=stats(s);
 const num=(v:number|null,u='')=>v===null?'-':v+u;
 const lines=[`${dayLabel(date)} (${date}) - ${s.title}`,`Status: ${s.status} | Time: ${formatClock(elapsedSeconds(s,s.ended_at??s.started_at??0))} | Sets: ${st.done}/${st.total} | Volume: ${st.volume} kg`,
  `Body weight: ${num(s.body_weight_kg,' kg')} | Sleep: ${num(s.sleep_hours,' h')} | Energy: ${num(s.energy,'/10')}`,
  `Pre soreness/pain: ${num(s.soreness_pre)}/${num(s.pain_pre)} of 10`];
 const check=(title:string,items:LogCheck[])=>{if(items.length){lines.push('',title+':');items.forEach(i=>lines.push(`${i.done?'[x]':'[ ]'} ${i.text}`));}};
 check('WARM-UP',s.warmup);
 for(const e of s.exercises){
  lines.push('',e.target?`${e.name} - target ${e.target}`:e.name);
  e.sets.forEach((x,i)=>lines.push(`Set ${i+1}: ${x.kind==='seconds'?`${num(x.reps)} sec`:`${num(x.weight_kg,' kg')} x ${num(x.reps)} reps`}${x.rir===null?'':` | RIR ${x.rir}`} | ${x.done?'done':'not done'}`));
  if(e.notes)lines.push('Notes: '+e.notes);
 }
 if(s.cardio.activity||s.cardio.minutes!==null||s.cardio.target)lines.push('',`CONDITIONING: ${s.cardio.activity||'-'} ${num(s.cardio.minutes,' min')}${s.cardio.target?` (target ${s.cardio.target})`:''}`);
 check('STRETCHING',s.stretch);check('COOLDOWN',s.cooldown);
 lines.push('',`Review: difficulty ${s.difficulty||'-'} | technique ${s.technique||'-'} | soreness after ${num(s.soreness_post)}/10 | pain after ${num(s.pain_post)}/10`);
 if(s.notes)lines.push('Notes: '+s.notes);
 return lines.join('\n');
}
