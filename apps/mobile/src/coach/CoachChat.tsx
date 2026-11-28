import React,{useCallback,useEffect,useRef,useState} from 'react';
import {Alert,Platform,Pressable,StyleSheet,Switch,Text,TextInput,View} from 'react-native';
import * as Network from 'expo-network';
import DeviceInfo from 'react-native-device-info';
import * as store from '../storage';
import {api} from '../api';
import {CoachAction,SYSTEM_PROMPT,buildState,chooseRoute,describeAction,parseReply,safetyCheck,userTurn,trimHistory,Route} from './coach-core';
import {executeAction,ExecResult} from './coach-exec';
import {askCloud,cloudAvailable} from './cloud';
import {LocalEngine,LocalHandle,LOCAL_MODEL_LABEL} from './LocalEngine';

import {colors as t} from '../theme';
const c={bg:t.bg,card:t.surface,card2:t.surface2,blue:t.volt,text:t.text,muted:t.muted,line:t.line,success:t.ready,warn:t.moderate};
type Msg={id:number;role:'user'|'assistant';content:string;source?:Route|'error';action?:CoachAction|null;actionState?:'pending'|'done'|'dismissed'};
type Prefs={local:boolean;cloud:boolean};
const MODEL_MB=1200;
const SOURCE_LABEL:Record<string,string>={local:'ON-DEVICE',cloud:'CLOUD',rules:'ENGINE',safety:'SAFETY',error:'ERROR'};

