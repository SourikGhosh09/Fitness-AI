const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function store(){
 let token='user-a-session';const rows=new Map();
 const db={execAsync:async(sql)=>{if(sql.includes('DELETE FROM cache'))rows.clear();},runAsync:async(sql,key,value)=>{if(sql.startsWith('INSERT OR REPLACE INTO cache'))rows.set(key,value);},getFirstAsync:async(sql,key)=>rows.has(key)?{data:rows.get(key)}:null};
 const modules={'expo-sqlite':{openDatabaseAsync:async()=>db},'expo-secure-store':{getItemAsync:async()=>token,setItemAsync:async(k,v)=>{token=v;},deleteItemAsync:async()=>{token=null;}},'expo-crypto':{randomUUID:()=> 'test-id'}};
 const context={exports:{},require:(name)=>{if(!modules[name])throw Error(name);return modules[name];}};
 vm.runInNewContext(fs.readFileSync(require.resolve('../.test-contribution/storage.js'),'utf8'),context);
 return context.exports;
}
test('an old account cannot write a draft after logout',async()=>{const s=store();await s.clear();await s.setToken('user-b-session');assert.equal(await s.cacheForSession('draft:a',{private:'a'},'user-a-session'),false);assert.equal(await s.cached('draft:a'),null);});
test('queued writes cannot resurrect a draft after cache erasure',async()=>{const s=store();const first=s.cacheForSession('draft:a',{reps:8},'user-a-session');const clear=s.clear();const late=s.cacheForSession('draft:a',{reps:10},'user-a-session');await Promise.all([first,clear,late]);assert.equal(await s.cached('draft:a'),null);assert.equal(await s.token(),null);});
test('current session saves and reloads its draft',async()=>{const s=store();assert.equal(await s.cacheForSession('draft:a',{reps:8},'user-a-session'),true);assert.equal((await s.cached('draft:a')).reps,8);});
