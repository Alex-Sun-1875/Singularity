import {test} from 'node:test';import assert from 'node:assert/strict';
import {CheckpointCompass} from '../assets/scripts/features/navigation/runtime/CheckpointCompass';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
test('compass chooses the nearest discovered checkpoint over physical open paths',()=>{
 const compass=new CheckpointCompass(AREAS),flags={'visited:S01':true,'visited:S01-T1':true,'checkpoint:S01':true,'checkpoint:S01-T1':true};
 const near=compass.find('S01',{x:0,z:-12},flags);
 assert.equal(near?.area,'S01');assert.ok(near!.distance<.01);
 const remote=compass.find('S01-T1',{x:0,z:-7},{'visited:S01':true,'visited:S01-T1':true,'checkpoint:S01':true});
 assert.equal(remote?.area,'S01');assert.ok(AREAS['S01-T1'].exits.some(e=>e.x===remote?.target.x&&e.z===remote?.target.z));
});
test('compass never invents a route through an undiscovered region',()=>{
 const compass=new CheckpointCompass(AREAS);
 assert.equal(compass.find('S10',{x:0,z:0},{'visited:S10':true,'checkpoint:S01':true}),null);
});
