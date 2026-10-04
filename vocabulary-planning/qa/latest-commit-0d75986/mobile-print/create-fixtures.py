from pathlib import Path
S=Path('/tmp/vocabulary-full-qa-0d75986-n5h3m0i4/vocabulary-planning')
O=Path('/workspace/korean_word/vocabulary-planning/qa/latest-commit-0d75986/mobile-print')
prefix=(S/'qa/development-readiness/prototype-vm-check.js').read_text().split('const wordIds=json')[0]
prefix=prefix.replace("path.resolve(__dirname,'../../prototype/pilot-flow.html')",repr(str(S/'prototype/pilot-flow.html')))
extra=r'''
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
'''
O.joinpath('markup-check.js').write_text(prefix+extra)
