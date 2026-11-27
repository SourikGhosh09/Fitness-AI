import React,{useEffect,useState,useRef} from 'react';
import {View,Text,Switch,Pressable,StyleSheet,Alert,ActivityIndicator} from 'react-native';
import {api} from './api';
import {token} from './storage';
type State={enabled:boolean;participant_code:string|null;consent_version:string;configured:boolean;imported_workouts:number;needs_attention:number;last_success_at:number|null;worker_status:string};
export function NotionSettings(){
 const session=useRef<string|null>(null),mounted=useRef(true);
 const [state,setState]=useState<State|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState('');
 async function refresh(){setBusy(true);setError('');try{const current=await token();if(!current||(session.current&&session.current!==current))throw new Error('Sign-in changed. Reopen Settings.');session.current=current;const next=await api<State>('/integrations/notion','GET',undefined,current);if(mounted.current&&await token()===current)setState(next);}catch(e){setError(e instanceof Error?e.message:'Unable to load Notion settings');}finally{setBusy(false);}}
 useEffect(()=>{mounted.current=true;void refresh();return()=>{mounted.current=false;};},[]);
 async function change(enabled:boolean){setBusy(true);setError('');try{const current=session.current;if(!current)throw new Error('Refresh Settings first.');const next=await api<State>('/integrations/notion/consent','PUT',{enabled,consent_version:'notion-import-v1'},current);if(mounted.current&&await token()===current)setState(next);}catch(e){setError(e instanceof Error?e.message:'Your choice was not saved');}finally{setBusy(false);}}
 function toggle(enabled:boolean){Alert.alert(enabled?'Import my Notion answers?':'Stop Notion imports?',enabled?'Your exercise sets, optional effort and recovery answers collected in the owner’s private Notion database will be copied to this account for shared-learning review. Names, contacts and notes are not imported. Enable shared learning above first. You can withdraw here.':'Imported records will be removed from the backend and affected models retired. Known Notion rows will be queued for clearing and trashing when the worker can connect. Notion may retain historical versions. Your regular app workout history remains.',[{text:'Cancel',style:'cancel'},{text:enabled?'Allow imports':'Stop imports',style:enabled?'default':'destructive',onPress:()=>void change(enabled)}]);}
 const recent=Boolean(state?.last_success_at&&Date.now()/1000-state.last_success_at<900);
 return <View style={s.card}><Text style={s.heading}>Notion collection</Text>
 <Text style={s.text}>Bring your consented Notion survey answers into this app’s contribution queue. Importing data does not train or deploy an AI model.</Text>
 {busy&&<ActivityIndicator accessibilityLabel="Loading or saving Notion settings" color="#d1f599"/>}
 {!!error&&<Text accessibilityLiveRegion="polite" style={s.error}>{error}</Text>}
 {state&&<><View style={s.row}><Text style={s.text}>Allow my Notion answers to be imported</Text><Switch accessibilityLabel="Allow Notion answer imports" value={state.enabled} disabled={busy} onValueChange={toggle}/></View>
 <Text accessibilityLiveRegion="polite" style={s.text}>{!state.configured?'Server connection needs setup':!state.enabled?'Imports are off':recent&&state.worker_status==='ok'?'Worker checked Notion recently':state.worker_status==='cleanup_pending'?'Remote removal still pending':state.worker_status==='retrying'?'Worker is retrying; check server connection':'Waiting for a successful worker check'}</Text>
 {state.last_success_at&&<Text style={s.text}>Last successful check: {new Date(state.last_success_at*1000).toLocaleString()}</Text>}
 {state.enabled&&<><Text style={s.text}>Give this participant code privately to the collection owner. Use the same code on every Notion set belonging to you:</Text><Text selectable style={s.code}>{state.participant_code}</Text><Text style={s.text}>Consent version: {state.consent_version}. The owner must record your explicit answers and the consent date. Other participants should not receive database access.</Text></>}
 <Text style={s.text}>{state.imported_workouts} exercise contributions imported · {state.needs_attention} need correction</Text>
 <Text style={s.text}>This connection imports from Notion. Workouts recorded directly in this app are not sent to Notion. Turning off shared learning also stops these imports.</Text></>}
 <Pressable style={s.button} accessibilityRole="button" disabled={busy} onPress={()=>void refresh()}><Text style={s.link}>Refresh connection status</Text></Pressable></View>;
}
const s=StyleSheet.create({card:{backgroundColor:'#1c2a23',borderRadius:24,padding:22,gap:16,borderWidth:1,borderColor:'#35473b'},heading:{fontSize:23,lineHeight:29,color:'#f1f5ee',fontWeight:'600'},text:{color:'#b5c3b9',fontSize:15,lineHeight:23,flexShrink:1},row:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:12},button:{minHeight:48,justifyContent:'center'},link:{color:'#d1f599',fontSize:16,fontWeight:'600'},code:{color:'#f1f5ee',fontSize:16,lineHeight:24},error:{color:'#ffb4a9',fontSize:15,lineHeight:23}});
