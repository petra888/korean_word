// Node VM + mocked DOM: behavioral checks only, not browser or server verification.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const target=process.argv[2]||path.resolve(__dirname,'../../../prototype/pilot-flow.html');
let html;function setTarget(p){html=fs.readFileSync(p,'utf8');}setTarget(target);
function boot(config={}){
const payload=html.match(/<script type="application\/json" id="curriculum-data">([\s\S]+?)<\/script>/)[1],source=html.match(/<script>\n([\s\S]+?)<\/script>/)[1];
const decode=s=>String(s).replace(/&lt;/g,'<').replace(/&gt;/g,'>').replace(/&quot;/g,'"').replace(/&#39;/g,"'").replace(/&amp;/g,'&');
const ids={},saved={...(config.saved||{})},sessionSaved={...(config.sessionSaved||{})},windowListeners={};let nodes=[],hostWrites=0,printCalls=0; const writes=[],removed=[];
class El{
  constructor(id='',attrs='',text=''){this.id=id;this.textContent=text;this.value='';this.checked=false;this.tagName='BUTTON';this.dataset={};this.listeners={};this.attrs={};this.classList={toggle(){},add(){},remove(){}};for(const m of attrs.matchAll(/([\w-]+)="([^"]*)"/g)){this.attrs[m[1]]=decode(m[2]);if(m[1].startsWith('data-'))this.dataset[m[1].slice(5).replace(/-([a-z])/g,(_,x)=>x.toUpperCase())]=decode(m[2]);}this.disabled=/\bdisabled\b/.test(attrs);this.checked=/\bchecked\b/.test(attrs);this.value=this.attrs.value||'';this.type=this.attrs.type||'';}
  get innerHTML(){return this._html||'';}
  set innerHTML(v){this._html=v;nodes=this.id==='app'?[]:nodes.filter(n=>n.owner!==this.id);for(const m of v.matchAll(/<(button|textarea|select)\b([^>]*)>([\s\S]*?)<\/\1>|<(input)\b([^>]*)>/g)){const tag=m[1]||m[4],el=new El('',m[2]||m[5],decode(m[3]||''));el.tagName=tag.toUpperCase();el.id=el.attrs.id||'';el.owner=this.id;if(tag==='textarea')el.value=decode(m[3]||'');if(tag==='select'){const options=[...(m[3]||'').matchAll(/<option\b([^>]*)>([\s\S]*?)<\/option>/g)],op=options.find(o=>/\bselected\b/.test(o[1]))||options[0];if(op)el.value=decode(op[1].match(/value="([^"]*)"/)?.[1]??op[2]);}nodes.push(el);}}
  addEventListener(name,fn){this.listeners[name]=fn;}getAttribute(n){return this.attrs[n];}setAttribute(n,v){this.attrs[n]=v;}focus(){}select(){}scrollIntoView(){}remove(){}trigger(name){this.listeners[name]?.({target:this,currentTarget:this,preventDefault(){}});}click(){if(!this.disabled)this.trigger('click');}
}
for(const m of html.matchAll(/\bid="([^"]+)"/g))ids[m[1]]??=new El(m[1]);ids['curriculum-data'].textContent=payload;
function query(sel){if(sel.startsWith('#'))return [doc.getElementById(sel.slice(1))];const ms=[...sel.matchAll(/\[([\w-]+)(?:="([^"]*)")?\]/g)];return ms.length?nodes.filter(n=>ms.every(m=>Object.hasOwn(n.attrs,m[1])&&(m[2]===undefined||n.attrs[m[1]]===m[2]))):[];}
const doc={getElementById(id){return nodes.find(n=>n.id===id)||(ids[id]??=new El(id));},querySelectorAll:query,querySelector(s){return query(s)[0]||null;},documentElement:{},body:{appendChild(){}},createElement(){return new El();}};
const win={scrollTo(){},confirm(){return config.confirm!==false},print(){printCalls++},addEventListener(n,cb){windowListeners[n]=cb},openai:config.host||null};
const storage={getItem(k){if(config.readThrow)throw new Error('SecurityError');return saved[k]||null},setItem(k,v){writes.push({key:k,value:v});if(config.writeThrow)throw new Error('QuotaExceededError');saved[k]=v},removeItem(k){if(config.removeThrow)throw new Error('SecurityError');removed.push(k);delete saved[k]}};
const sessionStorage={getItem(k){if(config.sessionReadThrow)throw new Error('SecurityError');return sessionSaved[k]||null},setItem(k,v){if(config.sessionWriteThrow)throw new Error('QuotaExceededError');sessionSaved[k]=v},removeItem(k){if(config.sessionRemoveThrow)throw new Error('SecurityError');delete sessionSaved[k]}};
const ctx=vm.createContext({document:doc,window:win,localStorage:storage,sessionStorage,console,Date,Intl,Math,Blob,URL,setTimeout});let bootError=null;try{vm.runInContext(source,ctx)}catch(e){bootError={name:e.name,message:e.message,stack:e.stack}}
const run=c=>vm.runInContext(c,ctx),json=c=>JSON.parse(run(`JSON.stringify(${c})`)),action=(a,f={})=>nodes.find(n=>n.dataset.action===a&&Object.entries(f).every(([k,v])=>n.dataset[k]===v));
function click(a,f){const n=action(a,f);assert(n,'missing '+a);assert(!n.disabled,'disabled '+a);n.click();}const choose=option=>click('option',{option}),checks=[];
function check(name,fn){fn();checks.push({name,status:'PASS'});}
function loginAs(role){if(run("typeof signIn!=='function'")){ids[role+'-tab'].click();return;}if(run(`signedIn(${JSON.stringify(role)})`))return;if(run('signedIn()'))ids.logout.click();const button=nodes.find(n=>n.dataset.loginRole===role);assert(button,'missing login role '+role);button.click();doc.getElementById('login-id').value=role==='teacher'?'test2':'test1';doc.getElementById('login-password').value=role==='teacher'?'test2':'test1';doc.getElementById('login-form').trigger('submit');assert(run(`signedIn(${JSON.stringify(role)})`));}
if(!bootError&&config.autoLogin!==false&&run("typeof signIn==='function'"))try{loginAs(config.loginRole||'student');}catch(e){bootError={name:e.name,message:e.message,stack:e.stack};}
return {run,json,click,choose,loginAs,ids,saved,sessionSaved,windowListeners,writes,removed,config,doc,ctx,win,get nodes(){return nodes},get printCalls(){return printCalls},bootError};
}

module.exports={boot,setTarget,target,readHTML:()=>html};
