// Mounts the on-device model only when the user has opted in. Downloads (resumable) then loads it; unmounting frees native memory.
import {useEffect,useRef} from 'react';
import {models,useLLMChatSession,setTelemetryEnabled} from 'react-native-executorch';
type ChatMessage={role:'system'|'user'|'assistant';content:string};
setTelemetryEnabled(false);
export const LOCAL_MODEL=models.llm.QWEN2_5_1_5B.XNNPACK_8DA4W;
export const LOCAL_MODEL_LABEL='Qwen 2.5 1.5B (4-bit weights)';
export type LocalHandle={send:(text:string,onToken:(t:string)=>void)=>Promise<string>;stop:()=>void;usage:()=>number};
export function LocalEngine({system,seed,onState}:{system:string;seed:{role:'user'|'assistant';content:string}[];onState:(s:{ready:boolean;progress:number;error:string|null;handle:LocalHandle|null})=>void}){
 const initial=useRef<ChatMessage[]>([{role:'system',content:system},...seed.map(m=>({role:m.role,content:m.content}))]).current;
 const s=useLLMChatSession(LOCAL_MODEL,{initialMessages:initial,generationConfig:{maxNewTokens:320,temperature:0.5}});
 useEffect(()=>{
  const {sendMessage,stop,getKVCacheState}=s;
  const handle:LocalHandle|null=s.isReady&&sendMessage?{
   send:async(text,onToken)=>{const turn=await sendMessage(text,onToken);const last=[...turn.messages].reverse().find(m=>m.role==='assistant');return typeof last?.content==='string'?last.content:'';},
   stop:()=>{stop?.();},usage:()=>getKVCacheState?.().usageRatio??0}:null;
  onState({ready:s.isReady,progress:s.downloadProgress,error:s.error?String((s.error as Error).message??s.error):null,handle});
  // eslint-disable-next-line react-hooks/exhaustive-deps
 },[s.isReady,s.downloadProgress,s.error]);
 return null;
}
