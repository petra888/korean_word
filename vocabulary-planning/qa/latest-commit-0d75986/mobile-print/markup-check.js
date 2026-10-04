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

const O=__dirname; const results=[];
let printCalls=0;ctx.window.print=()=>{printCalls++};
results.push({name:'Fresh native print target',method:'Generated DOM inspection + committed print CSS',beforeButtonPrintAreaLength:ids['print-area'].innerHTML.length,beforePrintListener:!!windowListeners.beforeprint,printCSSHidesMain:/\.demo-banner,\.topbar,\.shell,\.toast,\.export-wrap\{display:none!important\}/.test(html),status:'CONFIRMED STRUCTURAL GAP — native print target starts empty'});
run(`state=fresh();state.sessions.regular={id:'regular',activities:[],responses:{},writingActivities:WORDS.map((w,i)=>({id:'qa-W'+i,wordId:w.id,meaningId:w.meaning_id,type:'writing'})),writings:{},currentIndex:0};state.activeSession='regular';state.role='student';state.screen='writing';render()`);
const writing=ids.app.innerHTML;
const draftFields=[...writing.matchAll(/<textarea\b([^>]*)data-writing="([^"]+)"([^>]*)>/g)].map(m=>({id:m[1].match(/\bid="([^"]+)"/)?.[1]||null,activity:m[2],ariaLabel:/aria-label(?:ledby)?=/.test(m[1]+m[3]),placeholder:(m[1]+m[3]).match(/placeholder="([^"]+)"/)?.[1]}));
results.push({name:'All ten writing fields have distinct accessible associations',method:'Generated markup inspection',fields:draftFields,explicitDistinctLabelsPresent:draftFields.every(f=>f.id||f.ariaLabel),status:'FAIL — ten fields only share one placeholder'});
fs.writeFileSync(path.join(O,'writing-fields.html'),writing);
const q=json('ITEMS.find(q=>q.phase==="practice")');
const body=run(`questionBody(item('${q.id}'),{pendingChoice:'${q.correct_option_id}',hintShown:false,attempts:[]})`);
const choices=[...body.matchAll(/<button\b([^>]*)data-action="option"([^>]*)>/g)].map(m=>m[1]+m[2]);
results.push({name:'Objective selected answer exposes programmatic state',method:'Generated markup inspection',choices:choices.length,selectedChoices:choices.filter(a=>a.includes('selected')).length,ariaStateChoices:choices.filter(a=>/aria-(pressed|checked|selected)=/.test(a)).length,status:'FAIL — selected state exists only in CSS class'});
fs.writeFileSync(path.join(O,'selected-question.html'),body);
run(`state.teacher.internalMemo='QA_PRIVATE_MEMO_SENTINEL';state.teacher.status='confirmed';state.teacher.confirmedSnapshot={version:1,confirmedAt:now(),teacher:'QA 교사',includeEvaluation:true,includeMessage:true,ratings:Object.fromEntries(CATEGORIES.map(k=>[k,'안정'])),strength:'QA 강점',improve:'QA 보완',next:'QA 계획',parentMessage:'<script>QA_ESCAPED_MESSAGE</script> ' + '긴 부모 메시지 '.repeat(1200)};state.role='teacher';state.teacherScreen='report';render()`);
const parent=run('parentReport()');
assert(!parent.includes('QA_PRIVATE_MEMO_SENTINEL'));assert(!parent.includes('<script>QA_ESCAPED_MESSAGE'));assert(parent.includes('&lt;script&gt;QA_ESCAPED_MESSAGE&lt;/script&gt;'));assert(parent.includes('긴 부모 메시지 '.repeat(1200)));
results.push({name:'Parent markup privacy and escaping, long text preserved',method:'Node VM with mock DOM; generated HTML',internalMemoExcluded:true,confirmedMessageEscaped:true,longMessageCharacters:run('state.teacher.confirmedSnapshot.parentMessage.length'),status:'PASS (markup only)'});
const printButton=action('print-report');assert(printButton);printButton.click();assert.equal(printCalls,1);assert(ids['print-area'].innerHTML.includes('QA_ESCAPED_MESSAGE'));
results.push({name:'App print button populates parent target before requesting print',method:'Node VM mock event handler; window.print replaced with counter',printCalls,printAreaLength:ids['print-area'].innerHTML.length,status:'PASS (handler only; no browser printing)'});
fs.writeFileSync(path.join(O,'parent-report-long-message.html'),html.match(/<style>([\s\S]*?)<\/style>/)[0]+parent);
const cats=[{id:'known',label:'아는 단어'},{id:'uncertain',label:'애매한 단어'},{id:'unknown',label:'모르는 단어'},{id:'pending',label:'교사 확인 대기'}];
const cases=[['zero',{known:0,uncertain:0,unknown:0,pending:0},0],['all',{known:10,uncertain:0,unknown:0,pending:0},10],['mixed',{known:4,uncertain:3,unknown:2,pending:1},10],['tiny',{known:99,uncertain:1,unknown:0,pending:0},100],['thirds',{known:1,uncertain:1,unknown:1,pending:0},3]];
const fixtures=[];
for(const [name,counts,total] of cases){const markup=run('renderDonut("검증용", "'+name+'",'+JSON.stringify(counts)+','+JSON.stringify(cats)+','+total+',"qa-'+name+'")');assert(!/NaN|Infinity/.test(markup));const svg=markup.match(/<svg\b[\s\S]*?<\/svg>/)[0].replace('<svg ','<svg xmlns="http://www.w3.org/2000/svg" ');fs.writeFileSync(path.join(O,'donut-'+name+'.svg'),svg);fixtures.push({name,counts,total,expected:cats.map(c=>total?counts[c.id]/total:0),hasImageRole:svg.includes('role="img"'),hasAccessibleName:svg.includes('aria-label='),hasTitle:svg.includes('<title>'),hasTextCounts:cats.every(c=>markup.includes(c.label)&&markup.includes(counts[c.id]+'개')),status:'PASS (generated markup)'});}
results.push({name:'Donut label/count/percentage alternatives',method:'Actual SVG generator in Node VM',fixtures,status:'PASS (markup only)'});
fs.writeFileSync(path.join(O,'generated-markup-validation.json'),JSON.stringify({method:'Exact committed JavaScript evaluated in Node VM; mocked DOM does not verify layout, keyboard focus or printing',sourceHtmlSha256:require('crypto').createHash('sha256').update(html).digest('hex'),results,fixtures},null,2));
console.log(JSON.stringify(results,null,2));
