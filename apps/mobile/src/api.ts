import {buildMediaSource} from './media-source';
import {token,cache,cached,pending,acknowledge,markError} from './storage';
const origin=process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
if(!__DEV__&&!origin.startsWith('https://'))throw new Error('Production requires HTTPS');
export class ApiError extends Error { constructor(public status:number,message:string){super(message);} }
export async function api<T=any>(path:string,method='GET',body?:unknown):Promise<T>{
 const t=await token(); const controller=new AbortController(); const timeout=setTimeout(()=>controller.abort(),15000);
 try {const r=await fetch(origin+'/api/v1'+path,{method,headers:{'Content-Type':'application/json',...(t?{Authorization:`Bearer ${t}`}:{})},body:body===undefined?undefined:JSON.stringify(body),signal:controller.signal});if(!r.ok){const d=await r.json();throw new ApiError(r.status,typeof d.detail==='string'?d.detail:JSON.stringify(d.detail));}return r.status===204?undefined as T:await r.json();}finally{clearTimeout(timeout);}
}
export async function load<T>(path:string):Promise<{data:T;offline:boolean}>{try{const data=await api<T>(path);await cache(path,data);return {data,offline:false};}catch(e){if(e instanceof ApiError)throw e;const data=await cached<T>(path);if(data===null)throw e;return {data,offline:true};}}
let syncing=false;
export async function sync(){if(syncing)return;syncing=true;try{for(const item of await pending()){if(item.error)continue;try{await api('/sets','POST',JSON.parse(item.data));await acknowledge(item.id);}catch(e){if(e instanceof ApiError&&[409,422].includes(e.status)){await markError(item.id,e.message);continue;}throw e;}}}finally{syncing=false;}}

export async function tutorialMediaSource(path:string){return buildMediaSource(origin,path,(await token())||'');}
