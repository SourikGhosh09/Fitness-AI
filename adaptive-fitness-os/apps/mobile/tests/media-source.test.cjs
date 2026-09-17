const {test}=require('node:test');
const assert=require('node:assert/strict');
const {buildMediaSource}=require('../.test-media/media-source.js');
test('media credential goes only to configured backend',()=>{
 const source=buildMediaSource('https://fitness.example','/api/v1/exercises/source%3A0001/media/gif','synthetic-token');
 assert.equal(source.uri,'https://fitness.example/api/v1/exercises/source%3A0001/media/gif');
 assert.equal(source.headers.Authorization,'Bearer synthetic-token');
});
test('external and manipulated URLs cannot receive credentials',()=>{
 for(const path of ['https://evil.example/gif','//evil.example/gif','/api/v1/exercises/../secret/media/gif','/api/v1/exercises/source%3A0001/media/gif?next=evil','/api/v1/exercises/source%3A0001/media/gif#fragment']){
  assert.throws(()=>buildMediaSource('https://fitness.example',path,'synthetic-token'));
 }
});
test('reject unsafe API origin and missing credential',()=>{
 const path='/api/v1/exercises/source%3A0001/media/gif';
 for(const origin of ['file:///tmp/','https://user:secret@fitness.example','https://fitness.example/subpath','https://fitness.example?param=1']){
  assert.throws(()=>buildMediaSource(origin,path,'synthetic-token'));
 }
 assert.throws(()=>buildMediaSource('https://fitness.example',path,''));
});
