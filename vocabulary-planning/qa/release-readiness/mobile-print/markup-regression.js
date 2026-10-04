// Node VM + mocked DOM: behavioral checks only, not browser or server verification.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const sourcePath=process.argv[2]||path.resolve(__dirname,'../../../prototype/pilot-flow.html');
const html=fs.readFileSync(sourcePath,'utf8');
const payload=html.match(/<script type="application\/json" id="curriculum-data">([\s\S]+?)<\/script>/)[1],source=html.match(/<script>\n([\s\S]+?)<\/script>/)[1];
const decode=s=>String(s).replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&');
const ids={},saved={},windowListeners={};let nodes=[],hostWrites=0;
class El{
  constructor(id='',attrs='',text=''){this.id=id;this.textContent=text;this.value='';this.checked=false;this.tagName='BUTTON';this.dataset={};this.listeners={};this.attrs={};this.classList={toggle(){},add(){},remove(){}};for(const m of attrs.matchAll(/([\w-]+)="([^"]*)"/g)){this.attrs[m[1]]=decode(m[2]);if(m[1].startsWith('data-'))this.dataset[m[1].slice(5).replace(/-([a-z])/g,(_,x)=>x.toUpperCase())]=decode(m[2]);}this.disabled=/\bdisabled\b/.test(attrs);this.checked=/\bchecked\b/.test(attrs);this.value=this.attrs.value||'';}
  get innerHTML(){return this._html||'';}
  set innerHTML(v){this._html=v;nodes=this.id==='app'?[]:nodes.filter(n=>n.owner!==this.id);for(const m of v.matchAll(/<(button|textarea|select)\b([^>]*)>([\s\S]*?)<\/\1>|<(input)\b([^>]*)>/g)){const tag=m[1]||m[4],el=new El('',m[2]||m[5],decode(m[3]||''));el.tagName=tag.toUpperCase();el.id=el.attrs.id||'';el.owner=this.id;if(tag==='textarea')el.value=decode(m[3]||'');if(tag==='select'){const options=[...(m[3]||'').matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/g)],op=options.find(o=>/\bselected\b/.test(o[1]))||options[0];if(op)el.value=decode(op[1].match(/value="([^"]*)"/)?.[1]??op[2]);}nodes.push(el);}}
  addEventListener(name,fn){this.listeners[name]=fn;}getAttribute(n){return this.attrs[n];}setAttribute(n,v){this.attrs[n]=v;}focus(){doc.activeElement=this;}select(){}scrollIntoView(){}remove(){}trigger(name){this.listeners[name]?.({target:this,currentTarget:this,preventDefault(){}});}click(){if(!this.disabled)this.trigger('click');}
}
for(const m of html.matchAll(/\bid="([^"]+)"/g))ids[m[1]]??=new El(m[1]);ids['curriculum-data'].textContent=payload;
function query(sel){if(sel.startsWith('#'))return [doc.getElementById(sel.slice(1))];const ms=[...sel.matchAll(/\[([\w-]+)(?:="([^"]*)")?\]/g)];return ms.length?nodes.filter(n=>ms.every(m=>Object.hasOwn(n.attrs,m[1])&&(m[2]===undefined||n.attrs[m[1]]===m[2]))):[];}
const doc={getElementById(id){return nodes.find(n=>n.id===id)||(ids[id]??=new El(id));},querySelectorAll:query,querySelector(s){return query(s)[0]||null;},documentElement:{},body:{appendChild(){}},createElement(){return new El();}};
const ctx=vm.createContext({document:doc,window:{scrollTo(){},confirm(){return true},print(){},addEventListener(n,cb){windowListeners[n]=cb},openai:null},localStorage:{getItem(k){return saved[k]||null},setItem(k,v){saved[k]=v},removeItem(k){delete saved[k]}},console,Date,Intl,Math,Blob,URL,setTimeout});vm.runInContext(source,ctx);
const run=c=>vm.runInContext(c,ctx),json=c=>JSON.parse(run(`JSON.stringify(${c})`)),action=(a,f={})=>nodes.find(n=>n.dataset.action===a&&Object.entries(f).every(([k,v])=>n.dataset[k]===v));
function click(a,f){const n=action(a,f);assert(n,'missing '+a);assert(!n.disabled,'disabled '+a);n.click();}const choose=option=>click('option',{option}),checks=[];
function check(name,fn){fn();checks.push({name,status:'PASS'});}

const O=__dirname,results=[],fixtures=[];
function test(name,fn){try{const detail=fn()||{};results.push({name,status:'PASS',...detail});}catch(e){results.push({name,status:'FAIL',error:e.message});}}
let printCalls=0;ctx.window.print=()=>{printCalls++};
test('MP-003: Native print at initial screen creates a current parent report',()=>{
 assert.equal(typeof windowListeners.beforeprint,'function','beforeprint listener missing');
 assert.equal(ids['print-area'].innerHTML.length,0,'fixture must begin with empty print target');
 windowListeners.beforeprint({type:'beforeprint'});
 assert(ids['print-area'].innerHTML.includes('report-page'));
 assert(ids['print-area'].innerHTML.includes('어휘 학습 기록'));
 assert(/\.print-area\{display:block!important\}/.test(html));
 return {method:'Node VM event callback and generated markup; no browser printing',printAreaCharacters:ids['print-area'].innerHTML.length};
});
run(`state=fresh();state.sessions.regular={id:'regular',activities:[],responses:{},writingActivities:WORDS.map((w,i)=>({id:'qa-W'+i,wordId:w.id,meaningId:w.meaning_id,type:'writing'})),writings:{},currentIndex:0};state.activeSession='regular';state.role='student';state.screen='writing';render()`);
const writing=ids.app.innerHTML;
fs.writeFileSync(path.join(O,'writing-fields.html'),writing);
function attributes(s){return Object.fromEntries([...s.matchAll(/([\w-]+)="([^"]*)"/g)].map(m=>[m[1],decode(m[2])]));}
function textForId(markup,id){const escaped=id.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const match=markup.match(new RegExp('<([\\w]+)\\b[^>]*\\bid="'+escaped+'"[^>]*>([\\s\\S]*?)<\\/\\1>'));return match?decode(match[2].replace(/<[^>]+>/g,' ')):'';}
function accessibleName(markup,attrs){if(attrs['aria-label'])return attrs['aria-label'];if(attrs['aria-labelledby'])return attrs['aria-labelledby'].split(/\s+/).map(id=>textForId(markup,id)).join(' ');if(attrs.id){const escaped=attrs.id.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');const match=markup.match(new RegExp('<label\\b[^>]*for="'+escaped+'"[^>]*>([\\s\\S]*?)<\\/label>'));if(match)return decode(match[1].replace(/<[^>]+>/g,' '));}return '';}
let fieldEvidence=[];
test('MP-002: Ten draft textareas expose distinct word-specific names',()=>{
 const fields=[...writing.matchAll(/<textarea\b([^>]*)>/g)].map(m=>attributes(m[1])).filter(a=>a['data-writing']);
 const words=json('WORDS.map(w=>({id:w.id,title:titleWord(w.id)}))');
 assert.equal(fields.length,10);
 fieldEvidence=fields.map((a,i)=>({word:words[i].title,id:a.id||null,name:accessibleName(writing,a),descriptionReferences:a['aria-describedby']||null}));
 assert(fields.every(a=>!!a.id),'textarea id missing');assert.equal(new Set(fields.map(a=>a.id)).size,10,'duplicate textarea ids');
 assert(fieldEvidence.every((f,i)=>f.name.includes(words[i].title)),'word-specific accessible name missing');
 for(const a of fields)for(const id of (a['aria-labelledby']||'').split(/\s+/).filter(Boolean))assert(textForId(writing,id),'unresolved label reference '+id);
 for(const a of fields)for(const id of (a['aria-describedby']||'').split(/\s+/).filter(Boolean))assert(textForId(writing,id),'unresolved description reference '+id);
 return {method:'Generated HTML attributes and referenced text; no screen reader',fields:fieldEvidence};
});
test('Revision textareas expose word-specific names after teacher confirmation',()=>{
 run(`for(const a of state.sessions.regular.writingActivities){const wr=state.sessions.regular.writings[a.id];wr.versions=[{id:a.id+'-v1',number:1,kind:'draft',text:'QA '+titleWord(a.wordId)+' 문장',submittedAt:now()}];wr.grades=[{targetVersionId:a.id+'-v1',writing_judgment:'correct',understanding_state:'known',auto_understanding_state:'known',auto_reason:'QA 판정',classification_source:'automatic',comment:'QA 피드백',confirmedAt:now()}];}render()`);
 const markup=ids.app.innerHTML,fields=[...markup.matchAll(/<textarea\b([^>]*)>/g)].map(m=>attributes(m[1])).filter(a=>a['data-revision-input']);
 const words=json('WORDS.map(w=>({id:w.id,title:titleWord(w.id)}))');assert.equal(fields.length,10);
 const names=fields.map(a=>accessibleName(markup,a));assert(names.every((name,i)=>name.includes(words[i].title)),'word-specific revision name missing');
 return {method:'Generated revision HTML in Node VM; no screen reader',fields:fields.map((a,i)=>({word:words[i].title,id:a.id||null,name:names[i]}))};
});
const q=json('ITEMS.find(q=>q.phase==="practice")');
let body;
test('MP-001: Objective choices expose exactly one selected state and clear alternatives',()=>{
 body=run(`selection=null;retrying=false;questionBody(item('${q.id}'),{pendingChoice:'${q.correct_option_id}',hintShown:false,attempts:[]})`);
 const choices=[...body.matchAll(/<button\b([^>]*)>/g)].map(m=>attributes(m[1])).filter(a=>a['data-action']==='option');
 assert.equal(choices.length,4);
 const stateOf=a=>a['aria-pressed']??a['aria-checked']??a['aria-selected'];
 assert(choices.every(a=>['true','false'].includes(stateOf(a))),'selection state absent on one or more choices');
 assert.equal(choices.filter(a=>stateOf(a)==='true').length,1);
 assert.equal(choices.find(a=>stateOf(a)==='true')['data-option'],q.correct_option_id);
 const empty=run(`selection=null;retrying=false;questionBody(item('${q.id}'),{hintShown:false,attempts:[]})`);
 const emptyChoices=[...empty.matchAll(/<button\b([^>]*)>/g)].map(m=>attributes(m[1])).filter(a=>a['data-action']==='option');
 assert(emptyChoices.every(a=>stateOf(a)==='false'));
 const wrong=q.options.find(o=>o.id!==q.correct_option_id).id;
 const responded={first:{choice:wrong,correct:false},attempts:[{choice:wrong,correct:false},{choice:q.correct_option_id,correct:true}],pendingChoice:null,retryEditing:false};
 const after=run(`selection=null;retrying=false;questionBody(item('${q.id}'),${JSON.stringify(responded)})`);
 const submittedChoices=[...after.matchAll(/<button\b([^>]*)>/g)].map(m=>attributes(m[1])).filter(a=>a['data-action']==='option');
 assert.equal(submittedChoices.filter(a=>stateOf(a)==='true').length,1);
 assert.equal(submittedChoices.find(a=>stateOf(a)==='true')['data-option'],q.correct_option_id,'latest submitted choice not retained');
 assert(after.includes('첫 답 오답'),'original first-answer result no longer visible after corrected retry');
 return {method:'Actual questionBody generator in Node VM; no keyboard/focus test',optionCount:choices.length,selectedCount:1,unselectedCount:3,submittedSelectionRetained:true,firstIncorrectPreservedAfterCorrectRetry:true};
});
fs.writeFileSync(path.join(O,'selected-question.html'),body||'');
run(`state.teacher.internalMemo='QA_PRIVATE_MEMO_SENTINEL';state.teacher.status='confirmed';state.teacher.confirmedSnapshot={version:1,confirmedAt:now(),teacher:'QA 교사',includeEvaluation:true,includeMessage:true,ratings:Object.fromEntries(CATEGORIES.map(k=>[k,'안정'])),strength:'QA_CONFIRMED_STRENGTH',improve:'QA 보완',next:'QA 계획',parentMessage:'<script>QA_ESCAPED_MESSAGE</script> ' + '긴 부모 메시지 '.repeat(1200)};state.role='teacher';state.teacherScreen='report';render()`);
let parent;
test('Confirmed parent report excludes internal memo, escapes and preserves a long message',()=>{
 parent=run('parentReport()');assert(!parent.includes('QA_PRIVATE_MEMO_SENTINEL'));assert(!parent.includes('<script>QA_ESCAPED_MESSAGE'));assert(parent.includes('&lt;script&gt;QA_ESCAPED_MESSAGE&lt;/script&gt;'));assert(parent.includes('긴 부모 메시지 '.repeat(1200)));assert(parent.includes('QA_CONFIRMED_STRENGTH'));
 return {method:'Generated HTML inspection in Node VM',internalMemoExcluded:true,confirmedMessageEscaped:true,longMessageCharacters:run('state.teacher.confirmedSnapshot.parentMessage.length')};
});
test('App print button refreshes output before requesting print',()=>{
 ids['print-area'].innerHTML='QA_STALE_PRINT_TARGET';
 const printButton=action('print-report');assert(printButton);printButton.click();assert.equal(printCalls,1);assert(ids['print-area'].innerHTML.includes('QA_ESCAPED_MESSAGE'));assert(!ids['print-area'].innerHTML.includes('QA_STALE_PRINT_TARGET'));
 return {method:'Mock print call counter and actual handler',printCalls,printAreaCharacters:ids['print-area'].innerHTML.length};
});
test('MP-003: Native beforeprint replaces stale output with current confirmed content',()=>{
 run(`state.teacher.confirmedSnapshot.parentMessage='QA_UPDATED_CONFIRMED_PARENT_MESSAGE';state.teacher.internalMemo='QA_NEW_PRIVATE_MEMO';`);
 ids['print-area'].innerHTML='QA_STALE_PARENT_CONTENT';
 assert.equal(typeof windowListeners.beforeprint,'function');windowListeners.beforeprint({type:'beforeprint'});
 const target=ids['print-area'].innerHTML;assert(target.includes('QA_UPDATED_CONFIRMED_PARENT_MESSAGE'));assert(!target.includes('QA_ESCAPED_MESSAGE'));assert(!target.includes('QA_STALE_PARENT_CONTENT'));assert(!target.includes('QA_NEW_PRIVATE_MEMO'));
 return {method:'Actual event callback in Node VM',freshConfirmedMessage:true,staleOutputRemoved:true,internalMemoExcluded:true};
});
test('Native printing while report is draft excludes unconfirmed teacher text',()=>{
 run(`state.teacher.status='draft';state.teacher.parentMessage='QA_DRAFT_PARENT_DO_NOT_PRINT';state.teacher.strength='QA_DRAFT_STRENGTH_DO_NOT_PRINT';`);
 assert.equal(typeof windowListeners.beforeprint,'function');windowListeners.beforeprint({type:'beforeprint'});const target=ids['print-area'].innerHTML;
 assert(!target.includes('QA_DRAFT_PARENT_DO_NOT_PRINT'));assert(!target.includes('QA_DRAFT_STRENGTH_DO_NOT_PRINT'));assert(!target.includes('QA_NEW_PRIVATE_MEMO'));
 return {method:'Actual event callback in Node VM',unconfirmedParentMessageExcluded:true,unconfirmedStrengthExcluded:true};
});
fs.writeFileSync(path.join(O,'parent-report-long-message.html'),html.match(/<style>([\s\S]*?)<\/style>/)[0]+(parent||''));
const cats=[{id:'known',label:'아는 단어'},{id:'uncertain',label:'애매한 단어'},{id:'unknown',label:'모르는 단어'},{id:'pending',label:'교사 확인 대기'}];
const cases=[['zero',{known:0,uncertain:0,unknown:0,pending:0},0],['all',{known:10,uncertain:0,unknown:0,pending:0},10],['mixed',{known:4,uncertain:3,unknown:2,pending:1},10],['tiny',{known:99,uncertain:1,unknown:0,pending:0},100],['thirds',{known:1,uncertain:1,unknown:1,pending:0},3]];
test('Donut charts provide label/count/percentage alternatives in five edge cases',()=>{
 for(const [name,counts,total] of cases){const markup=run('renderDonut("검증용", "'+name+'",'+JSON.stringify(counts)+','+JSON.stringify(cats)+','+total+',"qa-'+name+'")');assert(!/NaN|Infinity/.test(markup));const svg=markup.match(/<svg\b[\s\S]*?<\/svg>/)[0].replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" ');assert(svg.includes('role="img"'));assert(svg.includes('aria-label='));assert(svg.includes('<title>'));assert(cats.every(c=>markup.includes(c.label)&&markup.includes(counts[c.id]+'개')));fs.writeFileSync(path.join(O,'donut-'+name+'.svg'),svg);fixtures.push({name,counts,total,expected:cats.map(c=>total?counts[c.id]/total:0),status:'PASS'});}
 return {method:'Actual SVG generator in Node VM',fixtureCount:fixtures.length};
});
const summary={sourcePath,sourceHtmlSha256:require('crypto').createHash('sha256').update(html).digest('hex'),method:'Current edited source evaluated in Node VM with mocked DOM. Layout, browser accessibility tree, focus, touch and browser printing are not exercised.',results,fixtures,passed:results.filter(r=>r.status==='PASS').length,failed:results.filter(r=>r.status==='FAIL').length};
fs.writeFileSync(path.join(O,'generated-markup-validation.json'),JSON.stringify(summary,null,2));console.log(JSON.stringify({passed:summary.passed,failed:summary.failed,results},null,2));if(summary.failed)process.exitCode=1;
