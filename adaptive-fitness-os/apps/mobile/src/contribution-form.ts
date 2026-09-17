// Pure form conversion: unknown stays null; planned values never inferred from outcomes.
export type Entry={reps:string;load:string;rpe:number|null;pain:boolean|null;skipped:boolean};
export type Draft={version:1;event_id:string;session_id:string;date:string;phase:number;exercise:{id:string;name:string;equipment:string}|null;
 context:{experience:number|null;sleep_hours:string;energy:number|null;soreness:number|null;stress:number|null};
 history_mode:'unknown'|'first_time'|'recorded';sets:Entry[];knowPlan:boolean;plannedReps:string;plannedLoad:string;targetRpe:number|null;enjoyment:number|null;duration:string;pending:any|null;receipt:any|null};
export function localDate(date=new Date()){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;}
export function blankSet():Entry{return {reps:'',load:'',rpe:null,pain:null,skipped:false};}
export function copySet(set:Entry):Entry{return {...set,rpe:null,pain:null,skipped:false};}
function number(value:string,label:string,min:number,max:number,integer=false,optional=false){
 if(!value.trim()){if(optional)return null;throw new Error(`Enter ${label}.`);}
 const n=Number(value);if(!Number.isFinite(n)||n<min||n>max||(integer&&!Number.isInteger(n)))throw new Error(`${label} must be ${integer?'a whole number ':''}between ${min} and ${max}.`);return n;
}
export function makePayload(d:Draft,now=new Date()){
 if(!d.exercise)throw new Error('Choose an exercise from the library.');
 if(!/^\d{4}-\d{2}-\d{2}$/.test(d.date))throw new Error('Enter a date as YYYY-MM-DD.');
 const y=Number(d.date.slice(0,4)),m=Number(d.date.slice(5,7)),day=Number(d.date.slice(8,10));const date=new Date(y,m-1,day,12);
 if(localDate(date)!==d.date||d.date>localDate(now)||date.getTime()<=0)throw new Error('Choose a valid date today or earlier.');
 if(d.sets.length<1||d.sets.length>20)throw new Error('Record between 1 and 20 sets.');
 return {event_id:d.event_id,session_id:d.session_id,exercise_id:d.exercise.id,occurred_at:d.date===localDate(now)?now.getTime()/1000:date.getTime()/1000,
  context:{...d.context,sleep_hours:number(d.context.sleep_hours,'sleep hours',0,24,false,true)},history_mode:d.history_mode,
  sets:d.sets.map((s,i)=>({reps:s.skipped?0:number(s.reps,`reps for set ${i+1}`,0,200,true),load_kg:s.skipped?0:number(s.load,`weight for set ${i+1}`,0,600),rpe:s.rpe,pain:s.pain,skipped:s.skipped,
   planned_reps:d.knowPlan?number(d.plannedReps,'planned reps',1,50,true,true):null,planned_load_kg:d.knowPlan?number(d.plannedLoad,'planned weight',0,600,false,true):null,target_rpe:d.knowPlan?d.targetRpe:null})),
  enjoyment:d.enjoyment,duration_minutes:number(d.duration,'minutes',1,300,true,true)};
}
