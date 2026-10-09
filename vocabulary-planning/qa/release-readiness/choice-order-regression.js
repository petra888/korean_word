// Focused release regression: Node VM + mocked DOM only, not browser validation.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const harness=require('./regression/vm-harness.js');
const target=path.resolve(process.argv[2]||path.join(__dirname,'../../prototype/pilot-flow.html'));
const output=path.resolve(process.argv[3]||path.join(__dirname,'choice-order-regression-results.json'));
harness.setTarget(target);
const {boot}=harness,checks=[];
function check(id,name,fn){try{checks.push({id,name,status:'PASS',details:fn()||{}});}catch(e){checks.push({id,name,status:'FAIL',error:e.message});}}
function prepared(){const b=boot();assert(!b.bootError);b.run("for(const w of WORDS)diagnosticUnknown(w.id);submitDiagnostic();state.screen='plan';render()");b.click('start-session');return b;}
function clone(o){return JSON.parse(JSON.stringify(o));}
function loaded(snapshot){return boot({saved:{'vocabulary-pilot-flow-v2':JSON.stringify(snapshot)}});}
function visibleOptions(b){return b.nodes.filter(n=>n.dataset.action==='option').map(n=>n.dataset.option);}
const fixture=prepared(),base=fixture.json('state'),q=fixture.json('activityQuestion(currentSession().activities[0])'),ids=q.options.map(o=>o.id);
const invalidOrders=[
 ['duplicates-wrong',Array(4).fill(ids.find(id=>id!==q.correct_option_id))],
 ['duplicates-correct',Array(4).fill(q.correct_option_id)],
 ['three-unique',[ids[0],ids[1],ids[2],ids[2]]],
 ['missing-option',ids.slice(0,3)],
 ['extra-option',[...ids,ids[0]]],
 ['foreign-option',[...ids.slice(0,3),'foreign-option']],
 ['invalid-option',[...ids.slice(0,3),'" onclick="bad']],
 ['non-array',{0:ids[0],1:ids[1],2:ids[2],3:ids[3]}]
];
for(const [name,order]of invalidOrders)check('CO-'+name,'Damaged '+name+' order is archived and repaired with all four distinct options',()=>{
 const snapshot=clone(base);snapshot.choiceOrders[q.id]=order;const raw=JSON.stringify(snapshot),b=loaded(snapshot);assert(!b.bootError);
 const shown=visibleOptions(b);assert.equal(shown.length,4);assert.equal(new Set(shown).size,4);assert.deepStrictEqual([...shown].sort(),[...ids].sort());assert(shown.includes(q.correct_option_id));
 assert(b.json('recoveredRecords').some(r=>r.raw===raw&&r.reason.includes('choiceOrders')));assert.equal(b.run('compatibleWidgetState(state)'),true);
 assert.deepStrictEqual(b.json('state.diagnostic'),base.diagnostic);assert.deepStrictEqual(b.json('currentSession().responses'),base.sessions.regular.responses);
 return {distinctOptions:4,correctOptionVisible:true,exactOriginalArchived:true};
});
check('CO-container','Malformed choiceOrders container is archived and repaired',()=>{const snapshot=clone(base);snapshot.choiceOrders=null;const b=loaded(snapshot);assert(!b.bootError);assert.equal(new Set(visibleOptions(b)).size,4);assert(b.json('recoveredRecords').some(r=>r.reason.includes('choiceOrders')));});
check('CO-valid','A valid stored permutation is retained exactly without quarantine',()=>{const snapshot=clone(base),order=[...ids].reverse();snapshot.choiceOrders[q.id]=order;const b=loaded(snapshot);assert(!b.bootError);assert.deepStrictEqual(visibleOptions(b),order);assert.deepStrictEqual(b.json(`state.choiceOrders[${JSON.stringify(q.id)}]`),order);assert.equal(b.run('recoveredRecords.length'),0);});
check('CO-runtime','Runtime damaged order is repaired and persisted before presentation',()=>{const b=prepared();b.run("{const q=activityQuestion(currentSession().activities[0]);state.choiceOrders[q.id]=Array(4).fill(q.options[0].id);render()}");assert.equal(new Set(visibleOptions(b)).size,4);const stored=JSON.parse(b.saved['vocabulary-pilot-flow-v2']),active=stored.sessions.regular.activities[0];assert.equal(new Set(stored.choiceOrders[active.questionSnapshot.id]).size,4);});
check('CO-preserve','Repair preserves first answer, retries, pending choice, writing drafts and navigation',()=>{
 const b=prepared();b.run("{const s=currentSession(),a=s.activities[0],q=activityQuestion(a),first={choice:q.options[0].id,correct:q.options[0].id===q.correct_option_id,hinted:true,submittedAt:now()};s.responses[a.id]={first,attempts:[first],pendingChoice:q.correct_option_id,retryEditing:true,hintShown:true};state.screen='writing';render();for(const wr of Object.values(s.writings)){wr.gradeDraft=null;wr.gradeDrafts={};wr.selectedVersionId=null;}s.writings[s.writingActivities[0].id].draftText='복구해도 남아야 할 학생 작문';remember();state.screen='study';s.currentIndex=0;state.choiceOrders[q.id]=Array(4).fill(q.options[0].id);persist()}");
 const snapshot=b.json('state'),c=loaded(snapshot);assert(!c.bootError);assert.deepStrictEqual(c.json('state.sessions'),snapshot.sessions);assert.deepStrictEqual(c.json('state.navigation'),snapshot.navigation);assert.deepStrictEqual(c.json('state.diagnostic'),snapshot.diagnostic);assert.equal(new Set(visibleOptions(c)).size,4);assert(c.ids.app.innerHTML.includes('다시 확인하기'));
 c.loginAs('teacher');c.ids['export-record'].click();const record=JSON.parse(c.ids['export-json'].value);assert(record.recoveredRecords.some(r=>r.raw===JSON.stringify(snapshot)));
 return {firstAndRetryPreserved:true,writingDraftPreserved:true,navigationPreserved:true,recoveryExportable:true};
});
check('CO-legacy-snapshot','Stored historical activity snapshot option IDs take precedence over new canonical IDs',()=>{
 const snapshot=clone(base),a=snapshot.sessions.regular.activities[0],old=clone(a.questionSnapshot),newIds=old.options.map((o,i)=>'legacy-'+i);old.options.forEach((o,i)=>o.id=newIds[i]);old.correct_option_id=newIds[2];old.prompt='과거 배정에서 저장한 문제';a.questionSnapshot=old;const order=[...newIds].reverse();snapshot.choiceOrders[old.id]=order;
 const b=loaded(snapshot);assert(!b.bootError);assert.deepStrictEqual(visibleOptions(b),order);assert.equal(b.run('recoveredRecords.length'),0);assert(b.ids.app.innerHTML.includes(old.prompt));
});
check('CO-legacy-unsnapshotted','Legacy item bank option IDs remain valid when old activity has no snapshot',()=>{
 const b=prepared();b.run("{DATA.previous_items=JSON.parse(JSON.stringify(ITEMS));delete currentSession().contentVersion;const a=currentSession().activities[0],old=DATA.previous_items.find(q=>q.id===a.itemId);old.options.forEach((o,i)=>o.id='legacy-'+i);old.correct_option_id='legacy-2';delete a.questionSnapshot;state.choiceOrders[old.id]=['legacy-3','legacy-2','legacy-1','legacy-0'];state=normalize(state);render()}");
 assert.deepStrictEqual(visibleOptions(b),['legacy-3','legacy-2','legacy-1','legacy-0']);assert.equal(b.run('compatibleWidgetState(state)'),true);
});
check('CO-review-snapshot','Period review snapshot ordering is preserved and damaged ordering is recoverable',()=>{
 const b=prepared();b.run("{const s=currentSession();for(const a of s.activities){const q=activityQuestion(a),first={choice:q.correct_option_id,correct:true,hinted:false,submittedAt:now()};s.responses[a.id]={first,attempts:[first]};}state.screen='writing';render();for(const a of s.writingActivities)s.writings[a.id].draftText='복습 전 작문';submitAllWriting(s);state.reviews.weekly=makeReview('weekly');state.activeReview='weekly';state.screen='review-question';const q=reviewQuestion(state.reviews.weekly,WORDS[0].id);q.options.forEach((o,i)=>o.id='review-old-'+i);q.correct_option_id='review-old-2';state.choiceOrders[q.id]=['review-old-3','review-old-2','review-old-1','review-old-0'];persist();render()}");
 const saved=b.json('state'),c=loaded(saved);assert(!c.bootError);assert.deepStrictEqual(visibleOptions(c),['review-old-3','review-old-2','review-old-1','review-old-0']);assert.equal(c.run('recoveredRecords.length'),0);
 const damaged=clone(saved),reviewQ=Object.values(damaged.reviews.weekly.questionSnapshots)[0];damaged.choiceOrders[reviewQ.id]=Array(4).fill('review-old-0');const d=loaded(damaged);assert(!d.bootError);assert.equal(new Set(visibleOptions(d)).size,4);assert(visibleOptions(d).includes('review-old-2'));assert(d.run('recoveredRecords.length')>0);
});
check('CO-full-flow','Normal study, all reviews, ten teacher grades, report print preparation, export and restore remain usable',()=>{
 const b=prepared();for(let i=0;i<10;i++){const q=b.json('activityQuestion(currentSession().activities[currentSession().currentIndex])');b.choose(q.correct_option_id);b.click('submit-answer');b.click('next');}
 for(const n of b.nodes.filter(n=>n.dataset.writing)){n.value='나는 단어의 뜻을 확인하며 문장을 썼다.';n.trigger('input');}b.click('submit-writing');b.click('reviews');
 for(const phase of ['weekly','monthly','quarterly']){b.click('open-review',{phase});for(let i=0;i<10;i++){const q=b.json('reviewQuestion(state.reviews[state.activeReview],state.reviews[state.activeReview].targetWordIds[state.reviews[state.activeReview].currentIndex])');b.choose(q.correct_option_id);b.click('submit-answer');b.click('next');if(b.run('state.screen')==='review-break')b.click('continue-review');}assert.equal(b.run(`reviewStats(state.reviews.${phase}).done`),10);b.click('reviews');}
 b.loginAs('teacher');b.click('teacher-page',{page:'grading'});for(const a of b.json('state.sessions.regular.writingActivities')){b.click('writing-judgment',{activity:a.id,judgment:'correct'});b.click('confirm-grade',{activity:a.id});}
 b.click('teacher-page',{page:'report'});const message=b.doc.querySelector('[data-report-field="parentMessage"]');message.value='집에서도 예문을 읽어 보세요.';message.trigger('input');b.click('confirm-report');b.click('print-report');b.ids['export-record'].click();const record=JSON.parse(b.ids['export-json'].value),c=loaded(record.state);assert(!c.bootError);assert.equal(b.printCalls,1);assert.equal(c.run('allStats().graded'),10);assert.equal(c.run('reportSummary().understanding.known'),10);
 return {objectiveResponses:10,writingSubmissions:10,periodReviewResponses:30,teacherGrades:10,printPrepared:true,exportReloadVerified:true};
});
const result={method:'Node VM with mocked DOM/localStorage/host; no real browser, mobile or browser print verification',source_sha256:crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex'),count:checks.length,passed:checks.filter(c=>c.status==='PASS').length,failed:checks.filter(c=>c.status==='FAIL').length,checks};fs.writeFileSync(output,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({source_sha256:result.source_sha256,count:result.count,passed:result.passed,failed:result.failed,failedChecks:checks.filter(c=>c.status==='FAIL')},null,2));if(result.failed)process.exitCode=1;
