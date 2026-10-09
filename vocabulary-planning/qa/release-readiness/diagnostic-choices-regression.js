// Behavioral coverage for lesson-only choices and migration. No real browser is used.
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert'),crypto=require('crypto');
const {execFileSync}=require('child_process');
const harness=require('./regression/vm-harness');
const target=path.resolve(__dirname,'../../prototype/pilot-flow.html');
const previous=path.join(os.tmpdir(),'korean-word-v5-choices-'+process.pid+'.html');
fs.writeFileSync(previous,execFileSync('git',['show','ba44a879f40132445687c455829179c68da6a8b0:vocabulary-planning/prototype/pilot-flow.html'],{cwd:path.resolve(__dirname,'../../..')}));
const checks=[],KEY='vocabulary-pilot-flow-v2';
const clone=v=>JSON.parse(JSON.stringify(v));
function check(name,fn){try{checks.push({name,status:'PASS',details:fn()||{}});}catch(e){checks.push({name,status:'FAIL',error:e.stack});}}
function prepared(old=false){harness.setTarget(old?previous:target);const b=harness.boot();assert(!b.bootError);b.run("for(const w of WORDS)diagnosticUnknown(w.id);submitDiagnostic();state.screen='plan';render()");b.click('start-session');harness.setTarget(target);return b;}
function restored(s,host=false){harness.setTarget(target);const b=harness.boot(host?{host:{widgetState:s,setWidgetState(){}}}:{saved:{[KEY]:JSON.stringify(s)}});assert(!b.bootError);return b;}
function checkChoices(b,q){const words=new Set(b.json('WORDS.map(w=>titleWord(w.id))'));assert.equal(q.options.length,4);assert.equal(new Set(q.options.map(o=>o.text)).size,4);assert(q.options.every(o=>words.has(o.text)));assert(q.options.some(o=>o.id===q.correct_option_id));}
function currentQuestion(b){return b.json("typeof studyQuestion==='function'?studyQuestion(currentSession().activities[currentSession().currentIndex],currentSession().responses[currentSession().activities[currentSession().currentIndex].id]):activityQuestion(currentSession().activities[currentSession().currentIndex])");}
check('All 90 practice questions use four distinct diagnostic display words, including the answer',()=>{
 const b=prepared(),questions=b.json("ITEMS.filter(q=>q.phase==='practice')");assert.equal(questions.length,90);
 for(const q of questions){checkChoices(b,q);assert.equal(q.options.find(o=>o.id===q.correct_option_id).word_id,q.word_id);}
 const gulji=questions.filter(q=>q.word_id==='W0009');assert.equal(gulji.length,9);assert(gulji.every(q=>q.prompt.includes('(____)의')&&q.options.find(o=>o.id===q.correct_option_id).text==='굴지'));
 return {practiceQuestions:90,optionEntries:360};
});
check('Every word has nine different distractor sets covering all other diagnosis words',()=>{
 const b=prepared();for(const w of b.json('WORDS')){const qs=b.json(`ITEMS.filter(q=>q.phase==='practice'&&q.word_id===${JSON.stringify(w.id)})`),sets=qs.map(q=>q.options.filter(o=>o.id!==q.correct_option_id).map(o=>o.word_id).sort().join(','));assert.equal(new Set(sets).size,9);const others=new Set(qs.flatMap(q=>q.options.filter(o=>o.id!==q.correct_option_id).map(o=>o.word_id)));assert.equal(others.size,9);assert(!others.has(w.id));}
});
check('Assessment and period-review questions remain identical to the prior release',()=>{
 const b=prepared(),current=b.json("ITEMS.filter(q=>q.phase!=='practice')"),before=b.json("DATA.previous_release_items.filter(q=>q.phase!=='practice')");assert.equal(current.length,70);assert.deepStrictEqual(current,before);
});
check('All mixed questions render lesson choices and still score correctly after shuffling and restart',()=>{
 let b=prepared();for(let i=0;i<10;i++){const q=currentQuestion(b);checkChoices(b,q);const selected=b.nodes.filter(n=>n.dataset.action==='option');assert.equal(selected.length,4);assert.equal(new Set(selected.map(n=>n.dataset.option)).size,4);b.choose(q.correct_option_id);b.click('submit-answer');if(i===3)b=restored(b.json('state'));b.click('next');}
 assert.equal(b.run('currentSession().currentIndex'),10);assert.equal(b.run('sessionStats(currentSession()).correct'),10);assert.equal(b.run('state.screen'),'writing');assert.equal(b.nodes.filter(n=>n.dataset.writing).length,10);
});
check('A prior unanswered question replaces foreign choices and clears only its unsubmitted selection',()=>{
 const old=prepared(true),q=currentQuestion(old);old.choose(q.options.find(o=>o.id!==q.correct_option_id).id);old.click('hint');const before=old.json('state'),after=restored(before);checkChoices(after,currentQuestion(after));
 const a=before.sessions.regular.activities[0],r=after.json(`state.sessions.regular.responses[${JSON.stringify(a.id)}]`);assert.equal(r.pendingChoice,null);assert.equal(r.hintShown,true);assert.deepStrictEqual(after.json('state.diagnostic'),before.diagnostic);assert.deepStrictEqual(after.json('state.self'),before.self);assert.deepStrictEqual(after.json('currentSession().quota'),before.sessions.regular.quota);assert.equal(after.run('recoveredRecords.length'),0);
 assert.deepStrictEqual(after.json('currentSession().activities.map(a=>({id:a.id,itemId:a.itemId,wordId:a.wordId,group:a.group,assignedAt:a.assignedAt}))'),before.sessions.regular.activities.map(({id,itemId,wordId,group,assignedAt})=>({id,itemId,wordId,group,assignedAt})));
});
check('All queued prior-release questions update, and fresh choice ordering remains stable on a second reload',()=>{
 const old=prepared(true),b=restored(old.json('state'));for(const a of b.json('currentSession().activities'))checkChoices(b,a.questionSnapshot);const order=b.json('state.choiceOrders'),c=restored(b.json('state'));assert.deepStrictEqual(c.json('state.choiceOrders'),order);assert.equal(c.run('compatibleWidgetState(state)'),true);
});
check('Host-state restoration applies the same lesson-choice migration',()=>{
 const old=prepared(true),b=restored(old.json('state'),true);checkChoices(b,currentQuestion(b));assert.equal(b.run('compatibleWidgetState(state)'),true);
});
check('Submitted first answers and their original question snapshot are preserved',()=>{
 const old=prepared(true),q=currentQuestion(old);old.choose(q.options.find(o=>o.id!==q.correct_option_id).id);old.click('submit-answer');const before=old.json('state'),b=restored(before),a=before.sessions.regular.activities[0];
 assert.deepStrictEqual(b.json('currentSession().activities[0].questionSnapshot'),a.questionSnapshot);assert.deepStrictEqual(b.json(`currentSession().responses[${JSON.stringify(a.id)}]`),before.sessions.regular.responses[a.id]);assert.equal(b.run('sessionStats(currentSession()).correct'),0);
});
check('Retrying an old answered question uses diagnosis choices while retaining its first-answer evidence',()=>{
 const old=prepared(true),q=currentQuestion(old);old.choose(q.options.find(o=>o.id!==q.correct_option_id).id);old.click('submit-answer');const b=restored(old.json('state')),original=b.json('currentSession().activities[0].questionSnapshot'),first=b.json('currentSession().responses[currentSession().activities[0].id].first');b.click('retry');checkChoices(b,currentQuestion(b));const retry=currentQuestion(b);b.choose(retry.correct_option_id);b.click('submit-answer');
 assert.deepStrictEqual(b.json('currentSession().activities[0].questionSnapshot'),original);assert.deepStrictEqual(b.json('currentSession().responses[currentSession().activities[0].id].first'),first);assert.equal(b.run('currentSession().responses[currentSession().activities[0].id].attempts.at(-1).correct'),true);assert.equal(b.run('sessionStats(currentSession()).correct'),0);checkChoices(b,b.json('currentSession().responses[currentSession().activities[0].id].attempts.at(-1).questionSnapshot'));
});
check('Pending retry choice and its new snapshot survive restart without rewriting the original answer',()=>{
 const old=prepared(true),q=currentQuestion(old);old.choose(q.correct_option_id);old.click('submit-answer');const b=restored(old.json('state'));b.click('retry');const retry=currentQuestion(b);b.choose(retry.correct_option_id);const before=b.json('state'),c=restored(before);assert.equal(c.run('compatibleWidgetState(state)'),true);assert.deepStrictEqual(c.json('currentSession().responses'),before.sessions.regular.responses);checkChoices(c,currentQuestion(c));c.click('submit-answer');assert.equal(c.run('currentSession().responses[currentSession().activities[0].id].attempts.length'),2);
});
check('A retry already in progress in the prior release updates its choices without losing first or submitted retries',()=>{
 const old=prepared(true),q=currentQuestion(old);old.choose(q.correct_option_id);old.click('submit-answer');old.click('retry');old.choose(q.options.find(o=>o.id!==q.correct_option_id).id);const before=old.json('state'),b=restored(before),id=before.sessions.regular.activities[0].id;checkChoices(b,currentQuestion(b));assert.equal(b.run(`currentSession().responses[${JSON.stringify(id)}].pendingChoice`),null);assert.deepStrictEqual(b.json(`currentSession().responses[${JSON.stringify(id)}].first`),before.sessions.regular.responses[id].first);assert.deepStrictEqual(b.json(`currentSession().responses[${JSON.stringify(id)}].attempts`),before.sessions.regular.responses[id].attempts);
});
check('Confirmed teacher grades and all ten writing submissions survive the content update unchanged',()=>{
 const old=prepared(true);for(let i=0;i<10;i++){const q=currentQuestion(old);old.choose(q.correct_option_id);old.click('submit-answer');old.click('next');}for(const n of old.nodes.filter(n=>n.dataset.writing)){n.value='배운 단어를 넣어 상황에 맞는 문장을 썼다.';n.trigger('input');}old.click('submit-writing');old.ids['teacher-tab'].click();old.click('teacher-page',{page:'grading'});for(const a of old.json('currentSession().writingActivities')){old.click('writing-judgment',{activity:a.id,judgment:'correct'});old.click('confirm-grade',{activity:a.id});}
 const before=old.json('state'),b=restored(before);assert.deepStrictEqual(b.json('state.sessions'),before.sessions);assert.equal(b.run('allStats().graded'),10);assert.equal(b.run('reportSummary().understanding.known'),10);
});
check('Invalid foreign options in the current content bank cannot enter a new plan',()=>{
 const b=prepared();b.run("state.sessions={};for(const q of ITEMS.filter(q=>q.phase==='practice'&&q.word_id===WORDS[0].id))q.options.find(o=>o.id!==q.correct_option_id).text='목록 밖 단어'");const plan=b.json("planActivities(Object.fromEntries(WORDS.map((w,i)=>[w.id,i?'known':'unknown'])),'scope-test')");assert(plan.shortage.includes('모름'));assert(plan.activities.every(a=>a.wordId!=='W0001'));for(const a of plan.activities)checkChoices(b,a.questionSnapshot);
});
fs.unlinkSync(previous);
const result={method:'Node VM with mocked DOM/localStorage/host; no browser, mobile or print verification',html_sha256:crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex'),count:checks.length,passed:checks.filter(c=>c.status==='PASS').length,failed:checks.filter(c=>c.status==='FAIL').length,checks};
fs.writeFileSync(path.join(__dirname,'diagnostic-choices-regression-results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));if(result.failed)process.exitCode=1;
