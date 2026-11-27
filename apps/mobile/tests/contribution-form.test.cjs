const test=require('node:test');
const assert=require('node:assert/strict');
const {makePayload,copySet}=require('../.test-contribution/contribution-form.js');
function draft(){return {event_id:'uuid_submission_01',session_id:'uuid_session_0001',date:'2026-09-10',exercise:{id:'source:0001'},context:{experience:null,sleep_hours:'',energy:null,soreness:null,stress:null},history_mode:'unknown',sets:[{reps:'8',load:'20',rpe:null,pain:null,skipped:false}],knowPlan:false,plannedReps:'',plannedLoad:'',targetRpe:null,enjoyment:null,duration:''};}
test('unknown is not converted to zero or the target',()=>{const p=makePayload(draft());assert.equal(p.context.sleep_hours,null);assert.equal(p.sets[0].rpe,null);assert.equal(p.sets[0].planned_load_kg,null);assert.equal(p.sets[0].pain,null);});
test('copied sets keep only entered reps and load, not inferred feedback',()=>{assert.deepEqual(copySet({reps:'8',load:'20',rpe:8,pain:false,skipped:false}),{reps:'8',load:'20',rpe:null,pain:null,skipped:false});});
test('actual weight and reps need valid numbers',()=>{for(const value of ['','NaN','-5','Infinity']){const d=draft();d.sets[0].load=value;assert.throws(()=>makePayload(d));}const d=draft();d.sets[0].reps='8.5';assert.throws(()=>makePayload(d));});
test('actual and planned values remain distinct',()=>{const d=draft();d.knowPlan=true;d.plannedReps='10';d.plannedLoad='25';d.targetRpe=7;const p=makePayload(d);assert.equal(p.sets[0].reps,8);assert.equal(p.sets[0].planned_reps,10);assert.equal(p.sets[0].planned_load_kg,25);assert.equal(p.sets[0].load_kg,20);});
test('bad dates and future dates rejected',()=>{for(const date of ['2026-02-30','not a date','2099-01-01']){assert.throws(()=>makePayload({...draft(),date},new Date('2026-09-11T12:00:00Z')));}});
