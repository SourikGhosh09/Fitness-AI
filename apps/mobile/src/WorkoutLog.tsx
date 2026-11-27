import React,{useCallback,useEffect,useRef,useState} from 'react';
import {Pressable,Share,StyleSheet,Text,TextInput,Vibration,View} from 'react-native';
import {api,load,ApiError} from './api';
import * as store from './storage';
import {ExerciseTutorial} from './ExerciseTutorial';
import {LogCheck,LogExercise,LogSession,LogSet,LogSummary,dayLabel,elapsedSeconds,emptySession,formatClock,isIsoDate,localDate,newExercise,newSet,numText,parseNum,remaining,sessionText,setDone,shiftDate,stats,toPayload,weekDates} from './workout-log';

const c={bg:'#090b0f',card:'#171b23',card2:'#202631',blue:'#4b6fff',text:'#f7f8fb',muted:'#969eae',line:'#2b3240',ok:'#6fe0a2',warn:'#fbbf24'};
type Timer={kind:'rest'|'set';endsAt:number;total:number;label:string;ei:number;si:number};
type Previous=Record<string,{date:string;sets:{kind:string;weight_kg:number|null;reps:number|null}[]}>;
type Loaded=LogSession&{previous?:Previous};
const now=()=>Date.now()/1000;

function Btn({label,onPress,kind='ghost',disabled=false}:{label:string;onPress:()=>void;kind?:'primary'|'ghost'|'danger';disabled?:boolean}){
 return <Pressable accessibilityRole="button" accessibilityLabel={label} accessibilityState={{disabled}} disabled={disabled} onPress={onPress} style={[s.btn,kind==='primary'&&s.btnPrimary,kind==='danger'&&s.btnDanger,disabled&&{opacity:.5}]}><Text style={[s.btnText,kind==='primary'&&{color:'#07120b'}]}>{label}</Text></Pressable>;
}
function Num({label,value,onChange,max=1000,width}:{label:string;value:number|null;onChange:(v:number|null)=>void;max?:number;width?:number}){
 const [text,setText]=useState(numText(value));
 useEffect(()=>{if(parseNum(text,0,max)!==value)setText(numText(value));},[value]);
 return <View style={{flex:width?undefined:1,width,minWidth:64}}><Text style={s.label}>{label}</Text><TextInput accessibilityLabel={label} keyboardType="decimal-pad" value={text} onChangeText={t=>{setText(t);onChange(parseNum(t,0,max));}} style={s.input}/></View>;
}
function Txt({label,value,onChange,multiline=false}:{label:string;value:string;onChange:(v:string)=>void;multiline?:boolean}){
 return <View><Text style={s.label}>{label}</Text><TextInput accessibilityLabel={label} value={value} onChangeText={onChange} multiline={multiline} style={[s.input,multiline&&{minHeight:80,textAlignVertical:'top'}]}/></View>;
}
function Checklist({title,items,onChange}:{title:string;items:LogCheck[];onChange:(v:LogCheck[])=>void}){
 const [text,setText]=useState('');
 return <View style={s.card}><Text style={s.heading}>{title}</Text>
  {items.map((it,i)=><Pressable key={i} accessibilityRole="checkbox" accessibilityState={{checked:it.done}} accessibilityLabel={it.text} onPress={()=>onChange(items.map((x,j)=>j===i?{...x,done:!x.done}:x))} style={s.check}><Text style={[s.checkBox,it.done&&{color:c.ok}]}>{it.done?'☑':'☐'}</Text><Text style={[s.text,{flex:1},it.done&&{color:c.muted}]}>{it.text}</Text><Pressable accessibilityRole="button" accessibilityLabel={`Remove ${it.text}`} onPress={()=>onChange(items.filter((_,j)=>j!==i))} hitSlop={10}><Text style={s.muted}>✕</Text></Pressable></Pressable>)}
  <View style={{flexDirection:'row',gap:8}}><TextInput accessibilityLabel={`Add to ${title}`} placeholder="Add item" placeholderTextColor={c.muted} value={text} onChangeText={setText} style={[s.input,{flex:1}]}/><Btn label="Add" onPress={()=>{const t=text.trim();if(t&&items.length<30){onChange([...items,{text:t.slice(0,200),done:false}]);setText('');}}}/></View></View>;
}

