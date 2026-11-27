const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm'),crypto=require('node:crypto');
const source=fs.readFileSync(__dirname+'/Code.gs','utf8');
function runtime(){
 const properties={FORM_ID:'test-form-id',SHEET_ID:'sheet',TIME_ZONE:'UTC',API_BASE_URL:'https://fitness.example.test',WEBHOOK_SECRET:'a-test-secret-with-at-least-thirty-two-chars'};
 const calls=[],ledger=[];let failure=false;const answers={};
 const journal={getRange(row,col,n,w){return{setValues(values){ledger[row-2]=values[0].slice();return this;}};}};
 const catalog={getDataRange(){return{getValues(){return[['exercise_label','exercise_id'],['Test exercise','test:0']];}};}};
 const context={console,Date,Set,JSON,Number,Object,String,Math,Error,
  PropertiesService:{getScriptProperties(){return{getProperty:k=>properties[k]||null,setProperty(k,v){properties[k]=v;}};}},
  SpreadsheetApp:{openById(){return{getSheetByName(name){return name==='_catalog'?catalog:journal;}};},flush(){}},
  Utilities:{Charset:{UTF_8:'utf8'},DigestAlgorithm:{SHA_256:'sha256'},getUuid:()=>crypto.randomUUID(),
   computeDigest:(algorithm,text)=>Array.from(crypto.createHash('sha256').update(text).digest()),
   computeHmacSha256Signature:(text,key)=>Array.from(crypto.createHmac('sha256',key).update(text).digest()),
   parseDate:day=>new Date(day+'T00:00:00Z'),formatDate:d=>d.toISOString().slice(0,10)},
  UrlFetchApp:{fetch(url,options){calls.push({url,options});if(failure)throw new Error('Temporary test outage');return{getResponseCode:()=>200,getContentText:()=>JSON.stringify({status:'active'})};}}};
 vm.createContext(context);vm.runInContext(source,context);
 const FIT=vm.runInContext('FIT',context);
 Object.assign(answers,{[FIT.code]:'a'.repeat(64),[FIT.action]:FIT.agree,[FIT.date]:'2026-01-01',[FIT.session]:'1',[FIT.exercise]:'Test exercise',[FIT.history]:'First time ever doing this exercise','Set 1 — completed reps':'6','Set 1 — actual load kg':'10'});
 const response={getId:()=> 'response-one',getItemResponses:()=>Object.entries(answers).map(([key,value])=>({getItem:()=>({getTitle:()=>key}),getResponse:()=>value}))};
 return{context,FIT,answers,response,calls,ledger,journal,fail(v){failure=v;}};
}
test('optional answers remain unknown and no target effort is invented',()=>{
 const r=runtime(),event=r.context.event_(r.response);
 assert.equal(event.contribution.context.energy,null);assert.equal(event.contribution.sets[0].rpe,null);assert.equal(event.contribution.sets[0].pain,null);assert.equal(event.contribution.sets[0].target_rpe,null);
 assert.equal(event.contribution.exercise_id,'test:0');assert.equal(event.contribution.sets.length,1);
});
test('bridge HMAC covers exact UTF-8 body, form, route, timestamp and nonce; redirects disabled',()=>{
 const r=runtime();r.context.send_('/api/v1/survey/status',{note:'বাংলা'});const req=r.calls[0];const h=req.options.headers;
 const text=['POST','/api/v1/survey/status',h['X-Fitness-Form'],h['X-Fitness-Timestamp'],h['X-Fitness-Nonce'],crypto.createHash('sha256').update(req.options.payload).digest('hex')].join('\n');
 assert.equal(h['X-Fitness-Signature'],crypto.createHmac('sha256','a-test-secret-with-at-least-thirty-two-chars').update(text).digest('hex'));
 assert.equal(req.options.followRedirects,false);
});
test('network retries keep the same revision, edits increment it and duplicate scans send nothing',()=>{
 const r=runtime(),rows=[];r.fail(true);r.context.syncOne_(r.response,rows,r.journal);assert.equal(rows[0][3],false);
 r.fail(false);r.context.syncOne_(r.response,rows,r.journal);assert.equal(rows[0][3],true);
 assert.deepEqual(r.calls.map(c=>JSON.parse(c.options.payload).revision),[1,1]);
 r.context.syncOne_(r.response,rows,r.journal);assert.equal(r.calls.length,2);
 r.answers['Set 1 — completed reps']='7';r.context.syncOne_(r.response,rows,r.journal);assert.equal(JSON.parse(r.calls[2].options.payload).revision,2);
});
test('invalid edits remove the previously eligible response and can later be corrected',()=>{
 const r=runtime(),rows=[];r.context.syncOne_(r.response,rows,r.journal);
 r.answers['Set 1 — completed reps']='6.5';r.context.syncOne_(r.response,rows,r.journal);
 assert.equal(JSON.parse(r.calls[1].options.payload).operation,'delete');
 r.answers['Set 1 — completed reps']='8';r.context.syncOne_(r.response,rows,r.journal);
 assert.equal(JSON.parse(r.calls[2].options.payload).revision,3);assert.equal(JSON.parse(r.calls[2].options.payload).operation,'upsert');
});
test('withdrawal needs no workout answers and failed Google cleanup retries',()=>{
 const r=runtime(),rows=[];r.answers[r.FIT.action]=r.FIT.withdraw;delete r.answers[r.FIT.date];
 assert.equal(r.context.event_(r.response).operation,'withdraw');
 r.context.purgeParticipant_=()=>{throw new Error('Temporary cleanup failure');};r.context.syncOne_(r.response,rows,r.journal);assert.equal(rows[0][3],false);
 r.context.purgeParticipant_=()=>{};r.context.syncOne_(r.response,rows,r.journal);assert.equal(rows[0][3],true);assert.equal(rows[0][4],'withdrawn');
});
