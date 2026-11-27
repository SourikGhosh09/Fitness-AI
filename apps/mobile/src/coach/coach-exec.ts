// Runs a confirmed coach action through the app's existing validated paths (same endpoints and offline queue as the buttons).
import {api,sync} from '../api';
import * as store from '../storage';
import {CoachAction,resolveExercise} from './coach-core';

export type ExecContext={workout:any;profile:any;logged:Record<string,boolean>};
export type ExecResult={message:string;workout?:any;profile?:any;logged?:Record<string,boolean>;week?:any};

export async function executeAction(a:CoachAction,ctx:ExecContext):Promise<ExecResult>{
 if(a.type==='set_training_days'){
  if(!ctx.profile)throw new Error('Your profile is not loaded yet.');
  const p={...ctx.profile,days:a.days};
  await api('/profile','PUT',p);await store.cache('/profile',p);await store.cache('today',null);
  let week;try{week=await api('/workouts/week');}catch{}
  return {message:'Training days updated. Your week was rebuilt.',profile:p,workout:null,week};
 }
 const w=ctx.workout;
 if(!w||!Array.isArray(w.items))throw new Error('No workout yet. Do the readiness check on the Today tab first.');
 if(w.status!=='planned')throw new Error('Today\'s workout is '+w.status+', so it cannot be changed.');
 if(a.type==='regenerate'){
  const r=await api<any>(`/workouts/${w.id}/regenerate`,'POST',{reason:a.reason});
  const next={...w,...r};await store.cache('today',next);return {message:'Workout rebuilt by the engine.',workout:next};
 }
 const item=resolveExercise(a.exercise,w.items);
 if(!item)throw new Error(`I could not match "${a.exercise}" to an exercise in today's workout.`);
 if(a.type==='substitute'){
  const r=await api<any>(`/workouts/${w.id}/substitute`,'POST',{exercise_id:item.exercise_id,reason:'dislike'});
  const next={...w,...r,status:'planned'};await store.cache('today',next);return {message:`Replaced ${item.name}.`,workout:next};
 }
 // log_set
 if(a.set_number>item.sets)throw new Error(`${item.name} has only ${item.sets} sets today.`);
 const key=`${w.id}:${item.exercise_id}:${a.set_number}`;
 if(ctx.logged[key])throw new Error(`Set ${a.set_number} of ${item.name} is already logged.`);
 await store.queue({workout_id:w.id,exercise_id:item.exercise_id,set_number:a.set_number,reps:a.reps,load_kg:a.load_kg,rpe:a.rpe,pain:a.pain,skipped:a.skipped});
 const logged={...ctx.logged,[key]:true};await store.cache('logged',logged);
 const next=a.pain?{...w,status:'paused'}:w;if(a.pain)await store.cache('today',next);
 let msg=a.pain?'Pain recorded. Stop this workout.':'Set saved on this device.';
 try{await sync();}catch{msg='Saved offline. It will sync when connected.';}
 return {message:msg,logged,workout:next};
}