export function WorkoutLog({setStatus}:{setStatus:(m:string)=>void}){
 const [date,setDate]=useState(localDate());
 const [jump,setJump]=useState('');
 const [week,setWeek]=useState<Record<string,LogSummary>>({});
 const [log,setLog]=useState<Loaded|null>(null);
 const [loading,setLoading]=useState(true);
 const [sync,setSync]=useState<'saved'|'saving'|'offline'|'idle'>('idle');
 const [tick,setTick]=useState(0);
 const [timer,setTimer]=useState<Timer|null>(null);
 const [pausedSince,setPausedSince]=useState<number|null>(null);
 const [openTut,setOpenTut]=useState<Record<number,boolean>>({});
 const [query,setQuery]=useState('');
 const [results,setResults]=useState<{id:string;name:string}[]>([]);
 const [customName,setCustomName]=useState('');
 const rev=useRef(0),saving=useRef(false),latest=useRef<{date:string;log:Loaded|null}>({date,log:null}),dirty=useRef(false);
 latest.current={date,log};

 const refreshWeek=useCallback(async(d:string)=>{
  const days=weekDates(d);
  try{const r=await api<{logs:LogSummary[]}>(`/logs?start=${days[0]}&end=${days[6]}`);setWeek(Object.fromEntries(r.logs.map(x=>[x.date,x])));}catch{/* offline: keep last week view */}
 },[]);
 const open=useCallback(async(d:string)=>{
  setLoading(true);setTimer(null);setPausedSince(null);setOpenTut({});
  try{
   const draft=await store.cached<{log:Loaded;dirty:boolean}>('/logs-draft/'+d);
   if(draft?.dirty){setLog(draft.log);dirty.current=true;setSync('offline');return;}
   try{const r=await load<Loaded>('/logs/'+d);setLog(r.data);setSync(r.offline?'offline':'saved');}
   catch(e){if(e instanceof ApiError&&e.status===404)setLog(null);else throw e;}
  }catch(e){setLog(null);setStatus(e instanceof Error?e.message:'Could not load this day.');}
  finally{setLoading(false);}
 },[setStatus]);
 useEffect(()=>{dirty.current=false;void open(date);void refreshWeek(date);},[date]);
 useEffect(()=>{const id=setInterval(()=>setTick(t=>t+1),500);return ()=>clearInterval(id);},[]);

 const save=useCallback(async()=>{
  if(saving.current)return;const {date:d,log:l}=latest.current;if(!l||!dirty.current)return;
  saving.current=true;setSync('saving');const sent=rev.current;
  try{
   const r=await api<Loaded>('/logs/'+d,'PUT',toPayload(l as any));
   if(latest.current.date===d){setLog(cur=>cur?{...cur,version:r.version}:cur);}
   if(rev.current===sent){dirty.current=false;await store.cache('/logs-draft/'+d,{log:{...l,version:r.version},dirty:false});setSync('saved');void refreshWeek(d);}
  }catch(e){
   if(e instanceof ApiError){setSync('offline');setStatus(e.status===409?e.message+' Pull down to reopen the day.':e.message);dirty.current=e.status!==409&&dirty.current;}
   else setSync('offline');
  }finally{saving.current=false;if(dirty.current&&rev.current!==sent)setTimeout(()=>void save(),300);}
 },[refreshWeek,setStatus]);
 useEffect(()=>{if(!log||!dirty.current)return;const t=setTimeout(()=>void save(),800);return ()=>clearTimeout(t);},[log]);

 function edit(fn:(l:Loaded)=>Loaded){
  setLog(cur=>{if(!cur)return cur;const next=fn(cur);rev.current++;dirty.current=true;void store.cache('/logs-draft/'+date,{log:next,dirty:true});return next;});
 }
 const patchEx=(ei:number,p:Partial<LogExercise>)=>edit(l=>({...l,exercises:l.exercises.map((e,i)=>i===ei?{...e,...p}:e)}));
 const patchSet=(ei:number,si:number,p:Partial<LogSet>)=>edit(l=>({...l,exercises:l.exercises.map((e,i)=>i!==ei?e:{...e,sets:e.sets.map((x,j)=>j===si?{...x,...p}:x)})}));

 async function create(fromPlan:boolean){
  try{
   if(fromPlan){const r=await api<Loaded>(`/logs/${date}/from-plan`,'POST');setLog(r);setSync('saved');void refreshWeek(date);return;}
   const l=emptySession(dayLabel(date).split(' ')[0]+' workout');rev.current++;dirty.current=true;setLog(l);
  }catch(e){setStatus(e instanceof Error?e.message:'Could not start a log.');}
 }
 function startSession(){edit(l=>({...l,status:'in_progress',started_at:l.started_at??now(),ended_at:null}));}
 function togglePause(){
  if(pausedSince!==null){const gap=Math.floor(now()-pausedSince);setPausedSince(null);edit(l=>({...l,paused_seconds:l.paused_seconds+gap}));}
  else setPausedSince(now());
 }
 function finish(){
  if(pausedSince!==null){const gap=Math.floor(now()-pausedSince);setPausedSince(null);edit(l=>({...l,paused_seconds:l.paused_seconds+gap,status:'completed',started_at:l.started_at??now(),ended_at:now()}));}
  else edit(l=>({...l,status:'completed',started_at:l.started_at??now(),ended_at:now()}));
  setTimer(null);
 }
 function tickSet(ei:number,si:number,done:boolean){
  if(!log)return;const r=setDone(log,ei,si,done,now());edit(()=>({...r.session,previous:log.previous}));
  if(done&&r.rest>0)setTimer({kind:'rest',endsAt:now()+r.rest,total:r.rest,label:`Rest after ${log.exercises[ei]?.name??'set'}`,ei,si});
  else if(!done&&timer?.ei===ei&&timer.si===si)setTimer(null);
 }
 function startSetTimer(ei:number,si:number){
  const set=log?.exercises[ei]?.sets[si];const secs=set?.reps??0;
  if(!set||secs<=0){setStatus('Enter the target seconds first, then start the timer.');return;}
  setTimer({kind:'set',endsAt:now()+secs,total:secs,label:`${log?.exercises[ei]?.name} · set ${si+1}`,ei,si});
 }
 function adjustTimer(delta:number){setTimer(t=>t?{...t,endsAt:Math.max(now(),t.endsAt+delta),total:Math.max(1,t.total+delta)}:t);}
 // Timer expiry (clock-based, so it is correct after backgrounding).
 useEffect(()=>{
  if(!timer||remaining(timer.endsAt,now())>0)return;
  Vibration.vibrate(timer.kind==='set'?[0,300,150,300]:[0,400]);
  const t=timer;setTimer(null);
  if(t.kind==='set'&&latest.current.log&&!latest.current.log.exercises[t.ei]?.sets[t.si]?.done)tickSet(t.ei,t.si,true);
 },[tick]);

 useEffect(()=>{
  if(!query.trim()){setResults([]);return;}
  const id=setTimeout(async()=>{try{setResults((await api<any[]>('/exercises?limit=8&q='+encodeURIComponent(query.trim()))).map(x=>({id:x.id,name:x.name})));}catch{setResults([]);}},350);
  return ()=>clearTimeout(id);
 },[query]);

 const days=weekDates(date);const today=localDate();
 const elapsed=log?elapsedSeconds(log,now(),pausedSince):0;const st=log?stats(log):null;
 const live=timer?remaining(timer.endsAt,now()):0;
 const syncText=sync==='saving'?'Saving…':sync==='saved'?'Saved':sync==='offline'?'Saved on this device · will sync when online':'';
 return <View style={{gap:14}}>
  <View style={s.weekHead}>
   <Btn label="‹ Week" onPress={()=>setDate(shiftDate(date,-7))}/><Text style={s.heading}>{days[0]} → {days[6]}</Text><Btn label="Week ›" onPress={()=>setDate(shiftDate(date,7))}/>
  </View>
  <View style={s.dayRow}>{days.map(d=>{const w=week[d];return <Pressable key={d} accessibilityRole="button" accessibilityLabel={`${dayLabel(d)}${w?`, ${w.status}`:', no log'}`} accessibilityState={{selected:d===date}} onPress={()=>setDate(d)} style={[s.day,d===date&&s.daySel,d===today&&{borderColor:c.blue}]}>
   <Text style={[s.dayText,d===date&&{color:'#07120b'}]}>{dayLabel(d)}</Text><Text style={[s.dayDot,{color:w?.status==='completed'?c.ok:w?c.warn:c.muted},d===date&&{color:'#07120b'}]}>{w?(w.status==='completed'?'●':'◐'):'○'}</Text></Pressable>;})}</View>
  <View style={{flexDirection:'row',gap:8,alignItems:'flex-end'}}><View style={{flex:1}}><Txt label="Jump to date (YYYY-MM-DD)" value={jump} onChange={setJump}/></View><Btn label="Go" onPress={()=>{if(isIsoDate(jump)){setDate(jump);setJump('');}else setStatus('Enter a real date like 2026-10-26.');}}/><Btn label="Today" onPress={()=>setDate(today)}/></View>
  {loading&&<Text style={s.muted}>Loading {date}…</Text>}
  {!loading&&!log&&<View style={s.card}><Text style={s.heading}>{dayLabel(date)} · no log yet</Text><Text style={s.muted}>Start from today's generated plan or build a session yourself.</Text><Btn kind="primary" label="Start from planned session" onPress={()=>void create(true)}/><Btn label="Start a blank log" onPress={()=>void create(false)}/></View>}
  {log&&<>
   {timer&&<View accessibilityLiveRegion="polite" style={[s.timer,{borderColor:timer.kind==='rest'?c.blue:c.ok}]}><Text style={s.label}>{timer.kind==='rest'?'REST TIMER':'SET TIMER'} · {timer.label}</Text><Text style={s.big}>{formatClock(live)}</Text>
    <View style={{flexDirection:'row',gap:8,flexWrap:'wrap'}}><Btn label="−15s" onPress={()=>adjustTimer(-15)}/><Btn label="+15s" onPress={()=>adjustTimer(15)}/><Btn label={timer.kind==='rest'?'Skip rest':'Cancel timer'} onPress={()=>setTimer(null)}/></View></View>}
   <View style={s.card}>
    <Txt label="Session title" value={log.title} onChange={v=>edit(l=>({...l,title:v.slice(0,120)||'Workout'}))}/>
    <View style={{flexDirection:'row',justifyContent:'space-between',alignItems:'center'}}><View><Text style={s.label}>SESSION TIME</Text><Text style={s.big}>{formatClock(elapsed)}</Text></View><View style={{alignItems:'flex-end'}}><Text style={[s.pill,log.status==='completed'&&{color:c.ok}]}>{log.status.replace('_',' ').toUpperCase()}</Text>{st&&<Text style={s.muted}>{st.done}/{st.total} sets · {st.volume} kg volume</Text>}</View></View>
    <View style={{flexDirection:'row',gap:8,flexWrap:'wrap'}}>
     {log.status==='planned'&&<Btn kind="primary" label="Start session" onPress={startSession}/>}
     {log.status==='in_progress'&&<><Btn label={pausedSince!==null?'Resume':'Pause'} onPress={togglePause}/><Btn kind="primary" label="Finish session" onPress={finish}/></>}
     {log.status==='completed'&&<Btn label="Reopen" onPress={()=>edit(l=>({...l,status:'in_progress',ended_at:null}))}/>}
    </View>
    <Text accessibilityLiveRegion="polite" style={s.muted}>{syncText}</Text>
   </View>
   <View style={s.card}><Text style={s.heading}>Before you start</Text>
    <View style={s.row}><Num label="Body weight kg" value={log.body_weight_kg} max={500} onChange={v=>edit(l=>({...l,body_weight_kg:v}))}/><Num label="Sleep h" value={log.sleep_hours} max={24} onChange={v=>edit(l=>({...l,sleep_hours:v}))}/><Num label="Energy /10" value={log.energy} max={10} onChange={v=>edit(l=>({...l,energy:v===null?null:Math.round(v)}))}/></View>
    <View style={s.row}><Num label="Soreness /10" value={log.soreness_pre} max={10} onChange={v=>edit(l=>({...l,soreness_pre:v===null?null:Math.round(v)}))}/><Num label="Pain /10" value={log.pain_pre} max={10} onChange={v=>edit(l=>({...l,pain_pre:v===null?null:Math.round(v)}))}/></View>
    <Text style={s.muted}>Stop if you feel sharp or worsening pain. Logged values are your own record and do not change your adaptive plan.</Text></View>
   <Checklist title="Warm-up" items={log.warmup} onChange={v=>edit(l=>({...l,warmup:v}))}/>
   {log.exercises.map((ex,ei)=>{const prev=ex.exercise_id?log.previous?.[ex.exercise_id]:undefined;return <View key={ei} style={s.card}>
    <View style={{flexDirection:'row',justifyContent:'space-between',gap:8}}><View style={{flex:1}}><Text style={s.heading}>{ei+1}. {ex.name}</Text>{!!ex.target&&<Text style={{color:'#93c5fd',fontSize:13}}>Target: {ex.target}</Text>}{!!prev&&<Text style={s.muted}>Last ({prev.date}): {prev.sets.map(x=>x.kind==='seconds'?`${x.reps??'-'}s`:`${x.weight_kg??'-'}×${x.reps??'-'}`).join(' · ')}</Text>}</View>
     <Btn label="Remove" kind="danger" onPress={()=>edit(l=>({...l,exercises:l.exercises.filter((_,i)=>i!==ei)}))}/></View>
    {ex.exercise_id?<><Btn label={openTut[ei]?`Hide tutorial for ${ex.name}`:`Show tutorial for ${ex.name}`} onPress={()=>setOpenTut(o=>({...o,[ei]:!o[ei]}))}/>{openTut[ei]&&<ExerciseTutorial exerciseId={ex.exercise_id} name={ex.name} autoStart/>}</>:<Text style={s.muted}>Custom exercise · no tutorial. Add it from the catalog to see its animation.</Text>}
    <View style={s.row}><Num label="Rest between sets (s)" value={ex.rest_seconds} max={900} onChange={v=>patchEx(ei,{rest_seconds:Math.round(v??0)})}/><View style={{flex:1}}><Text style={s.label}>Set type</Text><Btn label={ex.sets[0]?.kind==='seconds'?'Timed (sec)':'Reps'} onPress={()=>edit(l=>({...l,exercises:l.exercises.map((e,i)=>i!==ei?e:{...e,sets:e.sets.map(x=>({...x,kind:x.kind==='seconds'?'reps':'seconds'}))})}))}/></View></View>
    <View style={s.setHead}><Text style={[s.label,{width:28}]}>SET</Text><Text style={[s.label,{flex:1}]}>KG</Text><Text style={[s.label,{flex:1}]}>{ex.sets[0]?.kind==='seconds'?'SEC':'REPS'}</Text><Text style={[s.label,{width:48}]}>RIR</Text><Text style={[s.label,{width:84}]}>DONE</Text></View>
    {ex.sets.map((x,si)=><View key={si} style={s.setRow}>
     <Text style={[s.text,{width:28}]}>{si+1}</Text>
     <View style={{flex:1}}><SetNum label={`Set ${si+1} weight`} value={x.weight_kg} max={1000} onChange={v=>patchSet(ei,si,{weight_kg:v})}/></View>
     <View style={{flex:1}}><SetNum label={`Set ${si+1} ${x.kind==='seconds'?'seconds':'reps'}`} value={x.reps} max={3600} onChange={v=>patchSet(ei,si,{reps:v===null?null:Math.round(v)})}/></View>
     <View style={{width:48}}><SetNum label={`Set ${si+1} reps in reserve`} value={x.rir} max={10} onChange={v=>patchSet(ei,si,{rir:v===null?null:Math.round(v)})}/></View>
     <View style={{width:84,flexDirection:'row',gap:4}}>{x.kind==='seconds'&&!x.done&&<Pressable accessibilityRole="button" accessibilityLabel={`Start timer for set ${si+1}`} onPress={()=>startSetTimer(ei,si)} style={s.mini}><Text style={s.text}>⏱</Text></Pressable>}<Pressable accessibilityRole="checkbox" accessibilityState={{checked:x.done}} accessibilityLabel={`Set ${si+1} done`} onPress={()=>tickSet(ei,si,!x.done)} style={[s.mini,x.done&&{backgroundColor:c.ok}]}><Text style={[s.text,x.done&&{color:'#07120b'}]}>{x.done?'✓':'○'}</Text></Pressable></View>
    </View>)}
    <View style={{flexDirection:'row',gap:8}}><Btn label="+ Set" onPress={()=>{if(ex.sets.length<30)patchEx(ei,{sets:[...ex.sets,newSet(ex.sets[ex.sets.length-1])]});}}/><Btn label="− Set" disabled={ex.sets.length<=1||!!ex.sets[ex.sets.length-1]?.done} onPress={()=>patchEx(ei,{sets:ex.sets.slice(0,-1)})}/></View>
    <Txt label="Exercise notes" value={ex.notes} onChange={v=>patchEx(ei,{notes:v.slice(0,500)})}/>
   </View>;})}
   <View style={s.card}><Text style={s.heading}>Add exercise</Text>
    <Txt label="Search the exercise library" value={query} onChange={setQuery}/>
    {results.map(r=><Pressable key={r.id} accessibilityRole="button" accessibilityLabel={`Add ${r.name}`} onPress={()=>{if(log.exercises.length<40){edit(l=>({...l,exercises:[...l.exercises,newExercise(r.name,r.id)]}));setQuery('');setResults([]);}}} style={s.result}><Text style={s.text}>＋ {r.name}</Text></Pressable>)}
    <View style={{flexDirection:'row',gap:8,alignItems:'flex-end'}}><View style={{flex:1}}><Txt label="Or add a custom exercise" value={customName} onChange={setCustomName}/></View><Btn label="Add" onPress={()=>{const n=customName.trim();if(n&&log.exercises.length<40){edit(l=>({...l,exercises:[...l.exercises,newExercise(n)]}));setCustomName('');}}}/></View></View>
   <View style={s.card}><Text style={s.heading}>Conditioning</Text>{!!log.cardio.target&&<Text style={s.muted}>Target: {log.cardio.target}</Text>}
    <View style={s.row}><View style={{flex:2}}><Txt label="Activity / machine" value={log.cardio.activity} onChange={v=>edit(l=>({...l,cardio:{...l.cardio,activity:v.slice(0,120)}}))}/></View><Num label="Minutes" value={log.cardio.minutes} max={1440} onChange={v=>edit(l=>({...l,cardio:{...l.cardio,minutes:v}}))}/></View></View>
   <Checklist title="Stretching" items={log.stretch} onChange={v=>edit(l=>({...l,stretch:v}))}/>
   <Checklist title="Cooldown & relaxation" items={log.cooldown} onChange={v=>edit(l=>({...l,cooldown:v}))}/>
   <View style={s.card}><Text style={s.heading}>Session review</Text>
    <Txt label="Overall set difficulty" value={log.difficulty} onChange={v=>edit(l=>({...l,difficulty:v.slice(0,200)}))}/><Txt label="Technique" value={log.technique} onChange={v=>edit(l=>({...l,technique:v.slice(0,200)}))}/>
    <View style={s.row}><Num label="Soreness after /10" value={log.soreness_post} max={10} onChange={v=>edit(l=>({...l,soreness_post:v===null?null:Math.round(v)}))}/><Num label="Pain after /10" value={log.pain_post} max={10} onChange={v=>edit(l=>({...l,pain_post:v===null?null:Math.round(v)}))}/></View>
    <Txt label="Notes / what to change next time" multiline value={log.notes} onChange={v=>edit(l=>({...l,notes:v.slice(0,4000)}))}/></View>
   <View style={{gap:8}}><Btn kind="primary" label="Share this day's log" onPress={()=>void Share.share({message:sessionText(date,log)}).catch(()=>setStatus('Could not open the share sheet.'))}/>
    {sync==='offline'&&<Btn label="Retry sync now" onPress={()=>void save()}/>}
    <Btn kind="danger" label="Delete this day's log" onPress={()=>void (async()=>{try{if(log.version>0)await api('/logs/'+date,'DELETE');dirty.current=false;await store.cache('/logs-draft/'+date,{log:null,dirty:false});setLog(null);setTimer(null);void refreshWeek(date);}catch(e){setStatus(e instanceof Error?e.message:'Could not delete.');}})()}/></View>
  </>}
 </View>;
}
function SetNum({label,value,onChange,max}:{label:string;value:number|null;onChange:(v:number|null)=>void;max:number}){
 const [text,setText]=useState(numText(value));
 useEffect(()=>{if(parseNum(text,0,max)!==value)setText(numText(value));},[value]);
 return <TextInput accessibilityLabel={label} keyboardType="decimal-pad" value={text} onChangeText={t=>{setText(t);onChange(parseNum(t,0,max));}} style={[s.input,{textAlign:'center',paddingHorizontal:4,minHeight:46}]}/>;
}
const s=StyleSheet.create({
 card:{backgroundColor:c.card,borderRadius:20,padding:16,gap:12,borderWidth:1,borderColor:c.line},heading:{color:c.text,fontSize:17,fontWeight:'800'},text:{color:c.text,fontSize:15},muted:{color:c.muted,fontSize:13,lineHeight:19},label:{color:c.muted,fontSize:11,fontWeight:'700',letterSpacing:.4,marginBottom:4},
 input:{minHeight:48,borderWidth:1,borderColor:c.line,borderRadius:12,padding:10,color:c.text,fontSize:16,backgroundColor:'#0c1426'},row:{flexDirection:'row',gap:8},
 btn:{minHeight:44,paddingHorizontal:14,borderRadius:12,borderWidth:1,borderColor:c.line,backgroundColor:c.card2,justifyContent:'center',alignItems:'center'},btnPrimary:{backgroundColor:c.ok,borderColor:c.ok},btnDanger:{borderColor:'#7f1d1d'},btnText:{color:c.text,fontWeight:'700',fontSize:14},
 weekHead:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',gap:8},dayRow:{flexDirection:'row',gap:6},day:{flex:1,minHeight:56,borderRadius:12,borderWidth:1,borderColor:c.line,backgroundColor:c.card,alignItems:'center',justifyContent:'center'},daySel:{backgroundColor:c.ok,borderColor:c.ok},dayText:{color:c.text,fontSize:11,fontWeight:'700'},dayDot:{fontSize:14},
 timer:{backgroundColor:c.card2,borderRadius:20,padding:16,gap:8,borderWidth:2},big:{color:c.text,fontSize:40,fontWeight:'900',fontVariant:['tabular-nums']},pill:{color:c.warn,fontSize:12,fontWeight:'800',letterSpacing:1},
 check:{flexDirection:'row',alignItems:'center',gap:10,minHeight:44,backgroundColor:'#10192b',borderRadius:10,paddingHorizontal:10},checkBox:{color:c.muted,fontSize:20},
 setHead:{flexDirection:'row',gap:6,alignItems:'center'},setRow:{flexDirection:'row',gap:6,alignItems:'center'},mini:{width:38,height:46,borderRadius:10,borderWidth:1,borderColor:c.line,alignItems:'center',justifyContent:'center',backgroundColor:c.card2},result:{minHeight:44,justifyContent:'center',paddingHorizontal:10,backgroundColor:'#10192b',borderRadius:10}
});
