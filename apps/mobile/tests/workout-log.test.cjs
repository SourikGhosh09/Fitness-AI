const test=require('node:test');
const assert=require('node:assert/strict');
const L=require('../.test-log/workout-log.js');
test('dates: validation, shifting across month/year/leap boundaries',()=>{
 assert.equal(L.isIsoDate('2026-02-29'),false);assert.equal(L.isIsoDate('2028-02-29'),true);assert.equal(L.isIsoDate('26-1-1'),false);
 assert.equal(L.shiftDate('2026-10-31',1),'2026-11-01');assert.equal(L.shiftDate('2026-12-31',1),'2027-01-01');assert.equal(L.shiftDate('2026-03-01',-1),'2026-02-28');
 assert.throws(()=>L.shiftDate('nope',1));
});
test('week runs Monday to Sunday and labels match the reference week',()=>{
 const w=L.weekDates('2026-10-28');
 assert.deepEqual([w[0],w[6]],['2026-10-26','2026-11-01']);assert.equal(L.weekDates('2026-11-01')[0],'2026-10-26');assert.equal(L.weekDates('2026-10-26')[0],'2026-10-26');
 assert.equal(L.dayLabel('2026-10-26'),'Mon 26');assert.equal(L.dayLabel('2026-11-01'),'Sun 1');
});
test('clock formatting and countdown never go negative',()=>{
 assert.equal(L.formatClock(0),'0:00');assert.equal(L.formatClock(75),'1:15');assert.equal(L.formatClock(3725),'1:02:05');assert.equal(L.formatClock(-5),'0:00');assert.equal(L.formatClock(NaN),'0:00');
 assert.equal(L.remaining(110,100.2),10);assert.equal(L.remaining(100,120),0);
});
test('elapsed time uses stored timestamps, pauses and end time',()=>{
 const s={started_at:1000,ended_at:null,paused_seconds:60};
 assert.equal(L.elapsedSeconds(s,1600),540);assert.equal(L.elapsedSeconds(s,1600,1300),240);
 assert.equal(L.elapsedSeconds({...s,ended_at:1900},9999),840);assert.equal(L.elapsedSeconds({started_at:null,ended_at:null,paused_seconds:0},5),0);
 assert.equal(L.elapsedSeconds({started_at:1000,ended_at:null,paused_seconds:5000},1100),0);
});
test('numeric input parsing keeps unknown as null and clamps',()=>{
 assert.equal(L.parseNum(''),null);assert.equal(L.parseNum('abc'),null);assert.equal(L.parseNum('7,5'),7.5);assert.equal(L.parseNum('-3'),0);assert.equal(L.parseNum('5000',0,1000),1000);assert.equal(L.parseNum('0'),0);
});
function session(){const s=L.emptySession('Push');s.exercises=[L.newExercise('Bench press','ex:1'),L.newExercise('Plank')];s.exercises[0].sets[0].weight_kg=45;s.exercises[0].sets[0].reps=5;return s;}
test('ticking a set starts the session, records time and returns the rest to run',()=>{
 const r=L.setDone(session(),0,0,true,5000);
 assert.equal(r.session.status,'in_progress');assert.equal(r.session.started_at,5000);assert.equal(r.session.exercises[0].sets[0].completed_at,5000);assert.equal(r.rest,90);
 const undo=L.setDone(r.session,0,0,false,5100);assert.equal(undo.session.exercises[0].sets[0].done,false);assert.equal(undo.session.exercises[0].sets[0].completed_at,null);assert.equal(undo.rest,0);
 assert.equal(L.setDone(session(),9,0,true,1).rest,0);
});
test('no rest after the last set of an exercise; per-set rest overrides exercise rest',()=>{
 let s=session();s.exercises[0].sets[2].done=true;s.exercises[0].sets[1].done=true;
 assert.equal(L.setDone(s,0,0,true,10).rest,0);
 s=session();s.exercises[0].sets[0].rest_seconds=30;assert.equal(L.setDone(s,0,0,true,10).rest,30);
});
test('volume counts only completed rep sets, not timed sets',()=>{
 let s=session();s=L.setDone(s,0,0,true,10).session;s.exercises[1].sets[0]={...s.exercises[1].sets[0],kind:'seconds',weight_kg:7.5,reps:30,done:true};
 assert.deepEqual(L.stats(s),{total:6,done:2,volume:225});
});
test('payload drops server-only fields; export text lists sets',()=>{
 const s={...session(),date:'2026-10-26',updated_at:1,previous:{}};const p=L.toPayload(s);
 assert.equal('date' in p,false);assert.equal('previous' in p,false);assert.equal(p.title,'Push');
 const t=L.sessionText('2026-10-26',L.setDone(session(),0,0,true,10).session);
 assert.match(t,/Mon 26 \(2026-10-26\) - Push/);assert.match(t,/Set 1: 45 kg x 5 reps \| done/);assert.match(t,/Set 2: - x - reps \| not done/);
});
test('new sets copy the previous load but never its completion',()=>{
 const n=L.newSet({kind:'reps',weight_kg:40,reps:8,rir:2,done:true,completed_at:9,rest_seconds:60});
 assert.deepEqual(n,{kind:'reps',weight_kg:40,reps:8,rir:2,done:false,completed_at:null,rest_seconds:null});
});
