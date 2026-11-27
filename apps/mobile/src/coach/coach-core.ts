// Pure coach logic: safety gate, prompt/context, action parsing and validation, routing.
// No React or native imports so it can be unit tested with node.

export const ACTION_MARK='ACTION:';
export type CoachAction=
 |{type:'log_set';exercise:string;set_number:number;reps:number;load_kg:number;rpe:number|null;pain:boolean;skipped:boolean}
 |{type:'substitute';exercise:string}
 |{type:'regenerate';reason:'variety'|'equipment'|'time'|'fatigue'}
 |{type:'set_training_days';days:number[]};
export type WorkoutItem={exercise_id:string;name:string;sets:number;reps?:number;rep_range?:number[];load_kg?:number|null;rpe?:number;rest_seconds?:number};

const EMERGENCY=/\b(chest pain|chest pressure|fainting|faint|severe breathlessness|can'?t breathe)\b/i;
const PAIN=/\b(pain|painful|hurt|hurts|injury|injured|dizzy|numb|numbness)\b/i;
export function safetyCheck(text:string):string|null{
 if(EMERGENCY.test(text))return 'Stop training and seek urgent medical help for chest pain, chest pressure, fainting or severe breathlessness.';
 if(PAIN.test(text))return 'Pause if you have pain or alarming symptoms. Do not train through it. Update your readiness with pain marked so the safety layer can review your session, and see a professional if it persists.';
 return null;
}

export const SYSTEM_PROMPT=[
 'You are the coach inside the Fitness AI app. Be warm, brief and practical: 1 to 4 short sentences.',
 'The STATE block is the only truth about the user plan. Never invent exercises, weights, sets or reps that are not in STATE.',
 'You cannot diagnose or treat pain. If the user mentions pain or injury, tell them to stop and see a professional.',
 'To change something, end your reply with one line: '+ACTION_MARK+' followed by one JSON object, and say in your sentence what you are proposing. The user confirms and the app engine validates it.',
 'Allowed actions: {"type":"log_set","exercise":"name from STATE","set_number":1,"reps":8,"load_kg":40,"rpe":7} | {"type":"substitute","exercise":"name from STATE"} | {"type":"regenerate","reason":"variety|equipment|time|fatigue"} | {"type":"set_training_days","days":[0,2,4]} (0=Mon).',
 'Only emit an action when the user clearly asks for that change. Otherwise just answer.',
].join('\n');

export type CoachState={profile?:any;week?:any;workout?:any;logged?:Record<string,boolean>};
const cut=(s:unknown,n:number)=>String(s??'').slice(0,n);
export function buildState(st:CoachState):string{
 const L:string[]=['[STATE]'];const p=st.profile;
 if(p){const g=p.goals?Object.entries(p.goals).map(([k,v])=>`${k} ${v}%`).join(', '):'';L.push(`User: ${cut(p.display_name,30)}; goals ${g}; ${p.minutes} min sessions; training days ${(p.days||[]).map((d:number)=>['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d]).join('/')}; equipment ${(p.equipment||[]).join(', ')}.`);}
 const w=st.workout;
 if(w&&Array.isArray(w.items)){
  L.push(`Today (${w.status}${w.kind==='recovery'?', rest day':''}): readiness ${w.readiness??'?'}.`);
  w.items.slice(0,10).forEach((i:WorkoutItem,n:number)=>{
   const done=Array.from({length:i.sets},(_,k)=>k+1).filter(k=>st.logged?.[`${w.id}:${i.exercise_id}:${k}`]).length;
   const reps=i.rep_range?`${i.rep_range[0]}-${i.rep_range[1]}`:i.reps;
   L.push(`${n+1}. ${cut(i.name,50)}: ${i.sets}x${reps}${i.load_kg!=null?` @${i.load_kg}kg`:''} RPE ${i.rpe??'?'}, ${done}/${i.sets} sets logged`);
  });
 }else L.push('Today: no workout generated yet (user must do the readiness check on the Today tab).');
 const wk=st.week;
 if(wk?.days)L.push('Week: '+wk.days.map((d:any)=>`${cut(d.weekday,3)} ${cut(d.title,28)} [${d.status}]`).join('; ')+'.');
 if(wk?.recovery_snapshot){const r=Object.entries(wk.recovery_snapshot).slice(0,6).map(([m,v]:any)=>`${m} ${String(v.band).replace('_',' ')}`).join(', ');if(r)L.push('Recovery: '+r+'.');}
 L.push('[/STATE]');return L.join('\n');
}
export function userTurn(state:string,text:string){return `${state}\n\nUser: ${text}`;}

const norm=(s:string)=>s.toLowerCase().replace(/[^a-z0-9 ]/g,' ').replace(/\s+/g,' ').trim();
export function resolveExercise(name:string,items:WorkoutItem[]):WorkoutItem|null{
 const q=norm(name);if(!q)return null;
 const exact=items.find(i=>norm(i.name)===q);if(exact)return exact;
 const num=/^\d+$/.test(q)?items[Number(q)-1]:undefined;if(num)return num;
 const hits=items.filter(i=>norm(i.name).includes(q)||q.includes(norm(i.name)));
 if(hits.length===1)return hits[0]!;
 const toks=q.split(' ').filter(t=>t.length>2);
 const scored=items.map(i=>({i,s:toks.filter(t=>norm(i.name).includes(t)).length})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s);
 if(scored.length&&(scored.length===1||scored[0]!.s>scored[1]!.s))return scored[0]!.i;
 return null;
}

const int=(v:unknown)=>typeof v==='number'&&Number.isInteger(v);
const num=(v:unknown)=>typeof v==='number'&&Number.isFinite(v);
export function validateAction(raw:any):CoachAction|null{
 if(!raw||typeof raw!=='object')return null;
 switch(raw.type){
  case 'log_set':{
   const skipped=raw.skipped===true,pain=raw.pain===true;
   if(typeof raw.exercise!=='string'||!int(raw.set_number)||raw.set_number<1||raw.set_number>20)return null;
   const reps=skipped?0:raw.reps,load=skipped?0:(raw.load_kg??0);
   if(!int(reps)||reps<0||reps>200||!num(load)||load<0||load>600)return null;
   const rpe=skipped?null:raw.rpe;
   if(!skipped&&(!num(rpe)||(rpe as number)<1||(rpe as number)>10))return null;
   return {type:'log_set',exercise:raw.exercise.slice(0,80),set_number:raw.set_number,reps,load_kg:load,rpe:rpe as number|null,pain,skipped};}
  case 'substitute':return typeof raw.exercise==='string'&&raw.exercise?{type:'substitute',exercise:raw.exercise.slice(0,80)}:null;
  case 'regenerate':return ['variety','equipment','time','fatigue'].includes(raw.reason)?{type:'regenerate',reason:raw.reason}:null;
  case 'set_training_days':{
   if(!Array.isArray(raw.days)||!raw.days.length||raw.days.length>7||!raw.days.every((d:unknown)=>int(d)&&(d as number)>=0&&(d as number)<=6))return null;
   return {type:'set_training_days',days:[...new Set<number>(raw.days)].sort((a,b)=>a-b)};}
  default:return null;
 }
}
// Splits visible reply text from an optional action line. Invalid or repeated actions are dropped, never executed.
export function parseReply(text:string):{reply:string;action:CoachAction|null}{
 const lines=text.split('\n');const keep:string[]=[];let action:CoachAction|null=null;
 for(const line of lines){
  const at=line.indexOf(ACTION_MARK);
  if(at<0){keep.push(line);continue;}
  const before=line.slice(0,at).trim();if(before)keep.push(before);
  if(action)continue;
  const body=line.slice(at+ACTION_MARK.length).trim();
  const start=body.indexOf('{'),end=body.lastIndexOf('}');
  if(start>=0&&end>start){try{action=validateAction(JSON.parse(body.slice(start,end+1)));}catch{action=null;}}
 }
 return {reply:keep.join('\n').trim(),action};
}
export function describeAction(a:CoachAction,items:WorkoutItem[]):string{
 const ex=(n:string)=>resolveExercise(n,items)?.name??n;
 switch(a.type){
  case 'log_set':return a.skipped?`Skip set ${a.set_number} of ${ex(a.exercise)}`:`Log set ${a.set_number} of ${ex(a.exercise)}: ${a.reps} reps at ${a.load_kg} kg, RPE ${a.rpe}${a.pain?' (pain reported, this pauses the workout)':''}`;
  case 'substitute':return `Replace ${ex(a.exercise)} with the engine's top approved alternative`;
  case 'regenerate':return `Rebuild today's workout (${a.reason}) through the engine`;
  case 'set_training_days':return `Change training days to ${a.days.map(d=>['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][d]).join(', ')} (rebuilds your week)`;
 }
}

export type Route='safety'|'local'|'cloud'|'rules';
export type RouteInput={localReady:boolean;localSupported:boolean;cloudEnabled:boolean;cloudAvailable:boolean;forceCloud?:boolean;text:string;localFailed?:boolean};
const HEAVY=/\b(compare|periodi[sz]ation|design (a|me)|deload|plateau|nutrition|diet|macros?|calories?|\d+[- ]week)\b/i;
export function chooseRoute(i:RouteInput):Route{
 if(safetyCheck(i.text))return 'safety';
 const cloud=i.cloudEnabled&&i.cloudAvailable;
 if(i.forceCloud)return cloud?'cloud':(i.localReady?'local':'rules');
 const heavy=i.text.length>280||HEAVY.test(i.text);
 if(cloud&&(heavy||!i.localReady||i.localFailed||!i.localSupported))return 'cloud';
 if(i.localReady&&!i.localFailed)return 'local';
 return 'rules';
}
export function trimHistory<T extends {role:string;content:string}>(h:T[],max=6):T[]{return h.slice(-max);}
