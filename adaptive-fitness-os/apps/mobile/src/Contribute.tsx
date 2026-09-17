import React,{useEffect,useRef,useState} from 'react';
import {View,Text,TextInput,Pressable,StyleSheet,Alert,ActivityIndicator} from 'react-native';
import * as Crypto from 'expo-crypto';
import {api,load} from './api';
import * as store from './storage';
import {Choice,NumberAdjuster} from './InputControls';
import {Draft,Entry,blankSet,copySet,localDate,makePayload} from './contribution-form';
type State={account_id:string;consent:boolean;eligible_examples:number;pending_review:number};
const unknown={value:null,label:'Not sure'};
const effort=[unknown,...Array.from({length:10},(_,i)=>({value:i+1,label:String(i+1)}))];
const reasons:Record<string,string>={missing_pre_workout_context:'Some before-workout answers are missing',exercise_metadata_needs_review:'Exercise details need professional review',previous_exercise_history_unknown:'Previous exercise history is unknown',pain_reported_or_unknown:'Pain was reported or not answered',set_skipped:'Set was skipped',effort_not_recorded:'Effort was not recorded',original_prescription_unknown:'The original reps, weight or effort target is unknown',actual_differs_from_prescription:'Actual reps or weight differed from the original plan'};
function fresh():Draft{return {version:1,event_id:Crypto.randomUUID(),session_id:Crypto.randomUUID(),date:localDate(),phase:0,exercise:null,context:{experience:null,sleep_hours:'',energy:null,soreness:null,stress:null},history_mode:'unknown',sets:[blankSet()],knowPlan:false,plannedReps:'',plannedLoad:'',targetRpe:null,enjoyment:null,duration:'',pending:null,receipt:null};}
function Button({label,onPress,disabled=false}:{label:string;onPress:()=>void;disabled?:boolean}){return <Pressable disabled={disabled} accessibilityRole="button" accessibilityState={{disabled}} onPress={onPress} style={[s.button,disabled&&{opacity:.5}]}><Text style={s.buttonText}>{label}</Text></Pressable>;}
export function Contribute(){
 const [d,setD]=useState<Draft>(fresh),[state,setState]=useState<State|null>(null),[recent,setRecent]=useState<any[]>([]),[error,setError]=useState(''),[busy,setBusy]=useState(false),[hydrated,setHydrated]=useState(false),[query,setQuery]=useState(''),[results,setResults]=useState<any[]>([]),[saved,setSaved]=useState(''),[more,setMore]=useState(false);
 const alive=useRef(true),session=useRef(''),writes=useRef<Promise<void>>(Promise.resolve()),lock=useRef(false);
 const key=state?'contribution-draft:'+state.account_id:'';
 async function cacheOwner(value:State){const fingerprint=await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA256,session.current);await store.cacheForSession('contribution-owner',{fingerprint,state:value},session.current);}
 async function persist(value:Draft){
  if(!key)return;
  writes.current=writes.current.catch(()=>{}).then(async()=>{const saved=await store.cacheForSession(key,value,session.current);if(alive.current)setSaved(saved?'Draft saved on this device':'Sign in again to save this draft');});
  await writes.current;
 }
 async function refresh(){
  const current=await api<State>('/learning/status','GET',undefined,session.current);
  if(!alive.current)return;
  setState(current);await cacheOwner(current);
  const history=await api<any[]>('/contributions','GET',undefined,session.current);if(alive.current)setRecent(history);
 }
 useEffect(()=>{alive.current=true;void (async()=>{
  try{session.current=(await store.token())||'';if(!session.current)throw new Error('Sign in to contribute.');
   let current:State;
   try{current=await api<State>('/learning/status','GET',undefined,session.current);if(!alive.current)return;await cacheOwner(current);}
   catch(e){const cached=await store.cached<{fingerprint:string;state:State}>('contribution-owner');const fingerprint=await Crypto.digestStringAsync(Crypto.CryptoDigestAlgorithm.SHA256,session.current);if(!cached||cached.fingerprint!==fingerprint)throw e;current=cached.state;setError('Offline or session unavailable. You can edit a saved draft; consent is checked again when sending.');}
   if(!alive.current)return;setState(current);
   const draft=await store.cached<Draft>('contribution-draft:'+current.account_id);if(alive.current&&draft?.version===1)setD(draft);
   try{const rows=await api<any[]>('/contributions','GET',undefined,session.current);if(alive.current)setRecent(rows);}catch{}
  }catch(e){if(alive.current)setError(e instanceof Error?e.message:'Unable to open contributions');}finally{if(alive.current)setHydrated(true);}
 })();return()=>{alive.current=false;};},[]);
 useEffect(()=>{if(hydrated&&key)void persist(d).catch(()=>{if(alive.current)setSaved('Draft could not be saved. Keep this screen open.');});},[d,hydrated,key]);
 async function run(fn:()=>Promise<void>){if(lock.current)return;lock.current=true;setBusy(true);setError('');try{await fn();}catch(e){if(alive.current)setError(e instanceof Error?e.message:'Please try again.');}finally{lock.current=false;if(alive.current)setBusy(false);}}
 function edit(patch:Partial<Draft>){setD(v=>({...v,...patch}));setSaved('Saving draft…');}
 function context(name:keyof Draft['context'],value:any){edit({context:{...d.context,[name]:value}});}
 function setEntry(index:number,patch:Partial<Entry>){edit({sets:d.sets.map((set,i)=>i===index?{...set,...patch}:set)});}
 async function send(){
  const payload=d.pending||makePayload(d);
  const pending={...d,pending:payload};setD(pending);await persist(pending);
  const receipt=await api('/contributions','POST',payload,session.current);
  if(!alive.current)return;
  const done={...pending,pending:null,receipt,phase:3};setD(done);await persist(done);await refresh();
 }
 async function search(){
  const rows=(await load<any[]>('/exercises?q='+encodeURIComponent(query)+'&limit=30')).data;
  if(alive.current)setResults(rows);
 }
 if(!hydrated)return <ActivityIndicator accessibilityLabel="Opening your contribution draft" color="#d1f599"/>;
 return <View style={s.container}><Text style={s.title}>Your workout,\nyour contribution.</Text><Text style={s.text}>Log what you actually did. Unknown answers are welcome. No wearable, camera, spreadsheet or exercise ID is needed.</Text>
 {!!error&&<Text accessibilityLiveRegion="polite" style={s.error}>{error}</Text>}
 {busy&&<ActivityIndicator accessibilityLabel="Saving or loading contribution" color="#d1f599"/>}
 {!state?<Button label="Retry connection" onPress={()=>void run(refresh)} disabled={busy}/>:!state.consent?<View style={s.card}><Text style={s.heading}>Take part only if you want to</Text><Text style={s.text}>Contribute exercise logs, effort, experience and optional recovery ratings to improve the shared model. Other users cannot see your records. Names and email are excluded from model inputs. You can withdraw in Settings, which deletes contributions and retires affected models. Regular app use does not require participation.</Text><Button disabled={busy} label="I agree · contribute my workout data" onPress={()=>void run(async()=>{const next=await api<State>('/learning/consent','PUT',{enabled:true},session.current);if(alive.current)setState(next);await cacheOwner(next);})}/></View>:<>
 <Text style={s.caption}>{d.phase<3?`${d.phase+1} of 3 · ${['Before the workout','Exercise and sets','Review and send'][d.phase]}`:'Contribution saved'} · {saved}</Text>
 {d.pending?<View style={s.card}><Text style={s.heading}>Ready to send or retry</Text><Text style={s.text}>Your submission is saved on this device. If the connection dropped, retry with the same submission; it will not be counted twice.</Text><Button label="Send saved submission" disabled={busy} onPress={()=>void run(send)}/></View>:d.phase===0?<View style={s.card}>
 <Text style={s.heading}>A quick check-in</Text><Text style={s.text}>For past workouts, answer only what you remember from before that workout.</Text>
 <Text style={s.label}>Workout date · YYYY-MM-DD</Text><TextInput accessibilityLabel="Workout date in year month day format" value={d.date} onChangeText={date=>edit({date})} style={s.input}/>
 <Choice label="Your experience at that time" value={d.context.experience} onChange={v=>context('experience',v)} options={[unknown,...['First workouts','Beginner','Novice','Intermediate','Advanced','Recreational athlete','Competitive athlete'].map((label,value)=>({label,value}))]}/>
 <NumberAdjuster label="Hours slept · leave blank if unknown" value={d.context.sleep_hours} onChange={v=>context('sleep_hours',v)} step={.5} max={24}/>
 <Choice label="Energy before training" value={d.context.energy} onChange={v=>context('energy',v)} options={[unknown,...['Very low','Low','Okay','Good','Great'].map((label,i)=>({label,value:i+1}))]}/>
 <Choice label="Soreness before training" value={d.context.soreness} onChange={v=>context('soreness',v)} options={[unknown,...['None','1 · Slight','2','3 · Moderate','4','5 · High'].map((label,value)=>({label,value}))]}/>
 <Choice label="Stress before training" value={d.context.stress} onChange={v=>context('stress',v)} options={[unknown,...['None','1 · Low','2','3 · Moderate','4','5 · High'].map((label,value)=>({label,value}))]}/>
 <Button label="Next · choose an exercise" disabled={busy} onPress={()=>edit({phase:1})}/></View>:d.phase===1?<View style={s.card}>
 <Text style={s.heading}>What did you do?</Text><Text style={s.text}>This records your own workout. It does not prescribe an exercise or certify that a movement is suitable for you.</Text>
 <TextInput accessibilityLabel="Search exercise names" placeholder="Search squat, press, row…" placeholderTextColor="#b5c3b9" value={query} onChangeText={setQuery} style={s.input}/><Button label="Search exercise library" disabled={busy} onPress={()=>void run(search)}/>
 {results.map(e=><Pressable key={e.id} accessibilityRole="button" accessibilityLabel={`Select ${e.name}, ${e.equipment}`} style={s.result} onPress={()=>{edit({exercise:e,history_mode:'unknown'});setResults([]);}}><Text style={s.text}>{e.name}</Text><Text style={s.caption}>{e.equipment}</Text></Pressable>)}
 {d.exercise&&<Text style={s.heading}>{d.exercise.name}</Text>}
 {d.exercise?.equipment==='body weight'&&<Text style={s.text}>For unweighted body-weight exercise, enter 0 kg. Added external weight is logged separately.</Text>}
 <Text style={s.text}>Effort scale: 1 = very easy, 5 = moderate, 7 = hard, 9 = very hard, 10 = maximum. Choose your own rating; it is never copied from the previous set.</Text>
 {d.sets.map((set,i)=><View key={i} style={s.set}><Text style={s.heading}>Set {i+1}</Text>
 <Choice label={`Set ${i+1} status`} value={set.skipped} options={[{value:false,label:'Completed'},{value:true,label:'Skipped'}]} onChange={v=>setEntry(i,{skipped:v})}/>
 {!set.skipped&&<><NumberAdjuster label={`Set ${i+1} · completed reps`} value={set.reps} onChange={v=>setEntry(i,{reps:v})} max={200}/><NumberAdjuster label={`Set ${i+1} · weight in kg`} value={set.load} onChange={v=>setEntry(i,{load:v})} step={2.5}/><Choice label={`Set ${i+1} · how hard was it?`} value={set.rpe} options={effort} onChange={v=>setEntry(i,{rpe:v})}/></>}
 <Choice label={`Set ${i+1} · did you feel pain?`} value={set.pain} options={[unknown,{value:false,label:'No'},{value:true,label:'Yes'}]} onChange={v=>setEntry(i,{pain:v})}/>
 {set.pain===true&&<Text style={s.error}>Stop a movement that causes pain. This report is saved as feedback and will not become an RPE training example. Seek qualified assessment when appropriate.</Text>}
 {d.sets.length>1&&<Button label={`Remove set ${i+1}`} disabled={busy} onPress={()=>edit({sets:d.sets.filter((_,n)=>n!==i)})}/>}</View>)}
 {d.sets.length<20&&<Button label="Add set · copy reps and weight" disabled={busy} onPress={()=>edit({sets:[...d.sets,copySet(d.sets[d.sets.length-1]||blankSet())]})}/>}
 <Choice label="Do you know the original plan for these sets?" value={d.knowPlan} options={[{value:false,label:'No / not sure'},{value:true,label:'Yes · same target each set'}]} onChange={v=>edit({knowPlan:v})}/>
 {d.knowPlan&&<><Text style={s.text}>Enter what was planned before training, not what you completed. If targets varied, leave this unknown in this first form.</Text><NumberAdjuster label="Planned reps per set" value={d.plannedReps} onChange={v=>edit({plannedReps:v})} min={1} max={50}/><NumberAdjuster label="Planned weight in kg" value={d.plannedLoad} onChange={v=>edit({plannedLoad:v})} step={2.5}/><Choice label="Planned effort (RPE)" value={d.targetRpe} options={effort} onChange={v=>edit({targetRpe:v})}/></>}
 <Choice label="Previous experience with this exact exercise" value={d.history_mode} options={[{value:'unknown',label:'Not sure'},{value:'first_time',label:'First time ever'},{value:'recorded',label:'Use earlier reviewed contributions'}]} onChange={v=>edit({history_mode:v})}/>
 <Button label="Next · review your answers" disabled={busy} onPress={()=>void run(async()=>{makePayload(d);edit({phase:2});})}/><Button label="Back to check-in" disabled={busy} onPress={()=>edit({phase:0})}/></View>:d.phase===2?<View style={s.card}>
 <Text style={s.heading}>Check, then contribute</Text><Text style={s.text}>{d.date} · {d.exercise?.name}</Text>{d.sets.map((set,i)=><Text key={i} style={s.text}>Set {i+1}: {set.skipped?'skipped':`${set.reps} reps × ${set.load} kg · effort ${set.rpe??'unknown'}`} · pain {set.pain===null?'unknown':set.pain?'yes':'no'}</Text>)}
 <Text style={s.text}>Missing answers stay unknown. You can still submit. An operator reviews complete records before the network uses them.</Text>
 <Choice label="Did you enjoy this exercise? (optional)" value={d.enjoyment} options={[unknown,...['Not at all','A little','Okay','Yes','Very much'].map((label,i)=>({label,value:i+1}))]} onChange={v=>edit({enjoyment:v})}/>
 <NumberAdjuster label="Minutes on this exercise · optional" value={d.duration} onChange={v=>edit({duration:v})} min={1} max={300}/>
 <Button label="Submit my contribution" disabled={busy} onPress={()=>void run(send)}/><Button label="Edit my answers" disabled={busy} onPress={()=>edit({phase:1})}/></View>:<View style={s.card}>
 <Text style={s.heading}>Your contribution is saved</Text><Text style={s.text}>{d.receipt?.report.sets_recorded} sets recorded · {d.receipt?.report.potential_training_sets} complete enough for training review.</Text>
 <Text style={s.text}>You do not need to do extra workouts to contribute. Records from your usual routine are enough.</Text>
 {d.receipt?.report.sets.map((r:any)=><Text key={r.set} style={s.text}>Set {r.set}: {r.ready_for_review?'Ready for operator review':r.reasons.map((v:string)=>reasons[v]||v).join('; ')}</Text>)}
 <Button label="Add another exercise from this workout" disabled={busy} onPress={()=>setD({...fresh(),session_id:d.session_id,date:d.date,context:d.context,phase:1})}/><Button label="Start a different workout log" disabled={busy} onPress={()=>setD(fresh())}/></View>}
 <Button label={more?'Hide my recent contributions':'Show my recent contributions'} disabled={busy} onPress={()=>void run(async()=>{setMore(!more);await refresh();})}/>
 {more&&<View style={s.card}><Text style={s.heading}>Your latest 20 contributions</Text>{recent.length===0?<Text style={s.text}>Nothing submitted yet.</Text>:recent.map(r=><View key={r.id} style={s.set}><Text style={s.text}>{r.name} · {new Date(r.occurred_at*1000).toLocaleDateString()}</Text><Text style={s.caption}>{r.status==='reviewed'?'Reviewed':'Awaiting review'} · {r.report.sets_recorded} sets · {r.report.potential_training_sets} complete for training review</Text></View>)}</View>}
 </>}</View>;
}
const s=StyleSheet.create({container:{gap:16},title:{fontSize:34,lineHeight:40,color:'#f1f5ee',fontWeight:'700'},card:{backgroundColor:'#1c2a23',borderRadius:22,padding:18,gap:16,borderWidth:1,borderColor:'#35473b'},heading:{color:'#f1f5ee',fontSize:21,lineHeight:28,fontWeight:'600'},text:{color:'#b5c3b9',fontSize:16,lineHeight:24},caption:{color:'#b5c3b9',fontSize:13,lineHeight:21},label:{color:'#b5c3b9',fontSize:15},input:{minHeight:50,padding:12,borderWidth:1,borderColor:'#53695a',borderRadius:12,color:'#f1f5ee',fontSize:17},button:{minHeight:50,borderRadius:12,backgroundColor:'#d1f599',padding:12,justifyContent:'center',alignItems:'center'},buttonText:{color:'#101915',fontSize:16,fontWeight:'600',textAlign:'center'},set:{gap:14,padding:12,backgroundColor:'#101915',borderRadius:14},result:{minHeight:52,padding:12,borderBottomWidth:1,borderColor:'#53695a'},error:{color:'#ffb4a9',fontSize:15,lineHeight:23}});