export function CoachChat({profile,workout,week,logged,onResult,setStatus}:{profile:any;workout:any;week:any;logged:Record<string,boolean>;onResult:(r:ExecResult)=>void;setStatus:(s:string)=>void}){
 const [prefs,setPrefs]=useState<Prefs>({local:false,cloud:false});
 const [prefsLoaded,setPrefsLoaded]=useState(false);
 const [supported,setSupported]=useState<{ok:boolean;why:string}>({ok:true,why:''});
 const [cloudOk,setCloudOk]=useState(false);
 const [engine,setEngine]=useState<{ready:boolean;progress:number;error:string|null;handle:LocalHandle|null}>({ready:false,progress:0,error:null,handle:null});
 const [epoch,setEpoch]=useState(0);
 const [seed,setSeed]=useState<{role:'user'|'assistant';content:string}[]>([]);
 const [msgs,setMsgs]=useState<Msg[]>([]);
 const [input,setInput]=useState('');
 const [busy,setBusy]=useState(false);
 const [localFailed,setLocalFailed]=useState(false);
 const nextId=useRef(1);const handleRef=useRef<LocalHandle|null>(null);
 handleRef.current=engine.handle;

 useEffect(()=>{void (async()=>{
  const saved=await store.cached<Prefs>('coach:prefs');if(saved)setPrefs(saved);setPrefsLoaded(true);
  let ok=Platform.OS==='android'&&Number(Platform.Version)>=33,why=ok?'':'The on-device model needs Android 13 or newer.';
  if(ok){try{const mem=await DeviceInfo.getTotalMemory();if(mem<4.5*1024**3){ok=false;why='This phone has too little RAM for the on-device model.';}}catch{}}
  setSupported({ok,why});setCloudOk(await cloudAvailable());
 })();},[]);
 const savePrefs=useCallback(async(p:Prefs)=>{setPrefs(p);await store.cache('coach:prefs',p);},[]);

 async function enableLocal(){
  if(!supported.ok){Alert.alert('Not available',supported.why);return;}
  let wifi=false;try{wifi=(await Network.getNetworkStateAsync()).type===Network.NetworkStateType.WIFI;}catch{}
  const go=()=>void savePrefs({...prefs,local:true});
  if(wifi)Alert.alert('Download the on-device coach?',`About ${MODEL_MB/1000} GB, one time. It runs offline and free after that.`,[{text:'Cancel',style:'cancel'},{text:'Download',onPress:go}]);
  else Alert.alert('You are not on Wi-Fi',`The download is about ${MODEL_MB/1000} GB and may use mobile data. Wait for Wi-Fi?`,[{text:'Wait for Wi-Fi',style:'cancel'},{text:'Download anyway',onPress:go}]);
 }
 function disableLocal(){engine.handle?.stop();setEngine({ready:false,progress:0,error:null,handle:null});void savePrefs({...prefs,local:false});}

 const push=(m:Omit<Msg,'id'>)=>{const id=nextId.current++;setMsgs(x=>[...x,{...m,id}]);return id;};
 const patch=(id:number,f:(m:Msg)=>Msg)=>setMsgs(x=>x.map(m=>m.id===id?f(m):m));

 async function send(text:string,forceCloud=false){
  const t=text.trim();if(!t||busy)return;
  setBusy(true);setInput('');
  const history=msgs.filter(m=>m.source!=='error').map(m=>({role:m.role,content:m.content}));
  if(!forceCloud)push({role:'user',content:t});
  const route=chooseRoute({localReady:engine.ready&&!!engine.handle,localSupported:supported.ok&&prefs.local,cloudEnabled:prefs.cloud,cloudAvailable:cloudOk,forceCloud,text:t,localFailed});
  const state=buildState({profile,week,workout,logged});
  try{
   if(route==='safety'){push({role:'assistant',content:safetyCheck(t)!,source:'safety'});return;}
   if(route==='rules'){
    const r=await api<any>('/coach','POST',{message:t});
    push({role:'assistant',content:String(r.reply)+(prefs.local?'':'\n\nTip: turn on the on-device coach below for open conversation.'),source:'rules'});return;
   }
   const id=push({role:'assistant',content:'',source:route});
   let raw='';
   if(route==='local'){
    const h=handleRef.current!;
    raw=await h.send(userTurn(state,t),tok=>patch(id,m=>({...m,content:m.content+tok})));
    if(h.usage()>0.7){setSeed(trimHistory([...history,{role:'user' as const,content:t},{role:'assistant' as const,content:raw}],4));setEpoch(e=>e+1);}
   }else{
    raw=await askCloud(SYSTEM_PROMPT+'\n\n'+state,trimHistory(history,8),t);
   }
   const {reply,action}=parseReply(raw);
   patch(id,m=>({...m,content:reply||(action?'Here is what I suggest.':'(no answer)'),action,actionState:action?'pending':undefined}));
  }catch(e){
   const msg=e instanceof Error?e.message:'Something went wrong.';
   if(route==='local')setLocalFailed(true);
   push({role:'assistant',source:'error',content:route==='local'?`The on-device coach hit a problem (${msg}).${prefs.cloud&&cloudOk?' Tap "Ask cloud instead" to retry in the cloud.':''}`:msg});
  }finally{setBusy(false);}
 }
 async function apply(m:Msg){
  if(!m.action)return;
  try{const r=await executeAction(m.action,{workout,profile,logged});onResult(r);setStatus(r.message);patch(m.id,x=>({...x,actionState:'done'}));push({role:'assistant',content:r.message,source:'rules'});}
  catch(e){push({role:'assistant',source:'error',content:e instanceof Error?e.message:'Could not apply that.'});}
 }
 const lastUser=[...msgs].reverse().find(m=>m.role==='user')?.content;
 const items=workout?.items??[];
 if(!prefsLoaded)return null;
 return <View style={st.wrap}>
  {prefs.local&&<LocalEngine key={epoch} system={SYSTEM_PROMPT} seed={seed} onState={setEngine}/>}
  <View style={st.card}>
   <Text style={st.h}>Your AI coach</Text>
   <Text style={st.m}>The engine decides loads, swaps and safety. The coach explains, answers and proposes changes you confirm.</Text>
   {!prefs.local?<>
     <Text style={st.m}>{supported.ok?`On-device model: ${LOCAL_MODEL_LABEL}, about ${MODEL_MB/1000} GB download. Runs offline, free, private.`:supported.why}</Text>
     <Pressable accessibilityRole="button" onPress={()=>void enableLocal()} style={[st.btn,!supported.ok&&{opacity:.5}]}><Text style={st.bt}>Download on-device coach</Text></Pressable>
    </>:<>
     <Text style={st.m}>{engine.error?`On-device coach error: ${engine.error}`:engine.ready?'On-device coach ready (offline).':`Preparing on-device coach… ${engine.progress.toFixed(0)}%`}</Text>
     {!engine.ready&&!engine.error&&<View style={st.bar}><View style={[st.fill,{width:`${Math.min(100,engine.progress)}%`}]}/></View>}
     <Pressable accessibilityRole="button" onPress={disableLocal} style={[st.btn,st.sec]}><Text style={[st.bt,{color:c.text}]}>Turn off on-device coach</Text></Pressable>
    </>}
   <View style={st.row}><View style={{flex:1}}><Text style={st.t}>Cloud help for heavy questions</Text><Text style={st.m}>{cloudOk?'Sends your question and a short plan summary to a free Google/OpenRouter model. Off by default.':'Not set up on the server yet.'}</Text></View><Switch accessibilityLabel="Cloud help" disabled={!cloudOk} value={prefs.cloud} onValueChange={v=>void savePrefs({...prefs,cloud:v})}/></View>
  </View>
  {msgs.map(m=><View key={m.id} style={[st.bubble,m.role==='user'?st.user:st.coach]}>
   <Text style={st.t}>{m.content||(busy?'…':'')}</Text>
   {m.role==='assistant'&&!!m.source&&<Text style={st.src}>{SOURCE_LABEL[m.source]}</Text>}
   {m.action&&m.actionState==='pending'&&<View style={st.act}><Text style={st.t}>{describeAction(m.action,items)}</Text><View style={st.row}><Pressable style={[st.btn,{flex:1}]} onPress={()=>void apply(m)}><Text style={st.bt}>Apply</Text></Pressable><Pressable style={[st.btn,st.sec,{flex:1}]} onPress={()=>patch(m.id,x=>({...x,actionState:'dismissed'}))}><Text style={[st.bt,{color:c.text}]}>Dismiss</Text></Pressable></View></View>}
   {m.actionState==='done'&&<Text style={st.src}>Applied</Text>}
   {m.role==='assistant'&&m.source==='local'&&prefs.cloud&&cloudOk&&m===msgs[msgs.length-1]&&!busy&&lastUser&&<Pressable onPress={()=>void send(lastUser,true)}><Text style={st.link}>Ask cloud instead</Text></Pressable>}
  </View>)}
  {busy&&engine.handle&&<Pressable onPress={()=>handleRef.current?.stop()}><Text style={st.link}>Stop</Text></Pressable>}
  <TextInput accessibilityLabel="Message your coach" value={input} onChangeText={setInput} placeholder={'Ask, or say "log 8 reps at 40 kg"'} placeholderTextColor={c.muted} multiline style={st.input}/>
  <Pressable accessibilityRole="button" disabled={busy} onPress={()=>void send(input)} style={[st.btn,busy&&{opacity:.5}]}><Text style={st.bt}>{busy?'Thinking…':'Send'}</Text></Pressable>
 </View>;
}
const st=StyleSheet.create({
 wrap:{gap:12},card:{backgroundColor:c.card,borderRadius:20,padding:18,gap:12,borderWidth:1,borderColor:c.line},h:{color:c.text,fontSize:20,fontWeight:'900'},t:{color:c.text,fontSize:16,lineHeight:23},m:{color:c.muted,fontSize:14,lineHeight:20},
 btn:{minHeight:48,justifyContent:'center',alignItems:'center',backgroundColor:c.blue,borderRadius:8,padding:12},sec:{backgroundColor:'transparent',borderWidth:1,borderColor:c.line},bt:{color:t.onVolt,fontWeight:'900',fontSize:13,letterSpacing:1.2,textTransform:'uppercase'},row:{flexDirection:'row',alignItems:'center',gap:10},
 bar:{height:6,borderRadius:3,backgroundColor:c.card2,overflow:'hidden'},fill:{height:6,backgroundColor:c.blue},
 bubble:{borderRadius:4,padding:14,gap:8,maxWidth:'92%'},user:{alignSelf:'flex-end',backgroundColor:t.indigoBubble,borderRadius:16},coach:{alignSelf:'flex-start',backgroundColor:'transparent',borderWidth:0,borderTopWidth:1,borderTopColor:c.line},
 src:{color:c.blue,fontSize:9,fontWeight:'900',letterSpacing:1.6},link:{color:c.blue,fontWeight:'700',fontSize:14},act:{gap:10,padding:12,borderRadius:4,backgroundColor:t.well,borderWidth:1,borderColor:c.line},
 input:{minHeight:52,maxHeight:140,borderWidth:1,borderColor:c.line,borderRadius:8,padding:13,color:c.text,fontSize:16,backgroundColor:t.well}
});
