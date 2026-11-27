const test=require('node:test');const assert=require('node:assert/strict');
const c=require('../.test-coach/coach-core.js');
const items=[{exercise_id:'a1',name:'Barbell Bench Press',sets:3,reps:8,load_kg:40,rpe:7},{exercise_id:'b2',name:'Dumbbell Row',sets:3,reps:10,load_kg:20,rpe:7}];
test('safety gate catches emergencies and pain before any model',()=>{
 assert.match(c.safetyCheck('I have chest pain'),/urgent medical/);
 assert.match(c.safetyCheck('my shoulder hurts'),/Pause/);
 assert.equal(c.safetyCheck('what is a good split'),null);
});
test('parseReply extracts one valid action and strips the line',()=>{
 const r=c.parseReply('Logging that for you.\nACTION: {"type":"log_set","exercise":"bench","set_number":1,"reps":8,"load_kg":40,"rpe":7}');
 assert.equal(r.reply,'Logging that for you.');assert.equal(r.action.type,'log_set');assert.equal(r.action.pain,false);
});
test('invalid or out-of-range actions are dropped',()=>{
 for(const bad of ['{"type":"log_set","exercise":"x","set_number":1,"reps":900,"load_kg":40,"rpe":7}','{"type":"log_set","exercise":"x","set_number":1,"reps":5,"load_kg":-1,"rpe":7}','{"type":"log_set","exercise":"x","set_number":1,"reps":5,"load_kg":40}','{"type":"delete_account"}','{"type":"set_training_days","days":[9]}','{"type":"regenerate","reason":"yolo"}','not json {'])
  assert.equal(c.parseReply('ok\nACTION: '+bad).action,null,bad);
});
test('only the first action is kept',()=>{
 const r=c.parseReply('x\nACTION: {"type":"regenerate","reason":"time"}\nACTION: {"type":"regenerate","reason":"fatigue"}');
 assert.equal(r.action.reason,'time');assert.ok(!r.reply.includes('ACTION'));
});
test('skipped set needs no rpe and forces zeros',()=>{
 const a=c.validateAction({type:'log_set',exercise:'row',set_number:2,skipped:true,reps:5,load_kg:30});
 assert.deepEqual([a.reps,a.load_kg,a.rpe],[0,0,null]);
});
test('training days are deduped and sorted',()=>assert.deepEqual(c.validateAction({type:'set_training_days',days:[4,0,4,2]}).days,[0,2,4]));
test('resolveExercise matches fuzzy names, numbers, and refuses ambiguity',()=>{
 assert.equal(c.resolveExercise('bench press',items).exercise_id,'a1');
 assert.equal(c.resolveExercise('row',items).exercise_id,'b2');
 assert.equal(c.resolveExercise('2',items).exercise_id,'b2');
 assert.equal(c.resolveExercise('squat',items),null);
 assert.equal(c.resolveExercise('dumbbell',[...items,{exercise_id:'c3',name:'Dumbbell Curl',sets:3}]),null);
});
test('buildState is compact and reflects logged sets',()=>{
 const s=c.buildState({profile:{display_name:'S',goals:{strength:50},minutes:40,days:[0,2],equipment:['barbell']},workout:{id:'w',status:'planned',readiness:80,items},logged:{'w:a1:1':true}});
 assert.match(s,/Barbell Bench Press: 3x8 @40kg RPE 7, 1\/3 sets logged/);assert.ok(s.length<800);
});
test('routing: safety wins, local default, cloud for heavy/unavailable local, rules last',()=>{
 const base={localReady:true,localSupported:true,cloudEnabled:true,cloudAvailable:true,text:'how was my last session'};
 assert.equal(c.chooseRoute({...base,text:'my knee hurts'}),'safety');
 assert.equal(c.chooseRoute(base),'local');
 assert.equal(c.chooseRoute({...base,text:'design me a 12-week plan'}),'cloud');
 assert.equal(c.chooseRoute({...base,localReady:false}),'cloud');
 assert.equal(c.chooseRoute({...base,localFailed:true}),'cloud');
 assert.equal(c.chooseRoute({...base,cloudEnabled:false,localReady:false}),'rules');
 assert.equal(c.chooseRoute({...base,cloudEnabled:false,text:'design me a 12-week plan'}),'local');
 assert.equal(c.chooseRoute({...base,forceCloud:true}),'cloud');
});
