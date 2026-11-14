import test from 'node:test';
import assert from 'node:assert/strict';
import {TapLogin,type TapLoginAPI} from '../assets/scripts/platform/TapLogin';
const config={timeoutMs:30};
function fixture(){
 let logins=0,requests=0,checks=0,platformValid=true;
 const api:TapLoginAPI&{request:()=>void}={login:o=>{logins++;o.success({code:'one-time-code'});},checkSession:o=>{checks++;platformValid?o.success():o.fail({errno:1});},request:()=>{requests++;throw new Error('Platform login must not contact a custom auth service');}};
 const auth=new TapLogin(api,true,config);
 return {auth,api,get logins(){return logins;},get requests(){return requests;},get checks(){return checks;},invalidate:()=>{platformValid=false;}};
}

test('minigame requires real platform login APIs; browser preview and guest tests stay explicit',async()=>{
 for(const api of [undefined,{login:()=>{}},{checkSession:()=>{}}]){
  const missing=new TapLogin(api,true,config);assert.equal(await missing.ensure(),false);assert.equal(missing.ready,false);assert.equal(missing.state.error,'PLATFORM_UNAVAILABLE');
 }
 const preview=new TapLogin(undefined,false,config);assert.equal(await preview.ensure(),true);assert.equal(preview.state.status,'preview');
 const guest=new TapLogin(undefined,false,{...config,guestTest:true});assert.equal(await guest.ensure(),true);assert.equal(guest.state.status,'guest');
});
test('concurrent login coalesces without HTTP or retaining the temporary code as an account',async()=>{
 const f=fixture();assert.deepEqual(await Promise.all([f.auth.ensure(),f.auth.ensure()]),[true,true]);assert.equal(f.logins,1);assert.equal(f.auth.ready,true);assert.equal(f.auth.state.status,'platform-ready');
 assert.equal(await f.auth.ensure(),true);assert.equal(f.logins,1);
 assert.equal(await f.auth.ensure(true),true);assert.equal(f.checks,1);assert.equal(f.logins,1);assert.equal(f.requests,0);
 assert.ok(!JSON.stringify(f.auth).includes('one-time-code'));assert.ok(!('session' in f.auth));
});
test('foreground checks suspend readiness, renew invalid platform sessions and preserve failure recovery',async()=>{
 const f=fixture();await f.auth.ensure();let checked:(()=>void)|undefined;const original=f.api.checkSession;
 f.api.checkSession=o=>{checked=o.success;};const resuming=f.auth.ensure(true);assert.equal(f.auth.ready,false);assert.equal(f.auth.state.status,'checking');checked!();assert.equal(await resuming,true);assert.equal(f.auth.ready,true);
 f.api.checkSession=original;f.invalidate();assert.equal(await f.auth.ensure(true),true);assert.equal(f.logins,2);
 const login=f.api.login;f.api.login=o=>o.fail({errno:1});assert.equal(await f.auth.ensure(true),false);assert.equal(f.auth.ready,false);assert.equal(f.auth.state.error,'PLATFORM_FAILED');
 f.api.login=login;assert.equal(await f.auth.ensure(),true);assert.equal(f.logins,3);assert.equal(f.requests,0);
});
test('empty or malformed platform credentials and failed callbacks never enable entry',async()=>{
 const f=fixture();for(const code of [undefined,'','   ',12]){
  f.api.login=o=>o.success({code:code as string});assert.equal(await f.auth.ensure(),false);assert.equal(f.auth.ready,false);assert.equal(f.auth.state.error,'EMPTY_CODE');
 }
 f.api.login=o=>o.fail({errno:1});assert.equal(await f.auth.ensure(),false);assert.equal(f.auth.state.error,'PLATFORM_FAILED');
 f.api.login=o=>o.success({code:'fresh-platform-code'});assert.equal(await f.auth.ensure(),true);assert.equal(f.requests,0);
});
test('timeout and disposal ignore late platform callbacks and cannot restore readiness',async()=>{
 const f=fixture();let late:((r:{code?:string})=>void)|undefined;
 f.api.login=o=>{late=o.success;};assert.equal(await f.auth.ensure(),false);assert.equal(f.auth.state.error,'TIMEOUT');late!({code:'late'});assert.equal(f.auth.ready,false);
 const pending=f.auth.ensure();f.auth.dispose();assert.equal(await pending,false);late!({code:'late'});assert.equal(f.auth.ready,false);assert.equal(await f.auth.ensure(),false);assert.equal(f.requests,0);
 const resumed=fixture();await resumed.auth.ensure();let check:(()=>void)|undefined;resumed.api.checkSession=o=>{check=o.success;};const waiting=resumed.auth.ensure(true);resumed.auth.dispose();assert.equal(await waiting,false);check!();assert.equal(resumed.auth.ready,false);assert.equal(resumed.logins,1);
});
