import test from 'node:test';
import assert from 'node:assert/strict';
import {TapUpdates,type TapUpdateManager} from '../assets/scripts/platform/TapUpdates';
function fixture(){let check:(result:{hasUpdate:boolean})=>void=()=>{},ready=()=>{},fail=()=>{},applied=0,throws=false;const manager:TapUpdateManager={onCheckForUpdate:fn=>{check=fn;},onUpdateReady:fn=>{ready=fn;},onUpdateFailed:fn=>{fail=fn;},applyUpdate:()=>{if(throws)throw new Error('restart failed');applied++;}};const updates=new TapUpdates({getUpdateManager:()=>manager});return {updates,check:(value:boolean)=>check({hasUpdate:value}),ready:()=>ready(),fail:()=>fail(),get applied(){return applied;},throwOnApply:()=>{throws=true;}};}
test('updates wait for the downloaded package and a successful save; postpone and resume are explicit',()=>{
 const f=fixture();assert.equal(f.updates.apply(()=>true),false);f.check(true);assert.equal(f.updates.status,'available');assert.equal(f.updates.apply(()=>true),false);
 f.ready();assert.equal(f.updates.promptPending,true);assert.equal(f.updates.apply(()=>false),false);assert.equal(f.applied,0);assert.match(f.updates.message,/保存失败/);
 f.updates.defer();assert.equal(f.updates.ready,true);assert.equal(f.updates.promptPending,false);f.updates.requestPrompt();assert.equal(f.updates.promptPending,true);
 assert.equal(f.updates.apply(()=>true),true);assert.equal(f.applied,1);assert.equal(f.updates.status,'applying');assert.equal(f.updates.apply(()=>true),false);
});
test('unsupported, failed download, restart failure and destroyed scene stay recoverable',()=>{
 assert.equal(new TapUpdates(undefined).status,'unsupported');const f=fixture();f.fail();assert.equal(f.updates.status,'failed');assert.equal(f.updates.apply(()=>true),false);f.ready();f.throwOnApply();assert.equal(f.updates.apply(()=>true),false);assert.equal(f.updates.ready,true);
 f.updates.dispose();f.fail();assert.equal(f.updates.ready,true);assert.equal(f.updates.apply(()=>true),false);
});
