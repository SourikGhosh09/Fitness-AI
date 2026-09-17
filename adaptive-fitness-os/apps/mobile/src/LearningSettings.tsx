import React,{useEffect,useState} from 'react';
import {View,Text,Switch,Pressable,StyleSheet,Alert,ActivityIndicator} from 'react-native';
import {api} from './api';
type State={account_id:string;consent:boolean;eligible_examples:number;pending_review:number;contributions:number;pending_contributions:number;model_version:string|null;mode:'rules'|'shadow'|'live'};
export function LearningSettings(){
 const [state,setState]=useState<State|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(''),[details,setDetails]=useState(false);
 async function refresh(){setBusy(true);setError('');try{setState(await api<State>('/learning/status'));}catch(e){setError(e instanceof Error?e.message:'Unable to load learning settings');}finally{setBusy(false);}}
 useEffect(()=>{void refresh();},[]);
 async function change(enabled:boolean){setBusy(true);setError('');try{setState(await api<State>('/learning/consent','PUT',{enabled}));}catch(e){setError(e instanceof Error?e.message:'Your choice was not saved');}finally{setBusy(false);}}
 function toggle(enabled:boolean){if(enabled)void change(true);else Alert.alert('Stop contributing?','Your learning examples will be deleted and models that used them retired. Your workout history stays available.',[{text:'Cancel',style:'cancel'},{text:'Stop contributing',style:'destructive',onPress:()=>void change(false)}]);}
 return <View style={s.card}><Text style={s.heading}>Help improve training</Text><Text style={s.text}>Optionally contribute workout prescriptions, completed sets, experience and readiness ratings to a shared difficulty-prediction model. Names, email, medical notes and chats are excluded from its inputs. Other users cannot see your records.</Text>
 {busy&&<ActivityIndicator accessibilityLabel="Saving or loading learning settings" color="#d1f599"/>}
 {!!error&&<Text accessibilityLiveRegion="polite" style={s.error}>{error}</Text>}
 {state&&<><View style={s.row}><Text style={s.text}>Contribute my workout data</Text><Switch disabled={busy} accessibilityLabel="Contribute workout data to shared model training" value={state.consent} onValueChange={toggle}/></View>
 <Text style={s.text}>{state.eligible_examples} eligible sets · {state.pending_review} imported sets awaiting review · {state.pending_contributions} guided contributions awaiting review</Text>
 <Text style={s.text}>{state.mode==='rules'?'No neural model deployed · training uses the existing rules':state.mode==='shadow'?'Neural model in evaluation · workout rules remain active':'Reviewed neural difficulty estimates enabled'}</Text>
 <Text style={s.text}>Only completed, pain-free sets that match their recorded reps and load are used by this first model. Participation is optional. You can stop contributing here at any time.</Text>
 <Pressable accessibilityRole="button" accessibilityState={{expanded:details}} onPress={()=>setDetails(!details)} style={s.button}><Text style={s.link}>{details?'Hide details':'How training works'}</Text></Pressable>
 {details&&<><Text style={s.text}>The server trains a neural network with two hidden layers on eligible outcomes. New models must pass evaluation and operator review before changing workouts. More records do not guarantee a better model. Use the Contribute tab to log your own workouts with simple controls and unknown answers. CSV imports remain available for larger datasets.</Text><Text style={s.text}>Your account ID for importing your records:</Text><Text selectable style={s.text}>{state.account_id}</Text><Text style={s.text}>Model: {state.model_version||'No evaluated model deployed'}</Text></>}
 </>}
 <Pressable disabled={busy} accessibilityRole="button" onPress={()=>void refresh()} style={s.button}><Text style={s.link}>Refresh learning status</Text></Pressable></View>;
}
const s=StyleSheet.create({card:{backgroundColor:'#1c2a23',borderRadius:24,padding:22,gap:16,borderWidth:1,borderColor:'#35473b'},heading:{fontSize:23,lineHeight:29,color:'#f1f5ee',fontWeight:'600'},text:{color:'#b5c3b9',fontSize:15,lineHeight:23,flexShrink:1},row:{flexDirection:'row',alignItems:'center',justifyContent:'space-between',gap:12},button:{minHeight:48,justifyContent:'center'},link:{color:'#d1f599',fontSize:16,fontWeight:'600'},error:{color:'#ffb4a9',fontSize:15,lineHeight:23}});
