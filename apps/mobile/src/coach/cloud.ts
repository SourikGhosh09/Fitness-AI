import {api} from '../api';
export async function cloudAvailable():Promise<boolean>{try{return !!(await api<any>('/coach/cloud/status')).available;}catch{return false;}}
export async function askCloud(system:string,history:{role:'user'|'assistant';content:string}[],message:string):Promise<string>{
 const r=await api<any>('/coach/cloud','POST',{system,history:history.slice(-8).map(h=>({role:h.role,content:h.content.slice(0,1900)})),message:message.slice(0,1900)});
 return String(r.reply||'');
}
