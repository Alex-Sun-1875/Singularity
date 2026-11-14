import {test} from 'node:test';
import assert from 'node:assert/strict';
import {TouchOwnership} from '../assets/scripts/shared/input/TouchOwnership';
test('touch ownership stays with the starting control and cancels without firing',()=>{
 const input=new TouchOwnership();
 assert.equal(input.begin(1,'move'),true);
 assert.equal(input.begin(2,'combat0'),true);
 assert.equal(input.begin(3,'attack'),false);
 input.move(1,4,3); assert.ok(Math.abs(input.vector().x-.8)<1e-12&&Math.abs(input.vector().z-.6)<1e-12);
 assert.equal(input.end(2,true),undefined);
 assert.ok(Math.abs(input.vector().x-.8)<1e-12&&Math.abs(input.vector().z-.6)<1e-12);
 input.clear(); assert.deepEqual(input.vector(),{x:0,z:0});
 assert.equal(input.end(1,false),undefined);
});
test('release only submits the action owned by the same pointer once',()=>{
 const input=new TouchOwnership(); input.begin(2,'combat0');
 assert.equal(input.end(2,false),'combat0'); assert.equal(input.end(2,false),undefined);
});
