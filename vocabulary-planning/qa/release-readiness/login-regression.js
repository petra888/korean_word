// Test-login edge cases in the actual prototype JS; no server authentication claim.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {boot,target}=require('./regression/vm-harness');
const AUTH='vocabulary-demo-login-v1',LEARNING='vocabulary-pilot-flow-v2',checks=[];
function guest(config={}){const b=boot({...config,autoLogin:false});assert(!b.bootError,JSON.stringify(b.bootError));return b;}
function check(name,fn){try{checks.push({name,status:'PASS',details:fn()||{}});}catch(e){checks.push({name,status:'FAIL',error:e.stack});}}
function marker(role='student'){return {version:1,role,username:role==='teacher'?'test2':'test1',expiresAt:Date.now()+60000};}
check('No saved learning role or missing session automatically signs in',()=>{
 const b=guest();assert.equal(b.run('signedIn()'),false);assert(b.ids.app.innerHTML.includes('login-form'));const state=b.json('state');state.role='teacher';state.teacherScreen='report';const c=guest({saved:{[LEARNING]:JSON.stringify(state)}});assert.equal(c.run('signedIn()'),false);assert(!c.ids.app.innerHTML.includes('data-report-field'));assert(c.ids['account-toolbar'].hidden);
});
check('Invalid and unknown credentials do not create a session or alter learning records',()=>{
 const b=guest(),before=b.json('state');for(const call of ["signIn('student','test1','wrong')","signIn('teacher','test1','test1')","signIn('__proto__','test1','test1')"]){assert.equal(b.run(call),false);assert.deepStrictEqual(b.json('state'),before);assert.equal(b.sessionSaved[AUTH],undefined);}
});
check('Valid session restores the matching account and ignores extra stored fields',()=>{
 const b=guest({sessionSaved:{[AUTH]:JSON.stringify({...marker('teacher'),password:'SHOULD_NOT_LOAD',extra:'ignore'})}});assert.equal(b.run("signedIn('teacher')"),true);assert.equal(b.run('state.role'),'teacher');assert.deepStrictEqual(Object.keys(b.json('authSession')).sort(),['expiresAt','role','username','version']);assert(b.ids.app.innerHTML.includes('teacher-nav'));
});
check('Expired, excessive-future, wrong-account and unknown-role sessions are removed',()=>{
 const invalid=[{...marker(),expiresAt:0},{...marker(),expiresAt:Date.now()+9*60*60*1000},{...marker(),username:'test2'},{...marker(),role:'admin'}];for(const m of invalid){const b=guest({sessionSaved:{[AUTH]:JSON.stringify(m)}});assert.equal(b.run('signedIn()'),false);assert.equal(b.sessionSaved[AUTH],undefined);}
});
check('Broken session JSON is discarded without falsely claiming storage is unavailable',()=>{
 const b=guest({sessionSaved:{[AUTH]:'{broken'}});assert.equal(b.run('signedIn()'),false);assert.equal(b.sessionSaved[AUTH],undefined);assert.equal(b.run('authStorageWarning'),'');
});
check('Blocked session reads leave login usable and never infer authentication from saved data',()=>{
 const b=guest({sessionReadThrow:true});assert.equal(b.run('signedIn()'),false);assert(b.ids.app.innerHTML.includes('login-form'));assert(b.run('authStorageWarning').includes('다시 로그인'));b.loginAs('student');assert.equal(b.run("signedIn('student')"),true);
});
check('Blocked session writes allow the current tab and explain that reload needs login',()=>{
 const b=guest({sessionWriteThrow:true});b.loginAs('teacher');assert.equal(b.run("signedIn('teacher')"),true);assert.equal(b.sessionSaved[AUTH],undefined);assert(b.ids['storage-status'].textContent.includes('다시 로그인'));const c=guest({saved:b.saved,sessionSaved:b.sessionSaved});assert.equal(c.run('signedIn()'),false);
});
check('Logout clears authentication and private panels while retaining all learning records',()=>{
 const b=boot();assert(!b.bootError);b.run("diagnosticUnknown(WORDS[0].id);persist()");b.loginAs('teacher');b.ids['export-record'].click();b.run('prepareParentPrint()');const before=b.json('state.sessions'),diagnostic=b.json('state.diagnostic');b.ids.logout.click();assert.equal(b.run('signedIn()'),false);assert.equal(b.sessionSaved[AUTH],undefined);assert(b.ids['export-panel'].hidden);assert.equal(b.ids['export-json'].value,'');assert.equal(b.ids['print-area'].innerHTML,'');assert.deepStrictEqual(b.json('state.sessions'),before);assert.deepStrictEqual(b.json('state.diagnostic'),diagnostic);
});
check('Logout can invalidate a session when removal is blocked but replacement is available',()=>{
 const b=boot({sessionRemoveThrow:true});assert(!b.bootError);b.ids.logout.click();assert.equal(b.run('signedIn()'),false);assert.equal(b.sessionSaved[AUTH],'null');const c=guest({sessionSaved:b.sessionSaved});assert.equal(c.run('signedIn()'),false);
});
check('Complete session-storage failure still signs out in memory with an actionable message',()=>{
 const b=boot();b.config.sessionRemoveThrow=true;b.config.sessionWriteThrow=true;b.ids.logout.click();assert.equal(b.run('signedIn()'),false);assert(b.ids.app.innerHTML.includes('login-form'));assert(b.ids.app.innerHTML.includes('이 탭을 닫아'));assert(!b.ids.app.innerHTML.includes('teacher-nav'));
});
check('Expired in-memory session returns to login on the next render',()=>{
 const b=boot({loginRole:'teacher'});b.run('authSession.expiresAt=Date.now()-1;render()');assert.equal(b.run('signedIn()'),false);assert(b.ids.app.innerHTML.includes('login-form'));assert(b.ids['account-toolbar'].hidden);
});
check('Student cannot use teacher export, reset, page navigation or parent-print handlers',()=>{
 const b=boot(),before=b.json('state');b.ids['export-record'].click();b.ids.reset.click();b.run("teacherPage('report');prepareParentPrint()");assert.deepStrictEqual(b.json('state'),before);assert.equal(b.ids['export-json'].value,'');assert.equal(b.ids['print-area'].innerHTML,'');assert(b.ids['export-record'].hidden);assert(b.ids.reset.hidden);
});
check('Previously bound teacher actions cannot run after signing out and signing in as student',()=>{
 const b=boot({loginRole:'teacher'});b.click('teacher-page',{page:'report'});b.doc.querySelector('[data-report-field="parentMessage"]').value='QA';b.doc.querySelector('[data-report-field="parentMessage"]').trigger('input');const oldAction=b.nodes.find(n=>n.dataset.action==='confirm-report');b.ids.logout.click();b.loginAs('student');const before=b.json('state.teacher');oldAction.click();assert.deepStrictEqual(b.json('state.teacher'),before);assert.equal(b.run('state.role'),'student');
});
check('Host learning updates cannot switch the signed-in student to teacher',()=>{
 const b=boot(),incoming=b.json('state');incoming.role='teacher';incoming.teacherScreen='report';incoming.modifiedAt=new Date(Date.now()+1000).toISOString();incoming.stateRevision++;b.windowListeners['openai:set_globals']({detail:{widgetState:incoming}});assert.equal(b.run('state.role'),'student');assert(!b.ids.app.innerHTML.includes('data-report-field'));assert.equal(b.run("signedIn('student')"),true);
});
check('Host learning updates never authenticate a signed-out visitor',()=>{
 const b=guest(),incoming=b.json('state');incoming.role='teacher';incoming.modifiedAt=new Date(Date.now()+1000).toISOString();incoming.stateRevision++;b.windowListeners['openai:set_globals']({detail:{widgetState:incoming}});assert.equal(b.run('signedIn()'),false);assert(b.ids.app.innerHTML.includes('login-form'));assert.equal(b.ids['storage-status'].textContent,'');
});
check('Login credentials are absent from learning state, host exports and the session schema',()=>{
 const b=boot();const stored=JSON.parse(b.sessionSaved[AUTH]);assert.deepStrictEqual(Object.keys(stored).sort(),['expiresAt','role','username','version']);assert.equal(b.run("Object.hasOwn(state,'authSession')||Object.hasOwn(state,'password')"),false);b.loginAs('teacher');b.ids['export-record'].click();const exported=JSON.parse(b.ids['export-json'].value);assert.equal(exported.authSession,undefined);assert.equal(exported.password,undefined);assert.equal(exported.state.authSession,undefined);
});
const result={method:'Actual prototype JavaScript in Node VM with mocked DOM and blocked-storage cases; fixed test accounts only',source_sha256:crypto.createHash('sha256').update(fs.readFileSync(target)).digest('hex'),passed:checks.filter(c=>c.status==='PASS').length,failed:checks.filter(c=>c.status==='FAIL').length,checks};
const out=path.join(__dirname,'login');fs.mkdirSync(out,{recursive:true});fs.writeFileSync(path.join(out,'vm-results.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({passed:result.passed,failed:result.failed,failedChecks:checks.filter(c=>c.status==='FAIL')},null,2));if(result.failed)process.exitCode=1;
