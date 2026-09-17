import * as SQLite from 'expo-sqlite';
import * as SecureStore from 'expo-secure-store';
import * as Crypto from 'expo-crypto';
const database = SQLite.openDatabaseAsync('fitness.db');
let writes:Promise<unknown>=Promise.resolve();
function serial<T>(fn:()=>Promise<T>):Promise<T>{const next=writes.then(fn,fn);writes=next.catch(()=>{});return next;}
export async function init() { const db=await database; await db.execAsync('PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, data TEXT NOT NULL); CREATE TABLE IF NOT EXISTS outbox (id TEXT PRIMARY KEY, data TEXT NOT NULL, error TEXT);'); }
export async function token(){return SecureStore.getItemAsync('session');}
export async function setToken(value:string){await SecureStore.setItemAsync('session',value);}
export async function cached<T>(key:string):Promise<T|null>{const d=await database;const r=await d.getFirstAsync<{data:string}>('SELECT data FROM cache WHERE key=?',key);return r?JSON.parse(r.data):null;}
export async function cache(key:string,value:unknown){return serial(async()=>{const d=await database;await d.runAsync('INSERT OR REPLACE INTO cache(key,data) VALUES (?,?)',key,JSON.stringify(value));});}
export async function cacheForSession(key:string,value:unknown,expectedSession:string){return serial(async()=>{if(!expectedSession||(await token())!==expectedSession)return false;const d=await database;await d.runAsync('INSERT OR REPLACE INTO cache(key,data) VALUES (?,?)',key,JSON.stringify(value));return true;});}
export async function queue(payload:object){const d=await database;const id=Crypto.randomUUID();await d.runAsync('INSERT INTO outbox(id,data) VALUES (?,?)',id,JSON.stringify({...payload,event_id:id}));return id;}
export async function pending(){const d=await database;return d.getAllAsync<{id:string;data:string;error:string|null}>('SELECT * FROM outbox ORDER BY rowid');}
export async function acknowledge(id:string){const d=await database;await d.runAsync('DELETE FROM outbox WHERE id=?',id);}
export async function markError(id:string,error:string){const d=await database;await d.runAsync('UPDATE outbox SET error=? WHERE id=?',error,id);}
export async function clear(){return serial(async()=>{const d=await database;await d.execAsync('DELETE FROM cache; DELETE FROM outbox;');await SecureStore.deleteItemAsync('session');});}
