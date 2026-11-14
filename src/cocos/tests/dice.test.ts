import test from 'node:test';
import assert from 'node:assert/strict';

// Dynamic import yields a clear feature assertion before the new module exists.
let rules:any={};try{rules=require('../assets/scripts/features/progression/common/SkillChecks');}catch{}
const context={mode:'normal',modifiers:[{label:'魅力',value:2},{label:'熟练',value:2}],helpDie:false,helpLabel:null};
test('D20 rules expose real roll resolution',()=>assert.equal(typeof rules.resolveCheckRoll,'function','D20 resolver must exist'));
test('D20 plus modifiers meets the DC inclusively and exposes every term',()=>{
 assert.equal(typeof rules.resolveCheckRoll,'function');const r=rules.resolveCheckRoll([10],14,context);
 assert.deepEqual({kept:r.kept,bonus:r.bonus,total:r.total,success:r.success},{kept:10,bonus:4,total:14,success:true});
 assert.equal(rules.resolveCheckRoll([9],14,context).success,false);
});
test('natural1 fails despite bonuses and natural20 succeeds despite impossible DC',()=>{
 assert.equal(typeof rules.resolveCheckRoll,'function');assert.equal(rules.resolveCheckRoll([1],2,context).critical,'failure');assert.equal(rules.resolveCheckRoll([1],2,context).success,false);assert.equal(rules.resolveCheckRoll([20],40,context).critical,'success');assert.equal(rules.resolveCheckRoll([20],40,context).success,true);
});
test('advantage keeps high, disadvantage keeps low, opposing sources cancel',()=>{
 assert.equal(typeof rules.resolveCheckRoll,'function');assert.equal(rules.resolveCheckRoll([4,17],14,{...context,mode:'advantage'}).kept,17);assert.equal(rules.resolveCheckRoll([4,17],14,{...context,mode:'disadvantage'}).kept,4);
 assert.equal(rules.rollMode(true,true),'normal');assert.equal(rules.rollMode(true,false),'advantage');assert.equal(rules.rollMode(false,true),'disadvantage');
});
test('assistance is a visible1d4, and invalid faces cannot be used as results',()=>{
 assert.equal(typeof rules.resolveCheckRoll,'function');const r=rules.resolveCheckRoll([8],14,{...context,helpDie:true,helpLabel:'指导'},1,2);assert.equal(r.assist,2);assert.equal(r.total,14);assert.equal(r.success,true);
 for(const faces of [[0],[21],[1.5],[NaN],[2,3]])assert.throws(()=>rules.resolveCheckRoll(faces,14,context));
 assert.throws(()=>rules.resolveCheckRoll([8],14,{...context,helpDie:true},1,5));
});
test('seeded attempts are stable across reloads and separate by source and attempt',()=>{
 assert.equal(typeof rules.drawCheckRoll,'function');const a=rules.drawCheckRoll(371,'inn-lockbox',1,14,context);assert.deepEqual(a,rules.drawCheckRoll(371,'inn-lockbox',1,14,context));
 const outputs=new Set(Array.from({length:40},(_,i)=>rules.drawCheckRoll(371,'inn-lockbox',i+1,14,context).kept));assert.ok(outputs.size>12,'rolls must vary across legitimate inspiration attempts');
});
test('shown success probability uses actual natural20/1 and dice mode',()=>{
 assert.equal(typeof rules.checkChance,'function');assert.equal(rules.checkChance(14,context),.55);assert.ok(Math.abs(rules.checkChance(14,{...context,mode:'advantage'})-.7975)<1e-10);assert.ok(Math.abs(rules.checkChance(14,{...context,mode:'disadvantage'})-.3025)<1e-10);assert.equal(rules.checkChance(40,context),.05);
});
