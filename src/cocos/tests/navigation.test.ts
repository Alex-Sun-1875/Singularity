import {test} from 'node:test';import assert from 'node:assert/strict';
import {Navigation} from '../assets/scripts/features/navigation/runtime/Navigation';
test('navigation routes around the physical wall and respects both sides of the door',()=>{
 const nav=new Navigation(30,30,[{x:0,z:0,width:2,depth:18,height:3}]);
 const path=nav.path({x:-5,z:0},{x:5,z:0});assert.ok(path.length>2);
 for(let i=1;i<path.length;i++)assert.ok(nav.visible(path[i-1],path[i],.4));
 assert.ok(path.some(p=>Math.abs(p.z)>9.4));
 assert.equal(nav.visible({x:-5,z:0},{x:5,z:0},.4),false);
});
test('unreachable destinations return no invented connection',()=>{
 const nav=new Navigation(20,20,[{x:0,z:0,width:1,depth:22,height:3}]);
 assert.deepEqual(nav.path({x:-5,z:0},{x:5,z:0}),[]);
});
test('a free position beside a bench connects to reachable grid cells',()=>{
 const nav=new Navigation(36,32,[{x:-5,z:-2,width:4,depth:.7,height:.5}]);
 const from={x:-2.30559,z:-2.2208},to={x:-5,z:0};
 assert.equal(nav.blocked(from),false);const path=nav.path(from,to);assert.ok(path.length>1);
 for(let i=1;i<path.length;i++)assert.ok(nav.visible(path[i-1],path[i],.42));
});
test('a real radius .32 actor can leave a narrow clearance buffer without teleporting',()=>{
 const nav=new Navigation(20,20,[{x:0,z:0,width:2,depth:4,height:3}]);
 const a={x:-1.35,z:0},b={x:-4,z:4};assert.equal(nav.blocked(a,.32),false);
 const route=nav.path(a,b);assert.ok(route.length>1);assert.deepEqual(route[0],a);
 for(let i=1;i<route.length;i++)assert.ok(nav.visible(route[i-1],route[i],.32));
});
