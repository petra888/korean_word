// Node VM + mocked DOM: behavioral checks only, not browser or server verification.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('/tmp/vocabulary-full-qa-0d75986-n5h3m0i4/vocabulary-planning/prototype/pilot-flow.html','utf8');
const payload=html.match(/<script type="application\/json" id="curriculum-data">([\s\S]+?)<\/script>/)[1],source=html.match(/<script>\n([\s\S]+?)<\/script>/)[1];
const decode=s=>String(s).replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&');
const ids={},saved={},windowListeners={};let nodes=[],hostWrites=0;
class El{
  constructor(id='',attrs='',text=''){this.id=id;this.textContent=text;this.value='';this.checked=false;this.tagName='BUTTON';this.dataset={};this.listeners={};this.attrs={};this.classList={toggle(){},add(){},remove(){}};for(const m of attrs.matchAll(/([\w-]+)="([^"]*)"/g)){this.attrs[m[1]]=decode(m[2]);if(m[1].startsWith('data-'))this.dataset[m[1].slice(5).replace(/-([a-z])/g,(_,x)=>x.toUpperCase())]=decode(m[2]);}this.disabled=/\bdisabled\b/.test(attrs);this.checked=/\bchecked\b/.test(attrs);this.value=this.attrs.value||'';}
  get innerHTML(){return this._html||'';}
  set innerHTML(v){this._html=v;nodes=this.id==='app'?[]:nodes.filter(n=>n.owner!==this.id);for(const m of v.matchAll(/<(button|textarea|select)\b([^>]*)>([\s\S]*?)<\/\1>|<(input)\b([^>]*)>/g)){const tag=m[1]||m[4],el=new El('',m[2]||m[5],decode(m[3]||''));el.tagName=tag.toUpperCase();el.id=el.attrs.id||'';el.owner=this.id;if(tag==='textarea')el.value=decode(m[3]||'');if(tag==='select'){const options=[...(m[3]||'').matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/g)],op=options.find(o=>/\bselected\b/.test(o[1]))||options[0];if(op)el.value=decode(op[1].match(/value="([^"]*)"/)?.[1]??op[2]);}nodes.push(el);}}
  addEventListener(name,fn){this.listeners[name]=fn;}getAttribute(n){return this.attrs[n];}setAttribute(n,v){this.attrs[n]=v;}focus(){}select(){}scrollIntoView(){}remove(){}trigger(name){this.listeners[name]?.({target:this,currentTarget:this,preventDefault(){}});}click(){if(!this.disabled)this.trigger('click');}
}
for(const m of html.matchAll(/\bid="([^"]+)"/g))ids[m[1]]??=new El(m[1]);ids['curriculum-data'].textContent=payload;
function query(sel){if(sel.startsWith('#'))return [doc.getElementById(sel.slice(1))];const ms=[...sel.matchAll(/\[([\w-]+)(?:="([^"]*)")?\]/g)];return ms.length?nodes.filter(n=>ms.every(m=>Object.hasOwn(n.attrs,m[1])&&(m[2]===undefined||n.attrs[m[1]]===m[2]))):[];}
const doc={getElementById(id){return nodes.find(n=>n.id===id)||(ids[id]??=new El(id));},querySelectorAll:query,querySelector(s){return query(s)[0]||null;},documentElement:{},body:{appendChild(){}},createElement(){return new El();}};
const ctx=vm.createContext({document:doc,window:{scrollTo(){},confirm(){return true},print(){},addEventListener(n,cb){windowListeners[n]=cb},openai:null},localStorage:{getItem(k){return saved[k]||null},setItem(k,v){saved[k]=v},removeItem(k){delete saved[k]}},console,Date,Intl,Math,Blob,URL,setTimeout});vm.runInContext(source,ctx);
const run=c=>vm.runInContext(c,ctx),json=c=>JSON.parse(run(`JSON.stringify(${c})`)),action=(a,f={})=>nodes.find(n=>n.dataset.action===a&&Object.entries(f).every(([k,v])=>n.dataset[k]===v));
function click(a,f){const n=action(a,f);assert(n,'missing '+a);assert(!n.disabled,'disabled '+a);n.click();}const choose=option=>click('option',{option}),checks=[];
function check(name,fn){fn();checks.push({name,status:'PASS'});}
const wordIds=json('WORDS.map(w=>w.id)'),canonical=Array.from({length:10},(_,i)=>'W'+String(i+1).padStart(4,'0'));
if(process.argv.includes('--allow-pending-canonical')&&JSON.stringify(wordIds)!==JSON.stringify(canonical))checks.push({name:'PDF first ten canonical order',status:'PENDING — final content embed'});else check('PDF first ten canonical order',()=>assert.deepStrictEqual(wordIds,canonical));
check('Matching bank permutation and order persist independently of definition order',()=>{assert.equal(run('state.version'),2);assert.equal(run('selectedCount()'),0);assert(action('start-plan').disabled);const order=json('state.diagnostic.wordOrder');assert.deepStrictEqual([...order].sort(),[...wordIds].sort());assert.deepStrictEqual([...ids.app.innerHTML.matchAll(/data-drop-row="([^"]+)"/g)].map(m=>m[1]),wordIds);run('render()');assert.deepStrictEqual(json('state.diagnostic.wordOrder'),order);});
check('Unknown auto answer cannot count as correct; exposure snapshot prevents promotions',()=>{for(let i=0;i<5;i++)assert(run(`diagnosticAssign('${wordIds[i]}','${wordIds[i]}')`));run(`diagnosticAssign('${wordIds[5]}','${wordIds[6]}');diagnosticAssign('${wordIds[6]}','${wordIds[5]}')`);assert(run(`diagnosticUnknown('${wordIds[9]}')`));const snap=json('state.diagnostic.firstSnapshot');assert.equal(snap[wordIds[0]],wordIds[0]);assert.equal(snap[wordIds[5]],wordIds[6]);assert.equal(run(`state.diagnostic.assignments['${wordIds[9]}']`),wordIds[9]);assert.equal(run(`diagnosticResult('${wordIds[9]}').correct`),null);for(let i=5;i<9;i++)run(`diagnosticAssign('${wordIds[i]}','${wordIds[i]}')`);assert.equal(run(`diagnosticAssign('${wordIds[9]}','${wordIds[9]}')`),false);assert.deepStrictEqual(json('state.diagnostic.firstSnapshot'),snap);assert(run('submitDiagnostic()'));for(let i=0;i<5;i++)assert.equal(run(`state.self['${wordIds[i]}']`),'known');for(let i=5;i<9;i++)assert.equal(run(`state.self['${wordIds[i]}']`),'uncertain');assert.equal(run(`state.self['${wordIds[9]}']`),'unknown');assert.equal(run('Object.values(state.diagnostic.results).filter(r=>r.correct===true&&!r.exposed).length'),5);const locked=json('state.self');run(`diagnosticAssign('${wordIds[0]}','${wordIds[1]}');submitDiagnostic();setScreen('plan')`);ids.back.click();assert.equal(run('state.screen'),'self');assert.deepStrictEqual(json('state.self'),locked);assert.deepStrictEqual(json('state.diagnostic.firstSnapshot'),snap);});
check('Objective ten activities use 6/3/1; all ten writing targets are separately counted',()=>{run("setScreen('plan')");click('start-session');assert.deepStrictEqual(json('currentSession().quota'),{unknown:6,uncertain:3,known:1});assert.equal(run('currentSession().activities.length'),10);assert.deepStrictEqual(json('currentSession().writingActivities.map(a=>a.wordId)'),wordIds);assert.equal(run('new Set(currentSession().writingActivities.map(a=>a.wordId)).size'),10);assert.equal(run('sessionStats(currentSession()).objectivePlanned'),10);assert.equal(run('sessionStats(currentSession()).writingPlanned'),10);assert.equal(run('sessionStats(currentSession()).planned'),20);});
check('Unsubmitted choice and shuffled options survive Back',()=>{const correct=run('item(currentSession().activities[0].itemId).correct_option_id');choose(correct);const order=json('state.choiceOrders');ids.back.click();assert.equal(run('state.screen'),'plan');click('start-session');assert.equal(run('currentSession().responses[currentSession().activities[0].id].pendingChoice'),correct);assert(action('option',{option:correct}).attrs.class.includes('selected'));assert.deepStrictEqual(json('state.choiceOrders'),order);assert.equal(run('sessionStats(currentSession()).objective'),0);});
check('Four choices per mixed question with generic heading and no target classification',()=>{for(const a of json('currentSession().activities')){const q=json(`item('${a.itemId}')`);assert.equal(q.options.length,4);assert.equal(new Set(q.options.map(o=>o.id)).size,4);assert(q.options.some(o=>o.id===q.correct_option_id));}assert.deepStrictEqual([...ids.app.innerHTML.matchAll(/<h[12][^>]*>([\s\S]*?)<\/h[12]>/g)].map(m=>m[1]),['빈칸에 알맞은 말을 고르세요.']);assert(!ids.app.innerHTML.includes('배정 분류'));});
check('First responses, hints, retries and revisits retain original counts',()=>{for(let i=0;i<10;i++){const q=json('item(currentSession().activities[currentSession().currentIndex].itemId)');if(i===2)click('hint');choose(q.correct_option_id);click('submit-answer');if(i===2){const first=json('currentSession().responses[currentSession().activities[currentSession().currentIndex].id].first');click('retry');choose(q.options.find(o=>o.id!==q.correct_option_id).id);click('submit-answer');assert.deepStrictEqual(json('currentSession().responses[currentSession().activities[currentSession().currentIndex].id].first'),first);}click('next');if(i===0){const count=run('sessionStats(currentSession()).objective');ids.back.click();assert.equal(run('currentSession().currentIndex'),0);assert.equal(action('submit-answer'),undefined);click('next');assert.equal(run('sessionStats(currentSession()).objective'),count);}}assert.equal(run('state.screen'),'writing');const s=json('sessionStats(state.sessions.regular)');assert.equal(s.objective,10);assert.equal(s.correct,10);assert.equal(s.independent,9);assert.equal(s.hints,1);assert.equal(s.writing,0);assert.deepStrictEqual(s.groups,{unknown:6,uncertain:3,known:1});assert.equal(run('state.sessions.regular.responses[state.sessions.regular.activities[2].id].attempts.length'),2);});
check('All ten drafts required; Back preserves draft; repeated submission adds no activity',()=>{const el=doc.querySelectorAll('[data-writing]')[0];el.value='첫 단어의 작성 중 문장';el.trigger('input');ids.back.click();assert.equal(run('state.screen'),'study');click('next');assert.equal(doc.querySelectorAll('[data-writing]')[0].value,'첫 단어의 작성 중 문장');assert.equal(run('submitAllWriting(currentSession())'),false);assert.equal(run('sessionStats(currentSession()).writing'),0);for(const el of doc.querySelectorAll('[data-writing]')){el.value='나는 '+run(`titleWord(currentSession().writingActivities.find(a=>a.id==='${el.dataset.writing}').wordId)` )+'의 뜻을 드러내는 문장을 썼다.';el.trigger('input');}click('submit-writing');assert.equal(run('state.screen'),'finish');const s=json('sessionStats(state.sessions.regular)');assert.equal(s.done,20);assert.equal(s.unique,10);assert.equal(s.writing,10);assert.equal(s.graded,0);run('submitAllWriting(state.sessions.regular)');assert.equal(run('state.sessions.regular.writingActivities.every(a=>state.sessions.regular.writings[a.id].versions.length===1)'),true);assert(run('canReview()'));});
const initialPlan=json('state.sessions.regular.activities'),initialSelf=json('state.self');
function gradeWord(index,group){const a=json(`state.sessions.regular.writingActivities[${index}]`),judgment=group==='unknown'?'incorrect':group==='known'?'correct':'uncertain';run(`{const wr=state.sessions.regular.writings['${a.id}'];selectGradeVersion(wr,wr.versions.at(-1).id);chooseWritingJudgment('regular','${a.id}','${judgment}');setUnderstandingOverride('regular','${a.id}','${group}');}`);assert(run(`confirmGrade('regular','${a.id}')`));return a;}
check('Teacher confirmation requires one judgment and exact version; reasons are optional and latest classification wins',()=>{const a=json('state.sessions.regular.writingActivities[0]');run(`{const wr=state.sessions.regular.writings['${a.id}'];selectGradeVersion(wr,wr.versions[0].id);}`);assert.equal(run(`confirmGrade('regular','${a.id}')`),false);gradeWord(0,'known');assert.equal(run(`effectiveGroups()['${wordIds[0]}']`),'known');const g=json(`latestGrade(state.sessions.regular.writings['${a.id}'])`);for(const field of ['meaning','context','sentence','reason'])assert(!Object.hasOwn(g,field));assert.equal(g.comment,'');assert.equal(g.override_reason,'');gradeWord(0,'uncertain');assert.equal(run(`effectiveGroups()['${wordIds[0]}']`),'uncertain');for(let i=0;i<10;i++)gradeWord(i,i<5?'unknown':i<8?'uncertain':'known');assert.deepStrictEqual(json('groupsCount(effectiveGroups())'),{unknown:5,uncertain:3,known:2});assert.deepStrictEqual(json('state.sessions.regular.activities'),initialPlan);assert.deepStrictEqual(json('state.self'),initialSelf);});
check('Unreviewed revision never promotes group; grade identifies exact text version',()=>{run("state.role='student';state.activeSession='regular';setScreen('writing')");const a=json('state.sessions.regular.writingActivities[0]'),g=json(`latestGrade(state.sessions.regular.writings['${a.id}'])`),el=doc.querySelectorAll('[data-revision-input]').find(e=>e.dataset.revisionInput===a.id);assert(el);el.value='피드백을 반영한 수정 문장';el.trigger('input');click('submit-revision',{activity:a.id});assert.equal(run(`effectiveGroups()['${a.wordId}']`),'unknown');assert.deepStrictEqual(json(`latestGrade(state.sessions.regular.writings['${a.id}'])`),g);assert.notEqual(run(`state.sessions.regular.writings['${a.id}'].versions.at(-1).id`),g.targetVersionId);assert.equal(run('sessionStats(state.sessions.regular).done'),20);assert(run('parentReport()').includes('최신 수정본 교사 확인 대기'));run(`state.sessions.regular.writings['${a.id}'].gradeDraft={...${JSON.stringify(g)},targetVersionId:'missing-version'}`);assert.equal(run(`confirmGrade('regular','${a.id}')`),false);gradeWord(0,'unknown',0);assert.equal(run(`latestGrade(state.sessions.regular.writings['${a.id}']).targetVersionId`),run(`state.sessions.regular.writings['${a.id}'].versions.at(-1).id`));});
check('Period coverage includes all ten and checkpoints before fresh weighted remedial plan',()=>{run("state.role='student';state.activeSession='regular';setScreen('reviews')");click('open-review',{phase:'weekly'});assert.deepStrictEqual(json('state.reviews.weekly.targetWordIds'),wordIds);assert.equal(action('review-remedial'),undefined);for(let i=0;i<10;i++){const q=json('ITEMS.find(i=>i.phase===state.activeReview&&i.word_id===state.reviews[state.activeReview].targetWordIds[state.reviews[state.activeReview].currentIndex])');assert.equal(q.options.length,4);if(i===1)click('hint');choose(i===8?q.options.find(o=>o.id!==q.correct_option_id).id:q.correct_option_id);click('submit-answer');click('next');if(action('continue-review')){assert.equal(run('reviewStats(state.reviews.weekly).done'),5);click('reviews');click('open-review',{phase:'weekly'});assert.equal(run('reviewStats(state.reviews.weekly).done'),5);}}const s=json('reviewStats(state.reviews.weekly)');assert.equal(s.done,10);assert.equal(s.total,10);assert.equal(s.correct,9);assert.equal(s.independent,8);assert.deepStrictEqual(json('state.reviews.weekly.targetWordIds'),wordIds);assert.equal(run('reviewStats(state.reviews.monthly).done'),0);assert.equal(run('reviewStats(state.reviews.quarterly).done'),0);const g=json(`latestWordGrade('${wordIds[8]}')`);run(`state.reviews.weekly.responses['${wordIds[8]}'].first.submittedAt='2999-01-01T00:00:00.000Z'`);assert.equal(run(`resolveUnderstanding('${wordIds[8]}').group`),g.understanding_state);assert(run(`resolveUnderstanding('${wordIds[8]}').recheckRequired`));click('review-remedial');click('start-session');assert.deepStrictEqual(json('currentSession().quota'),{unknown:6,uncertain:3,known:1});assert.equal(run('currentSession().activities.length'),10);assert.equal(run('currentSession().writingActivities.length'),0);const old=new Set(initialPlan.map(a=>a.itemId));assert(json('currentSession().activities.map(a=>a.itemId)').every(id=>!old.has(id)));const running=json('currentSession().activities');gradeWord(0,'known');assert.equal(run(`effectiveGroups()['${wordIds[0]}']`),'known');assert.deepStrictEqual(json('currentSession().activities'),running);assert.deepStrictEqual(json('state.sessions.regular.activities'),initialPlan);});
check('Confirmed parent text is escaped; internal memo and unconfirmed edits excluded',()=>{ids['teacher-tab'].click();run("teacherPage('report')");for(const [key,text] of [['parentMessage','<img src=x onerror=alert(1)> 부모 메시지'],['internalMemo','비공개 내부 메모']]){const el=doc.querySelectorAll('[data-report-field]').find(e=>e.dataset.reportField===key);assert(el);el.value=text;el.trigger('input');}assert(!run('parentReport()').includes('부모 메시지'));click('confirm-report');const report=run('parentReport()');assert(report.includes('&lt;img src=x onerror=alert(1)&gt; 부모 메시지'));assert(!report.includes('<img src=x'));assert(!report.includes('비공개 내부 메모'));const el=doc.querySelectorAll('[data-report-field]').find(e=>e.dataset.reportField==='parentMessage');el.value='확인하지 않은 수정 메시지';el.trigger('input');assert(!run('parentReport()').includes('확인하지 않은 수정 메시지'));});
check('Empty groups normalize without altering diagnostic classification',()=>{assert.equal(run("allocate(Object.fromEntries(WORDS.map(w=>[w.id,'known']))).known"),10);assert.deepStrictEqual(json("allocate(Object.fromEntries(WORDS.map((w,i)=>[w.id,i<8?'uncertain':'known'])))"),{unknown:0,uncertain:8,known:2});assert.deepStrictEqual(json('state.self'),initialSelf);});
check('Host v2 restoration preserves pending choice and disclosure; rejects v1 with no feedback loop',()=>{assert.equal(typeof windowListeners['openai:set_globals'],'function');const original=run('JSON.stringify(state)');for(const bad of [{version:1,self:{},sessions:{},reviews:{},diagnostic:{}},{version:9},{version:2,self:[],sessions:{},reviews:{},diagnostic:{}}]){windowListeners['openai:set_globals']({detail:{globals:{widgetState:bad}}});assert.equal(run('JSON.stringify(state)'),original);}ctx.window.openai={setWidgetState(){hostWrites++}};const incoming=JSON.parse(original);incoming.role='teacher';incoming.teacher={parentMessage:'호스트 새 메시지',ratings:{'뜻 이해':'안정'}};windowListeners['openai:set_globals']({detail:{globals:{widgetState:incoming}}});assert.equal(run('state.teacher.parentMessage'),'호스트 새 메시지');assert.equal(run("state.teacher.ratings['학습 태도']"),'미평가');assert.equal(hostWrites,0);const same=run('JSON.stringify(state)');windowListeners['openai:set_globals']({detail:{widgetState:JSON.parse(same)}});assert.equal(run('JSON.stringify(state)'),same);const fallback=JSON.parse(same);fallback.role='student';fallback.screen='study';fallback.activeSession='regular';fallback.sessions.regular.currentIndex=0;fallback.choiceOrders={};const a=fallback.sessions.regular.activities[0],q=json(`item('${a.itemId}')`);fallback.sessions.regular.responses[a.id]={pendingChoice:q.correct_option_id,hintShown:false,attempts:[]};windowListeners['openai:set_globals']({detail:{widgetState:fallback}});assert.equal(run('state.version'),2);assert.equal(run('currentSession().responses[currentSession().activities[0].id].pendingChoice'),q.correct_option_id);assert(action('option',{option:q.correct_option_id}).attrs.class.includes('selected'));assert(Object.keys(json('state.choiceOrders')).length>0);assert.equal(Object.keys(fallback.choiceOrders).length,0);assert.equal(hostWrites,0);assert.deepStrictEqual(json('state.diagnostic.firstSnapshot'),JSON.parse(original).diagnostic.firstSnapshot);});
check('Four individual drafts allow early teacher review while all-ten review gate stays closed',()=>{
  const baseline=run('JSON.stringify(state)');
  try{
    run("state.role='student';state.activeSession='regular';state.screen='writing';state.navigation.student=[];state.sessions.regular.writings={};state.sessions.regular.allWritingSubmittedAt=null;for(const a of state.sessions.regular.activities){const q=item(a.itemId),first={choice:q.correct_option_id,correct:true,hinted:false,submittedAt:now()};state.sessions.regular.responses[a.id]={first,attempts:[first],hintShown:false};}render()");
    const activities=json('state.sessions.regular.writingActivities');
    // Keep drafts for all ten, then submit only the first four individual cards.
    for(const el of doc.querySelectorAll('[data-writing]')){el.value='부분 제출 확인 문장 '+el.dataset.writing;el.trigger('input');}
    for(let i=0;i<4;i++)click('submit-draft',{activity:activities[i].id});
    assert.equal(run('sessionStats(state.sessions.regular).writing'),4);
    assert.equal(run('sessionStats(state.sessions.regular).done'),14);
    assert.equal(run('allDraftsSubmitted(state.sessions.regular)'),false);
    assert.equal(run('canReview()'),false);
    for(let i=4;i<10;i++)assert.equal(run(`state.sessions.regular.writings['${activities[i].id}'].draftText`),'부분 제출 확인 문장 '+activities[i].id);
    // Only submitted versions are teacher-evaluable before the remaining six.
    const first=activities[0];
    gradeWord(0,'uncertain',1);
    assert.equal(run('sessionStats(state.sessions.regular).graded'),1);
    assert.equal(run(`latestGrade(state.sessions.regular.writings['${first.id}']).targetVersionId`),first.id+'-v1');
    assert.equal(run('canReview()'),false);
    run(`submitOneWriting(state.sessions.regular,'${first.id}')`);
    assert.equal(run(`state.sessions.regular.writings['${first.id}'].versions.length`),1);
    assert.equal(run('sessionStats(state.sessions.regular).writing'),4);
    assert(run('submitAllWriting(state.sessions.regular)'));
    assert.equal(run('sessionStats(state.sessions.regular).writing'),10);
    assert.equal(run('sessionStats(state.sessions.regular).done'),20);
    assert.equal(run('sessionStats(state.sessions.regular).graded'),1);
    assert(run('allDraftsSubmitted(state.sessions.regular)'));
    assert(run('canReview()'));
    assert(run('state.sessions.regular.writingActivities.every(a=>state.sessions.regular.writings[a.id].versions.length===1)'));
  }finally{run('state='+baseline+';render()');}
});
// Isolated fixtures exercise the changed teacher rules without disturbing the
// integrated student flow or silently rewriting its frozen activity plan.
function withReviewFixture(firsts,fn){
  const baseline=run('JSON.stringify(state)');
  try{
    run(`{state=fresh();state.self=Object.fromEntries(WORDS.map(w=>[w.id,'unknown']));const specs=${JSON.stringify(firsts)},wid=WORDS[0].id,activities=specs.map((x,i)=>({id:'fixture-Q'+(i+1),type:'context',wordId:wid,meaningId:WORDS[0].meaning_id,itemId:'fixture-item'+(i+1),group:'unknown'})),responses={};activities.forEach((a,i)=>{const x=specs[i];responses[a.id]=x===null?{pendingChoice:'a',hintShown:false,attempts:[]}:{first:{choice:'a',correct:x.correct,hinted:!!x.hinted,submittedAt:'2026-10-01T00:00:00.000Z'},attempts:[{correct:x.correct},...(x.retryCorrect?[{correct:true}]:[])]};});const wa={id:'fixture-W1',type:'writing',wordId:wid,meaningId:WORDS[0].meaning_id};state.sessions.fixture={id:'fixture',activities,responses,writingActivities:[wa],writings:{'fixture-W1':{draftText:'학생의 원래 문장',versions:[{id:'fixture-W1-v1',number:1,kind:'draft',text:'학생의 원래 문장',submittedAt:'2026-10-01T00:00:00.000Z'}],grades:[],revisionDraft:''}},currentIndex:0,quota:{unknown:activities.length,uncertain:0,known:0}};state.activeSession='fixture';state.role='teacher';state.teacherScreen='grading';render();}`);
    fn();
  }finally{run('state='+baseline+';render()');}
}
const fixtureGrade=()=>json("latestGrade(state.sessions.fixture.writings['fixture-W1'])");
check('Teacher UI exposes three single-choice buttons and removes every score control',()=>{
  withReviewFixture([{correct:true}],()=>{
    const buttons=doc.querySelectorAll('[data-judgment]');
    assert.deepStrictEqual(buttons.map(el=>el.dataset.judgment),['correct','incorrect','uncertain']);
    assert(buttons.every(el=>el.tagName==='BUTTON'));
    for(const key of ['meaning','context','sentence','reason'])assert.equal(doc.querySelectorAll('[data-grade-key="'+key+'"]').length,0);
    assert.equal(action('confirm-grade',{activity:'fixture-W1'}).disabled,true);
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});
    assert.equal(action('writing-judgment',{activity:'fixture-W1',judgment:'correct'}).attrs['aria-pressed'],'true');
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.writing_judgment"),'correct');
    assert.equal(doc.querySelectorAll('[data-judgment]').filter(el=>el.attrs['aria-pressed']==='true').length,1);
    click('writing-judgment',{activity:'fixture-W1',judgment:'incorrect'});
    assert.equal(doc.querySelectorAll('[data-judgment]').filter(el=>el.attrs['aria-pressed']==='true').length,1);
    assert.equal(action('writing-judgment',{activity:'fixture-W1',judgment:'correct'}).attrs['aria-pressed'],'false');
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.understanding_state"),'unknown');
    click('confirm-grade',{activity:'fixture-W1'});
    assert.equal(fixtureGrade().writing_judgment,'incorrect');
    assert.equal(fixtureGrade().comment,'');assert.equal(fixtureGrade().override_reason,'');
  });
});
check('Correct writing plus all valid first answers correct automatically yields known, including hinted answers',()=>{
  withReviewFixture([{correct:true,hinted:true},{correct:true}],()=>{
    const auto=json("computeAutoUnderstanding('fixture','fixture-W1','correct')");
    assert.equal(auto.auto_understanding_state,'known');assert.equal(auto.first_response_count,2);assert.equal(auto.first_correct_count,2);assert.equal(auto.first_hint_count,1);
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});
    // Draft preview must not change the effective classification yet.
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'unknown');
    click('confirm-grade',{activity:'fixture-W1'});
    const g=fixtureGrade();assert.equal(g.understanding_state,'known');assert.equal(g.auto_understanding_state,'known');assert.equal(g.classification_source,'auto');assert.equal(g.manual_override,false);assert.equal(g.targetVersionId,'fixture-W1-v1');assert.equal(g.evidence.length,2);assert.equal(g.rule_version,'writing-understanding-v3-1');assert.deepStrictEqual(g.evidence_itemIds,['fixture-item1','fixture-item2']);
    const snapshot=JSON.stringify(g.evidence);
    run("state.sessions.fixture.responses['fixture-Q1'].first.correct=false;state.sessions.fixture.responses['fixture-Q1'].first.submittedAt='2999-01-01T00:00:00.000Z'");
    assert.equal(JSON.stringify(fixtureGrade().evidence),snapshot);
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'known');
    assert.equal(run('resolveUnderstanding(WORDS[0].id).recheckRequired'),true);
    for(const key of ['meaning','context','sentence','reason'])assert(!Object.hasOwn(g,key));
  });
});
check('Any first-answer mistake keeps correct writing uncertain even after successful retries',()=>{
  for(const firsts of [[{correct:false,retryCorrect:true}],[{correct:true},{correct:false,retryCorrect:true}]])withReviewFixture(firsts,()=>{
    const auto=json("computeAutoUnderstanding('fixture','fixture-W1','correct')");
    assert.equal(auto.auto_understanding_state,'uncertain');assert(auto.first_correct_count<auto.first_response_count);
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});click('confirm-grade',{activity:'fixture-W1'});
    assert.equal(fixtureGrade().understanding_state,'uncertain');
    assert.equal(fixtureGrade().first_correct_count,firsts.filter(x=>x.correct).length);
  });
});
check('No submitted objective evidence, pending choices, and another session cannot satisfy automatic known',()=>{
  for(const firsts of [[],[null]])withReviewFixture(firsts,()=>{
    run("state.sessions.other={id:'other',activities:[{id:'other-Q1',wordId:WORDS[0].id,meaningId:WORDS[0].meaning_id,itemId:'other-item',group:'known'}],responses:{'other-Q1':{first:{correct:true,hinted:false}}},writingActivities:[],writings:{},currentIndex:0}");
    const auto=json("computeAutoUnderstanding('fixture','fixture-W1','correct')");
    assert.equal(auto.first_response_count,0);assert.equal(auto.auto_understanding_state,'uncertain');
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});click('confirm-grade',{activity:'fixture-W1'});
    assert.equal(fixtureGrade().understanding_state,'uncertain');assert.equal(fixtureGrade().evidence.length,0);
  });
});
check('Incorrect and uncertain writing judgments map directly to unknown and uncertain',()=>{
  for(const [judgment,group] of [['incorrect','unknown'],['uncertain','uncertain']])withReviewFixture([{correct:true},{correct:true}],()=>{
    click('writing-judgment',{activity:'fixture-W1',judgment});click('confirm-grade',{activity:'fixture-W1'});
    assert.equal(fixtureGrade().writing_judgment,judgment);assert.equal(fixtureGrade().understanding_state,group);assert.equal(fixtureGrade().auto_understanding_state,group);assert.equal(fixtureGrade().classification_source,'auto');
  });
});
check('Manual uncertain overrides automatic known only on confirmation and survives v2 restoration',()=>{
  withReviewFixture([{correct:true}],()=>{
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});click('confirm-grade',{activity:'fixture-W1'});
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'known');
    assert(run("setUnderstandingOverride('fixture','fixture-W1','uncertain')"));run('render()');
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'known');
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.understanding_state"),'uncertain');
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.manual_override"),true);
    click('confirm-grade',{activity:'fixture-W1'});
    const g=fixtureGrade();assert.equal(g.understanding_state,'uncertain');assert.equal(g.auto_understanding_state,'known');assert.equal(g.classification_source,'manual');assert.equal(g.override_reason,'');
    const stored=json('state');stored.teacherScreen='dashboard';
    windowListeners['openai:set_globals']({detail:{globals:{widgetState:stored}}});
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'uncertain');assert.deepStrictEqual(fixtureGrade(),g);
    // A different judgment resets the draft override, while confirmed state stays put.
    run("teacherPage('grading')");click('writing-judgment',{activity:'fixture-W1',judgment:'incorrect'});
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.manual_override"),false);
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'uncertain');
  });
});
check('Legacy score-only records are preserved without conversion; explicit historical classification stays authoritative',()=>{
  withReviewFixture([{correct:false}],()=>{
    const legacy={targetVersionId:'fixture-W1-v1',meaning:2,context:2,sentence:2,comment:'과거 평가',confirmedAt:'2026-10-01T01:00:00.000Z',teacher:'이전 교사'};
    run("state.sessions.fixture.writings['fixture-W1'].grades="+JSON.stringify([legacy])+";state.sessions.fixture.writings['fixture-W1'].gradeDraft=null;state.sessions.fixture.writings['fixture-W1'].selectedVersionId=null;render()");
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'unknown');
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.writing_judgment"),'');
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.auto_understanding_state"),null);
    assert.deepStrictEqual(json("state.sessions.fixture.writings['fixture-W1'].grades"),[legacy]);
    assert(ids['teacher-main'].innerHTML.includes('새 작문 판정 미등록'));
    const historical={...legacy,understanding_state:'known',reason:'당시 교사 직접 분류'};
    run("state.sessions.fixture.writings['fixture-W1'].grades="+JSON.stringify([historical])+";state.sessions.fixture.writings['fixture-W1'].gradeDraft=null;render()");
    assert.equal(run('effectiveGroups()[WORDS[0].id]'),'known');
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].gradeDraft.writing_judgment"),'');
    const stored=json('state');stored.teacherScreen='dashboard';
    windowListeners['openai:set_globals']({detail:{globals:{widgetState:stored}}});
    assert.equal(run('state.version'),2);assert.equal(run('effectiveGroups()[WORDS[0].id]'),'known');assert.equal(run('resolveUnderstanding(WORDS[0].id).source'),'legacy-teacher');
    assert.deepStrictEqual(json("state.sessions.fixture.writings['fixture-W1'].grades"),[historical]);
    assert.equal(run("state.sessions.fixture.writings['fixture-W1'].versions[0].text"),'학생의 원래 문장');
    assert.equal(run("state.sessions.fixture.responses['fixture-Q1'].first.correct"),false);
  });
});
check('Embedded curriculum replaces numeric criteria with judgment labels and non-scored teacher guidance',()=>{
  const words=json('WORDS');assert.equal(words.length,10);
  for(const w of words){
    assert(!Object.hasOwn(w.writing,'criteria'));
    assert.deepStrictEqual(w.writing.judgment_labels,[{id:'correct',label:'정답'},{id:'incorrect',label:'오답'},{id:'uncertain',label:'검토(애매)'}]);
    assert(Array.isArray(w.writing.teacher_guidance)&&w.writing.teacher_guidance.length>0);
    for(const guide of w.writing.teacher_guidance){assert.equal(typeof guide.instruction,'string');assert(guide.instruction.trim());assert(!Object.hasOwn(guide,'scores'));}
  }
});
check('Teacher records color wrong first answers red across regular, remedial and all review periods',()=>{
  const baseline=run('JSON.stringify(state)');
  try{
    assert(/\.record-answer\.incorrect\s*\{[^}]*color\s*:\s*var\(--red\)/.test(html));
    assert(/--red\s*:\s*#a83535/.test(html));
    run(`{state=fresh();state.self=Object.fromEntries(WORDS.map(w=>[w.id,'unknown']));const qs=ITEMS.filter(q=>q.phase==='practice').slice(0,3),acts=qs.map((q,i)=>({id:'color-Q'+(i+1),type:q.type,wordId:q.word_id,meaningId:word(q.word_id).meaning_id,itemId:q.id,group:'unknown'}));const first=(q,correct)=>({choice:correct?q.correct_option_id:q.options.find(o=>o.id!==q.correct_option_id).id,correct,hinted:false,submittedAt:'2026-10-01T00:00:00.000Z'});state.sessions.regular={id:'regular',activities:acts,responses:{'color-Q1':{first:first(qs[0],false),attempts:[first(qs[0],false),first(qs[0],true)]},'color-Q2':{first:first(qs[1],true),attempts:[first(qs[1],true)]}},writingActivities:[],writings:{},currentIndex:0,quota:{unknown:3,uncertain:0,known:0}};state.sessions['remedial-color']={id:'remedial-color',activities:[{...acts[0],id:'color-remedial'}],responses:{'color-remedial':{first:first(qs[0],false),attempts:[first(qs[0],false),first(qs[0],true)]}},writingActivities:[],writings:{},currentIndex:0,quota:{unknown:1,uncertain:0,known:0}};for(const phase of Object.keys(PHASES)){const targets=WORDS.slice(0,3).map(w=>w.id),responses={};targets.slice(0,2).forEach((wid,i)=>{const q=ITEMS.find(q=>q.phase===phase&&q.word_id===wid);responses[wid]={first:first(q,i===1),attempts:[first(q,i===1),first(q,true)]};});state.reviews[phase]={id:phase,targetWordIds:targets,targetMeaningIds:WORDS.slice(0,3).map(w=>w.meaning_id),responses,currentIndex:0,targetVersion:1};}state.role='teacher';state.teacherScreen='dashboard';render();}`);
    const before=json("state.sessions.regular.responses['color-Q1'].first");
    const wrongMarkup=run("teacherAnswerMarkup(item(state.sessions.regular.activities[0].itemId),state.sessions.regular.responses['color-Q1'])");
    assert(wrongMarkup.includes('class="record-answer incorrect"'));
    assert(wrongMarkup.includes(' · 오답'));
    assert(wrongMarkup.includes(run("esc(item(state.sessions.regular.activities[0].itemId).options.find(o=>o.id===state.sessions.regular.responses['color-Q1'].first.choice).text)")));
    assert(run("teacherAnswerMarkup(item(state.sessions.regular.activities[1].itemId),state.sessions.regular.responses['color-Q2'])").includes('class="record-answer correct"'));
    assert.equal(run("teacherAnswerMarkup(item(state.sessions.regular.activities[2].itemId),undefined)"),'<span class="record-answer pending">미제출</span>');
    const rendered=ids['teacher-main'].innerHTML,rows=[...rendered.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m=>m[1]);
    assert(rows.find(r=>r.includes('regular · color-Q1')).includes('record-answer incorrect'));
    assert(rows.find(r=>r.includes('regular · color-Q2')).includes('record-answer correct'));
    assert(rows.find(r=>r.includes('regular · color-Q3')).includes('record-answer pending'));
    assert(rows.find(r=>r.includes('remedial-color · color-remedial')).includes('record-answer incorrect'));
    assert(rendered.includes('복습 답안 상세'));
    const details=run('teacherReviewAnswerDetails()'),detailRows=[...details.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m=>m[1]);
    for(const label of ['주간','월간','분기']){
      const periodRows=detailRows.filter(r=>r.startsWith('<td>'+label+'</td>'));assert.equal(periodRows.length,3);
      for(const css of ['incorrect','correct','pending'])assert.equal(periodRows.filter(r=>r.includes('record-answer '+css)).length,1);
    }
    assert.deepStrictEqual(json("state.sessions.regular.responses['color-Q1'].first"),before);
    assert.equal(run("state.sessions.regular.responses['color-Q1'].attempts.at(-1).correct"),true);
    assert.equal(run("state.sessions.regular.responses['color-Q1'].first.correct"),false);
    // Empty wrong-word summaries must not inherit the red class.
    run('for(const r of Object.values(state.reviews))for(const response of Object.values(r.responses))response.first.correct=true;render()');
    const summaryRows=[...ids['teacher-main'].innerHTML.matchAll(/<tr>([\s\S]*?)<\/tr>/g)].map(m=>m[1]);
    for(const label of ['주간','월간','분기']){const summary=summaryRows.find(r=>r.startsWith('<td>'+label+'</td>')&&r.includes('오답 없음'));assert(summary);assert(!summary.includes('record-answer incorrect'));}
  }finally{run('state='+baseline+';render()');}
});
check('Donut distributions use unique meanings and latest confirmed grades, with revision and legacy states separate',()=>{
  withReviewFixture([{correct:true}],()=>{
    let s=json('reportSummary()');assert.equal(s.totalWords,10);assert.deepStrictEqual(s.understanding,{known:0,uncertain:0,unknown:0,pending:10});assert.deepStrictEqual(s.writing,{correct:0,incorrect:0,uncertain:0,pending:10});
    click('writing-judgment',{activity:'fixture-W1',judgment:'correct'});click('confirm-grade',{activity:'fixture-W1'});
    s=json('reportSummary()');assert.equal(s.understanding.known,1);assert.equal(s.writing.correct,1);
    run("setUnderstandingOverride('fixture','fixture-W1','uncertain');confirmGrade('fixture','fixture-W1')");
    run("state.sessions.fixture.writings['fixture-W1'].versions.push({id:'fixture-W1-v2',number:2,kind:'revision',text:'재검토할 수정 문장',submittedAt:'2999-01-01T00:00:00.000Z'})");
    s=json('reportSummary()');assert.equal(s.understanding.known,0);assert.equal(s.understanding.uncertain,1);assert.equal(s.writing.correct,1);assert.equal(s.revisionPendingCount,1);assert.equal(Object.values(s.understanding).reduce((a,b)=>a+b),10);assert.equal(Object.values(s.writing).reduce((a,b)=>a+b),10);
    const originalMeaning=run('WORDS[1].meaning_id');
    try{
      run("WORDS[1].meaning_id=WORDS[0].meaning_id;state.sessions.fixture.writingActivities.push({id:'alias-W',wordId:WORDS[1].id,meaningId:WORDS[0].meaning_id,type:'writing'});state.sessions.fixture.writings['alias-W']={versions:[{id:'alias-v1',number:1,kind:'draft',text:'별칭 문장',submittedAt:'2026-10-01T00:00:00.000Z'}],grades:[{targetVersionId:'alias-v1',writing_judgment:'incorrect',understanding_state:'unknown',classification_source:'manual',confirmedAt:'3000-01-01T00:00:00.000Z'}]}");
      s=json('reportSummary()');assert.equal(s.totalWords,9);assert.equal(new Set(s.meaningIds).size,9);assert.equal(s.understanding.unknown,1);assert.equal(s.writing.incorrect,1);assert.equal(Object.values(s.understanding).reduce((a,b)=>a+b),9);assert.equal(Object.values(s.writing).reduce((a,b)=>a+b),9);
    }finally{run('WORDS[1].meaning_id='+JSON.stringify(originalMeaning));}
    run("state.sessions.fixture.writingActivities.push({id:'legacy-chart-W',wordId:WORDS[2].id,meaningId:WORDS[2].meaning_id,type:'writing'});state.sessions.fixture.writings['legacy-chart-W']={versions:[{id:'legacy-chart-v1',number:1,kind:'draft',text:'기존 기록 문장',submittedAt:'2026-10-01T00:00:00.000Z'}],grades:[{targetVersionId:'legacy-chart-v1',meaning:2,context:2,sentence:2,understanding_state:'known',confirmedAt:'2026-10-01T01:00:00.000Z'}]}");
    s=json('reportSummary()');const legacy=s.rows.find(r=>r.wordId===wordIds[2]);assert.equal(legacy.understanding,'known');assert.equal(legacy.writing,'pending');assert.equal(s.totalWords,10);
  });
});
check('Known-word comparison uses actual prior confirmed snapshots and never invents a first baseline',()=>{
  withReviewFixture([{correct:true}],()=>{
    run("state.teacher.includeMessage=false;teacherPage('report')");
    assert.equal(json('reportSummary().comparison').available,false);
    assert(!Object.hasOwn(json('reportSummary().comparison'),'confirmedAt'));
    click('confirm-report');
    const first=json('state.teacher.confirmedSnapshot.assessmentSnapshot');assert(run('validAssessmentSnapshot(state.teacher.confirmedSnapshot.assessmentSnapshot)'));assert.equal(first.understanding.known,0);assert.equal(first.reportVersion,1);assert.equal(run('state.teacher.confirmedSnapshot.previousAssessmentSnapshot'),null);assert.equal(json('reportSummary().comparison').available,false);
    run("selectGradeVersion(state.sessions.fixture.writings['fixture-W1'],'fixture-W1-v1');chooseWritingJudgment('fixture','fixture-W1','correct');confirmGrade('fixture','fixture-W1');render()");
    let comparison=json('reportSummary().comparison');assert.equal(comparison.available,true);assert.equal(comparison.previousKnown,0);assert.equal(comparison.currentKnown,1);assert.equal(comparison.delta,1);assert.equal(comparison.confirmedAt,first.confirmedAt);assert(comparison.message.includes('이전 확정 자료 대비'));
    click('confirm-report');
    assert.deepStrictEqual(json('state.teacher.confirmedSnapshot.previousAssessmentSnapshot'),first);
    comparison=json('reportSummary().comparison');assert.equal(comparison.available,true);assert.equal(comparison.delta,1);assert.equal(comparison.reportVersion,1);
    run("state.teacher.confirmedSnapshot.previousAssessmentSnapshot.meaningIds[0]='different-meaning'");
    assert.equal(json('reportSummary().comparison').available,false);
    assert(json('reportSummary().comparison').message.includes('대상 단어가 달라'));
  });
});
check('Charts and legends render safely for zero targets and share teacher-parent printable SVG without memos',()=>{
  withReviewFixture([],()=>{
    run('globalThis.chartWordsBackup=WORDS.splice(0)');
    try{
      const s=json('reportSummary()');assert.equal(s.totalWords,0);assert.equal(s.writingProgress.total,0);
      const charts=run('renderAssessmentCharts()'),progress=run('renderReportProgress()');
      assert.equal((charts.match(/<svg\b/g)||[]).length,2);assert(charts.includes('대상 없음'));assert(!/NaN|Infinity|100%/.test(charts+progress));
    }finally{run('WORDS.push(...globalThis.chartWordsBackup);delete globalThis.chartWordsBackup');}
    run("state.sessions.regular={id:'regular',activities:[{id:'chart-Q1',wordId:WORDS[0].id,meaningId:WORDS[0].meaning_id,itemId:'chart-item1',group:'unknown'},{id:'chart-Q2',wordId:WORDS[0].id,meaningId:WORDS[0].meaning_id,itemId:'chart-item2',group:'unknown'}],responses:{'chart-Q1':{first:{correct:true,hinted:false}}},writingActivities:[],writings:{},currentIndex:0};state.sessions['remedial-chart']={id:'remedial-chart',activities:[{id:'chart-remedial',wordId:WORDS[0].id,meaningId:WORDS[0].meaning_id,itemId:'chart-item3',group:'unknown'}],responses:{'chart-remedial':{first:{correct:true,hinted:false}}},writingActivities:[],writings:{},currentIndex:0};state.teacher.internalMemo='차트에 노출되면 안 되는 내부 메모';teacherPage('report')");
    const s=json('reportSummary()');assert.deepStrictEqual(s.objectiveProgress,{completed:1,total:2,remaining:1});assert.deepStrictEqual(s.writingProgress,{completed:1,total:10,remaining:9});
    const charts=run('renderAssessmentCharts()'),progress=run('renderReportProgress()'),parent=run('parentReport()');
    assert.equal((charts.match(/<svg\b/g)||[]).length,2);assert(charts.includes('chart-legend'));assert(charts.includes('10개 <small>100%</small>'));assert(/<(?:circle|path)[^>]*(?:fill|stroke)="#[A-Fa-f0-9]+"/.test(charts));assert(charts.includes('교사 확인 대기'));assert(charts.includes('평가 대기'));assert(progress.includes('정규 객관 연습'));assert(progress.includes('전수 작문 제출'));
    const categories=[{id:'known',label:'앎'},{id:'uncertain',label:'애매함'},{id:'unknown',label:'모름'},{id:'pending',label:'대기'}];
    for(const [counts,total] of [[{known:0,uncertain:0,unknown:0,pending:0},0],[{known:1,uncertain:0,unknown:0,pending:0},1],[{known:2,uncertain:1,unknown:1,pending:0},4]]){
      const donut=run('renderDonut("형태 검수","0·전체·복수 범주",'+JSON.stringify(counts)+','+JSON.stringify(categories)+','+total+',"geometry-check")');
      assert(!/NaN|Infinity/.test(donut));assert(!donut.includes('stroke-dasharray'));
      const paths=[...donut.matchAll(/<path\b([^>]*)>/g)];
      for(const p of paths){const d=p[1].match(/\bd="([^"]+)"/)?.[1];assert(d);const numbers=d.match(/-?(?:\d+(?:\.\d+)?|\.\d+)(?:e[+-]?\d+)?/gi)||[];assert(numbers.length>0);assert(numbers.every(n=>Number.isFinite(Number(n))));}
      if(total){for(const category of categories.filter(c=>counts[c.id]>0)){const color=run('CHART_COLORS.'+category.id);assert(paths.some(p=>p[1].includes('fill="'+color+'"')));}}else assert(!donut.includes('100%'));
    }
    assert(ids['teacher-main'].innerHTML.includes(charts));assert(parent.includes(charts));assert(parent.includes(progress));assert(!parent.includes('차트에 노출되면 안 되는 내부 메모'));
  });
});
const result={prototypeVersion:2,teacherReviewVersion:3,method:'Node VM + mocked DOM; pure-function and event-handler behavioral checks',syntax:'PASS',mockDomFlow:'PASS',checks,scope:{diagnosticRows:10,regularObjectiveActivities:10,objectiveQuota:'6/3/1',fullWritingTargets:10,partialWritingSubmission:4,periodCoverageTargets:10,hostStateVersion:2,teacherJudgments:['correct','incorrect','uncertain'],numericWritingScores:false,classificationRule:'writing-understanding-v3-1',teacherFirstAnswerColors:true,assessmentCharts:2},actualBrowser:'NOT RUN — mocked DOM only',notVerified:['Actual pointer drag and drop','Real browser appearance and accessibility','Production authentication and authorization','Server autosave, calendar aggregation and deployment','Educational content approval or learning efficacy']};
// Read-only audit: do not rewrite source validation metadata.
console.log(JSON.stringify(result,null,2));
