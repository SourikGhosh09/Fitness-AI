/** Fitness AI survey installer and durable bridge. No participant data goes to ChatGPT.
 * Set API_BASE_URL and WEBHOOK_SECRET in Script Properties before connect().
 * Run createSurvey() first. It logs the form ID for backend SURVEY_FORM_ID.
 * Run connect() after backend configuration, then createParticipantLink() for each person.
 */
const FIT = {
  title: 'Fitness AI — Workout Feedback',
  code: 'Private participant code',
  action: 'What would you like to do?',
  agree: 'I am 18 or older and agree to contribute this workout to shared model training',
  withdraw: 'Withdraw my participation and delete my collected training data',
  date: 'Workout date (YYYY-MM-DD)',
  session: 'Which workout was this on that date?',
  exercise: 'Which exercise did you perform?',
  experience: 'Your training experience',
  sleep: 'Sleep before this workout — hours (optional)',
  energy: 'Energy before training — 1 very low to 5 very high (optional)',
  soreness: 'Soreness before training — 0 none to 5 very high (optional)',
  stress: 'Stress before training — 0 none to 5 very high (optional)',
  history: 'Your previous experience with this exact exercise',
  plannedReps: 'Planned reps per set (optional)',
  plannedLoad: 'Planned load per set — kg (optional)',
  targetRpe: 'Planned effort — 1 very easy to 10 maximum (optional)',
  enjoyment: 'Enjoyment — 1 disliked to 5 enjoyed (optional)',
  duration: 'Whole workout duration — minutes (optional)'
};
const EXPERIENCE = ['0 — Complete beginner','1 — Beginner','2 — Novice','3 — Intermediate','4 — Advanced','5 — Recreational athlete','6 — Competitive athlete'];
const HISTORY = ['First time ever doing this exercise','I previously logged this exercise using this participant link','I do not know / previous sessions were not logged'];
const COMMON = ['barbell bench press','barbell full squat','barbell deadlift','barbell bent over row','dumbbell bench press','dumbbell biceps curl','dumbbell lateral raise','push-up','pull-up','bodyweight squat','cable lat pulldown','cable seated row','dumbbell shoulder press','barbell curl','dumbbell concentration curl','plank','3/4 sit-up'];
function prop_(){return PropertiesService.getScriptProperties();}
function form_(){const id=prop_().getProperty('FORM_ID');if(!id)throw new Error('Run createSurvey first.');return FormApp.openById(id);}
function number_(form,title,min,max,required){
  return form.addTextItem().setTitle(title).setRequired(!!required).setValidation(FormApp.createTextValidation().requireNumberBetween(min,max).setHelpText('Enter a number from '+min+' to '+max+'.').build());
}
function choices_(form,title,choices,required){return form.addListItem().setTitle(title).setChoiceValues(choices).setRequired(!!required);}
function createSurvey(){
  if(prop_().getProperty('FORM_ID')){showLinks();return;}
  const form=FormApp.create(FIT.title,false);
  prop_().setProperty('FORM_ID',form.getId()); // Persist early so retries never create another form.
  form.setDescription('Log one exercise with up to three sets, using your private link. Participation is optional. We collect exercise results and optional readiness ratings to train shared difficulty-prediction models. Responses are stored in the organizer\'s Google account and Fitness AI backend. Names, email, photos and medical details are not requested. This survey does not provide a workout prescription. Keep your link private. You may edit an answer or withdraw using the same link. Do not submit another person\'s data.').setCollectEmail(false).setAllowResponseEdits(true).setPublishingSummary(false).setProgressBar(true).setShowLinkToRespondAgain(false).setConfirmationMessage('Thank you. Answers synchronize after the backend is connected. Updates train evaluated model candidates when enough eligible data exists; one answer does not immediately change workouts. Keep your private participant link and the edit-response link.');
  form.addTextItem().setTitle(FIT.code).setHelpText('Prefilled in your personal link. Please do not change this code.').setRequired(true).setValidation(FormApp.createTextValidation().requireTextMatchesPattern('^[A-Za-z0-9_-]{32,100}$').build());
  const action=form.addMultipleChoiceItem().setTitle(FIT.action).setRequired(true);
  const details=form.addPageBreakItem().setTitle('1 of 3 — Your workout');
  action.setChoices([action.createChoice(FIT.agree,details),action.createChoice(FIT.withdraw,FormApp.PageNavigationType.SUBMIT)]);
  form.addTextItem().setTitle(FIT.date).setHelpText('Example: 2026-09-12. Use the date where you trained.').setRequired(true).setValidation(FormApp.createTextValidation().requireTextMatchesPattern('^20[0-9]{2}-[0-9]{2}-[0-9]{2}$').build());
  choices_(form,FIT.session,['1','2','3'],true);
  choices_(form,FIT.exercise,['Connect the backend to load exercise choices'],true);
  choices_(form,FIT.experience,EXPERIENCE,false);
  number_(form,FIT.sleep,0,24,false);
  choices_(form,FIT.energy,['1','2','3','4','5'],false);
  choices_(form,FIT.soreness,['0','1','2','3','4','5'],false);
  choices_(form,FIT.stress,['0','1','2','3','4','5'],false);
  choices_(form,FIT.history,HISTORY,true);
  form.addPageBreakItem().setTitle('2 of 3 — The original plan (optional)').setHelpText('Use the original prescription, not a target invented after the workout. Leave unknown values blank. These targets apply to all sets in this response. Use the app for workouts with different targets across sets.');
  number_(form,FIT.plannedReps,1,50,false);number_(form,FIT.plannedLoad,0,600,false);number_(form,FIT.targetRpe,1,10,false);
  form.addPageBreakItem().setTitle('3 of 3 — What you completed').setHelpText('Record the load consistently: barbell including the bar; dumbbells combined; bodyweight-only = 0 kg. Record up to 3 sets. For more sets or skipped-set details, use the Fitness AI Contribute tab. Pain and unknown answers are not used as pain-free training examples.');
  for(let n=1;n<=3;n++){
    form.addSectionHeaderItem().setTitle('Set '+n+(n>1?' — leave all fields blank if not performed':''));
    number_(form,'Set '+n+' — completed reps',0,200,n===1);number_(form,'Set '+n+' — actual load kg',0,600,n===1);
    choices_(form,'Set '+n+' — actual effort (optional)',['1','2','3','4','5','6','7','8','9','10'],false).setHelpText('1 = very easy, 10 = maximum effort. Leave blank if unsure.');
    choices_(form,'Set '+n+' — pain or discomfort? (optional)',['No','Yes','Not sure / prefer not to answer'],false);
  }
  choices_(form,FIT.enjoyment,['1','2','3','4','5'],false);number_(form,FIT.duration,1,300,false);
  const book=SpreadsheetApp.create('Fitness AI — Private survey responses');
  form.setDestination(FormApp.DestinationType.SPREADSHEET,book.getId());
  book.insertSheet('_sync').appendRow(['response_id','content_hash','revision','acknowledged','status','last_attempt']);
  book.insertSheet('_catalog').appendRow(['exercise_label','exercise_id']);
  book.insertSheet('_participants').appendRow(['participant_label','private_link','created_at']);
  prop_().setProperties({SHEET_ID:book.getId(),FORM_READY:'true',TIME_ZONE:prop_().getProperty('TIME_ZONE')||'Asia/Kolkata'});
  showLinks();
}
function showLinks(){
  const form=form_();
  console.log(JSON.stringify({form_id:form.getId(),edit_url:form.getEditUrl(),response_url:form.getPublishedUrl(),sheet_url:SpreadsheetApp.openById(prop_().getProperty('SHEET_ID')).getUrl(),next:'Configure backend SURVEY_FORM_ID, then run connect(). Share personal links from createParticipantLink(), not the generic form link.'}));
}
function connect(){
  if(prop_().getProperty('FORM_READY')!=='true')throw new Error('Form creation is incomplete. Inspect it before connecting.');
  send_('/api/v1/survey/status',{});
  refreshExercises();
  const form=form_();
  ['surveySubmitted','reconcile'].forEach(name=>{
    if(!ScriptApp.getProjectTriggers().some(t=>t.getHandlerFunction()===name)){
      if(name==='surveySubmitted')ScriptApp.newTrigger(name).forForm(form).onFormSubmit().create();
      else ScriptApp.newTrigger(name).timeBased().everyMinutes(15).create();
    }
  });
  form.setPublished(true);form.setAcceptingResponses(true);showLinks();
}
function refreshExercises(){
  const catalog=send_('/api/v1/survey/catalog',{}).exercises;
  const configured=(prop_().getProperty('EXERCISE_IDS')||'').split(',').map(x=>x.trim()).filter(Boolean);
  const selected=catalog.filter(e=>configured.length?configured.includes(e.id):COMMON.includes(e.name.toLowerCase()));
  if(!selected.length)throw new Error('No matching catalog exercises. Import the dataset or configure EXERCISE_IDS.');
  if(selected.length>100)throw new Error('Use up to 100 exercises per survey for manageable mobile choices.');
  const labels={};selected.forEach(e=>{const label=selected.filter(x=>x.name===e.name).length>1?e.name+' ['+e.id+']':e.name;labels[label]=e.id;});
  item_(FIT.exercise).asListItem().setChoiceValues(Object.keys(labels));
  // Preserve old labels so historic responses still decode after refreshing choices.
  const previous=catalogMap_();Object.assign(previous,labels);
  const sheet=SpreadsheetApp.openById(prop_().getProperty('SHEET_ID')).getSheetByName('_catalog');
  const entries=Object.entries(previous);sheet.getRange(2,1,entries.length,2).setValues(entries);
}
function catalogMap_(){const rows=SpreadsheetApp.openById(prop_().getProperty('SHEET_ID')).getSheetByName('_catalog').getDataRange().getValues().slice(1);return Object.fromEntries(rows.filter(r=>r[0]));}
function item_(title){const i=form_().getItems().find(x=>x.getTitle()===title);if(!i)throw new Error('A required question was removed or renamed: '+title);return i;}
function createParticipantLink(){
  const code=Utilities.getUuid().replace(/-/g,'')+Utilities.getUuid().replace(/-/g,'');
  const result=send_('/api/v1/survey/enroll',{participant_code:code});
  if(result.status!=='ready')throw new Error('Enrollment was not accepted.');
  const form=form_();const link=form.createResponse().withItemResponse(item_(FIT.code).asTextItem().createResponse(code)).toPrefilledUrl();
  const sheet=SpreadsheetApp.openById(prop_().getProperty('SHEET_ID')).getSheetByName('_participants');
  sheet.appendRow(['Participant '+sheet.getLastRow(),link,new Date()]);
  console.log('Private participant link created. Copy the newest link from the _participants sheet; give it only to that participant.');
}
function answers_(response){const a={};response.getItemResponses().forEach(r=>a[r.getItem().getTitle()]=r.getResponse());return a;}
function optionalNumber_(value){if(value===undefined||value===null||value==='')return null;const n=Number(value);if(!Number.isFinite(n))throw new Error('Invalid numeric answer.');return n;}
function integer_(value){const n=optionalNumber_(value);if(n!==null&&!Number.isInteger(n))throw new Error('Reps and duration must be whole numbers.');return n;}
function event_(response){
  const a=answers_(response),code=String(a[FIT.code]||'');
  const event={response_id:response.getId(),revision:1,participant_code:code,operation:'upsert',adult:true,consent:true};
  if(a[FIT.action]!==FIT.agree)return Object.assign(event,{operation:'withdraw',adult:false,consent:false});
  const day=String(a[FIT.date]||'');if(!/^20\d\d-\d\d-\d\d$/.test(day))throw new Error('Workout date needs YYYY-MM-DD.');
  const zone=prop_().getProperty('TIME_ZONE')||'Asia/Kolkata';const when=Utilities.parseDate(day,zone,'yyyy-MM-dd');
  if(Utilities.formatDate(when,zone,'yyyy-MM-dd')!==day)throw new Error('Workout date does not exist.');
  if(when.getTime()>Date.now()+300000)throw new Error('Workout date cannot be in the future.');
  const map=catalogMap_();const exercise=map[a[FIT.exercise]];if(!exercise)throw new Error('Exercise is not in the configured catalog.');
  const sets=[];
  for(let n=1;n<=3;n++){
    const reps=integer_(a['Set '+n+' — completed reps']),load=optionalNumber_(a['Set '+n+' — actual load kg']);
    const rpe=optionalNumber_(a['Set '+n+' — actual effort (optional)']),pain=a['Set '+n+' — pain or discomfort? (optional)'];
    if(n>1&&reps===null&&load===null&&rpe===null&&!pain)continue;
    if(reps===null||load===null)throw new Error('A performed set needs both reps and actual load.');
    sets.push({reps:reps,load_kg:load,rpe:rpe,pain:pain==='No'?false:pain==='Yes'?true:null,skipped:false,
      planned_reps:integer_(a[FIT.plannedReps]),planned_load_kg:optionalNumber_(a[FIT.plannedLoad]),target_rpe:optionalNumber_(a[FIT.targetRpe])});
  }
  event.contribution={event_id:'survey_'+sha_(response.getId()).slice(0,40),session_id:'survey_'+day.replace(/-/g,'')+'_'+a[FIT.session],
    exercise_id:exercise,occurred_at:when.getTime()/1000+(Number(a[FIT.session])-1)*60,
    context:{experience:a[FIT.experience]?Number(String(a[FIT.experience]).split(' ')[0]):null,sleep_hours:optionalNumber_(a[FIT.sleep]),energy:optionalNumber_(a[FIT.energy]),soreness:optionalNumber_(a[FIT.soreness]),stress:optionalNumber_(a[FIT.stress])},
    history_mode:a[FIT.history]===HISTORY[0]?'first_time':a[FIT.history]===HISTORY[1]?'recorded':'unknown',sets:sets,
    enjoyment:optionalNumber_(a[FIT.enjoyment]),duration_minutes:integer_(a[FIT.duration])};
  return event;
}
function hex_(bytes){return bytes.map(b=>('0'+(b&255).toString(16)).slice(-2)).join('');}
function sha_(text){return hex_(Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,text,Utilities.Charset.UTF_8));}
function send_(path,payload){
  const props=prop_(),base=(props.getProperty('API_BASE_URL')||'').replace(/\/$/,'');const secret=props.getProperty('WEBHOOK_SECRET')||'';
  if(!/^https:\/\/[a-zA-Z0-9.-]+(?::443)?$/.test(base)||secret.length<32)throw new Error('Configure a public HTTPS API_BASE_URL origin and a secret of at least 32 characters.');
  const body=JSON.stringify(payload),stamp=String(Math.floor(Date.now()/1000)),nonce=Utilities.getUuid(),formId=props.getProperty('FORM_ID');
  const canonical=['POST',path,formId,stamp,nonce,sha_(body)].join('\n');
  const signature=hex_(Utilities.computeHmacSha256Signature(canonical,secret,Utilities.Charset.UTF_8));
  const result=UrlFetchApp.fetch(base+path,{method:'post',contentType:'application/json',payload:body,followRedirects:false,muteHttpExceptions:true,
    headers:{'X-Fitness-Timestamp':stamp,'X-Fitness-Nonce':nonce,'X-Fitness-Form':formId,'X-Fitness-Signature':signature}});
  const status=result.getResponseCode();if(status<200||status>=300)throw new Error('Backend returned HTTP '+status+'. Check configuration or the response; retries continue automatically.');
  return JSON.parse(result.getContentText());
}
function journal_(){return SpreadsheetApp.openById(prop_().getProperty('SHEET_ID')).getSheetByName('_sync');}
function syncOne_(response,rows,sheet){
  const id=response.getId();let index=rows.findIndex(r=>r[0]===id);if(index<0){rows.push([id,'',0,false,'new','']);index=rows.length-1;}
  let payload,invalid=false;
  try{payload=event_(response);}catch(e){invalid=true;payload={response_id:id,revision:1,operation:'delete'};}
  const contentHash=invalid?'invalid:'+sha_(JSON.stringify(answers_(response))):sha_(JSON.stringify(payload)),row=rows[index];
  if(row[1]===contentHash&&row[3]===true)return;
  if(row[1]!==contentHash){row[1]=contentHash;row[2]=Number(row[2])+1;row[3]=false;}
  payload.revision=Number(row[2]);row[4]='pending';row[5]=new Date();sheet.getRange(index+2,1,1,6).setValues([row]);SpreadsheetApp.flush();
  try{const result=send_('/api/v1/survey/events',payload);row[3]=true;row[4]=invalid?'Invalid answers — removed from training':result.status;
    sheet.getRange(index+2,1,1,6).setValues([row]);
    if(result.status==='withdrawn'||payload.operation==='withdraw'){purgeParticipant_(payload.participant_code);row[4]='withdrawn';sheet.getRange(index+2,1,1,6).setValues([row]);}
  }catch(e){row[3]=false;row[4]='Retry required — '+String(e.message).slice(0,160);sheet.getRange(index+2,1,1,6).setValues([row]);}
}
function surveySubmitted(e){
  const lock=LockService.getScriptLock();if(!lock.tryLock(1000))return;
  try{const sheet=journal_();const rows=sheet.getLastRow()>1?sheet.getRange(2,1,sheet.getLastRow()-1,6).getValues():[];syncOne_(e.response,rows,sheet);}finally{lock.releaseLock();}
}
function reconcile(){
  const lock=LockService.getScriptLock();if(!lock.tryLock(1000))return;
  try{
    const started=Date.now(),sheet=journal_(),rows=sheet.getLastRow()>1?sheet.getRange(2,1,sheet.getLastRow()-1,6).getValues():[];
    // Full authoritative scan catches edits to old responses; a timestamp cursor cannot.
    const responses=form_().getResponses(),present=new Set(responses.map(r=>r.getId()));
    let cursor=Number(prop_().getProperty('SYNC_CURSOR')||0);if(cursor>=responses.length)cursor=0;
    for(let offset=0;offset<responses.length;offset++){
      const i=(cursor+offset)%responses.length;syncOne_(responses[i],rows,sheet);
      if(Date.now()-started>210000){prop_().setProperty('SYNC_CURSOR',String(i+1));return;}
    }
    prop_().setProperty('SYNC_CURSOR','0');
    for(let i=0;i<rows.length;i++){
      const row=rows[i];if(present.has(row[0])||row[4]==='deleted'||row[4]==='withdrawn')continue;
      // Persist a stable delete revision before sending; preserve it on network retry.
      if(!String(row[4]).startsWith('delete')){row[2]=Number(row[2])+1;row[3]=false;}
      row[4]='delete pending';row[5]=new Date();sheet.getRange(i+2,1,1,6).setValues([row]);SpreadsheetApp.flush();
      try{send_('/api/v1/survey/events',{response_id:row[0],revision:Number(row[2]),operation:'delete'});row[3]=true;row[4]='deleted';}catch(e){row[4]='delete retry';}
      sheet.getRange(i+2,1,1,6).setValues([row]);
      if(Date.now()-started>240000)return;
    }
  }finally{lock.releaseLock();}
}
function purgeParticipant_(code){
  if(!code)return;
  const form=form_();form.getResponses().filter(r=>String(answers_(r)[FIT.code]||'')===code).forEach(r=>form.deleteResponse(r.getId()));
  const book=SpreadsheetApp.openById(prop_().getProperty('SHEET_ID'));
  book.getSheets().filter(s=>!s.getName().startsWith('_')).forEach(sheet=>{
    const values=sheet.getDataRange().getValues(),col=values[0].indexOf(FIT.code);if(col<0)return;
    for(let i=values.length-1;i>=1;i--)if(String(values[i][col])===code)sheet.deleteRow(i+1);
  });
  const links=book.getSheetByName('_participants'),values=links.getDataRange().getValues();
  for(let i=values.length-1;i>=1;i--)if(String(values[i][1]).includes(code))links.getRange(i+1,2).setValue('Withdrawn — private link removed');
}
function showTrainingStatus(){console.log(JSON.stringify(send_('/api/v1/survey/status',{})));}
