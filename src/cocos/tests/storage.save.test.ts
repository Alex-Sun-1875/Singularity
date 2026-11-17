import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession} from '../assets/scripts/core/GameSession';
import {SaveStore,checksum,CAMPAIGN_SAVE_PREFIX,type KeyValueStore} from '../assets/scripts/features/persistence/common/SaveStore';
import {AutoSavePolicy} from '../assets/scripts/features/persistence/common/AutoSavePolicy';
const world={move:(p:any,d:any)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
class Memory implements KeyValueStore { data=new Map<string,string>();fail=false;truncate=false;getItem(k:string){return this.data.get(k)??null;}setItem(k:string,v:string){if(this.fail)throw new Error('disk full');this.data.set(k,this.truncate?v.slice(0,20):v);}}
test('dual slots restore the newest complete revision with rewards unchanged',()=>{const m=new Memory(),s=new SaveStore(m),g=new GameSession(7,world);assert.equal(s.write(g).ok,true);g.state.player.gold=20;g.state.receipts.reward=true;assert.equal(s.write(g).ok,true);const loaded=new SaveStore(m).load(world);assert.equal(loaded.session!.state.player.gold,20);assert.equal(loaded.session!.state.receipts.reward,true);assert.equal(m.data.size,2);});
test('a torn write leaves the previous complete slot and never marks session saved',()=>{const m=new Memory(),s=new SaveStore(m),g=new GameSession(7,world);s.write(g);g.state.player.gold=20;g.dirty=true;m.truncate=true;assert.equal(s.write(g).ok,false);assert.equal(g.dirty,true);const loaded=new SaveStore(m).load(world);assert.equal(loaded.session!.state.player.gold,0);assert.match(loaded.warning!,/保留/);const before=[...m.data];assert.equal(new SaveStore(m).write(g).ok,false);assert.deepEqual([...m.data],before);});
test('unknown schema and corrupt originals remain byte-for-byte until explicit new journey',()=>{const m=new Memory();m.data.set(CAMPAIGN_SAVE_PREFIX+'.a',JSON.stringify({version:99,payload:'future',hash:'x',revision:100}));m.data.set(CAMPAIGN_SAVE_PREFIX+'.b','{broken');const s=new SaveStore(m);assert.equal(s.load(world).session,null);const before=[...m.data];assert.equal(s.write(new GameSession(1,world)).ok,false);assert.deepEqual([...m.data],before);assert.equal(s.startFresh(new GameSession(2,world)).ok,true);assert.ok([...m.data.values()].includes('{broken'));assert.ok([...m.data.values()].includes(before[0][1]));assert.equal(new SaveStore(m).load(world).session!.state.seed,3);});
test('valid hash cannot legitimize a malformed or forged inventory snapshot',()=>{const m=new Memory(),g=new GameSession(7,world),bad=g.snapshot();bad.inventory.W02=1;const payload=JSON.stringify(bad);m.data.set(CAMPAIGN_SAVE_PREFIX+'.a',JSON.stringify({version:1,revision:1,payload,hash:checksum(payload)}));const s=new SaveStore(m);assert.equal(s.load(world).session,null);assert.equal(s.write(g).ok,false);});
test('failed backup preserves original slots and aborts explicit reset',()=>{const m=new Memory(),s=new SaveStore(m),g=new GameSession(7,world);s.write(g);s.write(g);const before=[...m.data];m.fail=true;assert.equal(s.startFresh(new GameSession(8,world)).ok,false);assert.deepEqual([...m.data],before);});
test('retry after a failed write durably saves the latest session in that single call',()=>{const m=new Memory(),s=new SaveStore(m),g=new GameSession(7,world);assert.ok(s.write(g).ok);m.fail=true;g.advance(.1,{x:1,z:0});assert.equal(s.write(g).ok,false);g.advance(.2,{x:1,z:0});const latest=g.snapshot();m.fail=false;assert.ok(s.write(g).ok);assert.equal(g.dirty,false);assert.deepEqual(new SaveStore(m).load(world).session!.snapshot(),latest);});
test('new journey owns the first verified commit even if its mirror write fails',()=>{class FailMirror extends Memory{writes=0;failAt=Infinity;override setItem(k:string,v:string){if(++this.writes===this.failAt)throw new Error('mirror full');super.setItem(k,v);}}const m=new FailMirror(),s=new SaveStore(m),old=new GameSession(7,world);assert.ok(s.write(old).ok);assert.ok(s.write(old).ok);m.failAt=m.writes+4;const fresh=new GameSession(99,world),result=s.startFresh(fresh);assert.equal(result.ok,true);assert.match(result.warning!,/新旅程|镜像/);assert.equal(new SaveStore(m).load(world).session!.state.seed,fresh.state.seed);assert.equal([...m.data.keys()].filter(k=>k.includes('backup')).length,2);});
test('periodic autosave commits dirty exploration every fifteen seconds and restores its latest position',()=>{
 const m=new Memory(),store=new SaveStore(m),game=new GameSession(7,world),policy=new AutoSavePolicy();let commits=0;
 for(let second=1;second<=60;second++){
  game.advance(.1,{x:1,z:0});policy.advance(1);
  if(policy.due(game.dirty)){const result=store.write(game);policy.committed(result.ok);assert.ok(result.ok);commits++;}
 }
 assert.equal(commits,4);assert.equal(game.dirty,false);
 assert.equal(new SaveStore(m).load(world).session!.state.player.x,game.state.player.x);
 policy.advance(60);assert.equal(policy.due(false),false);
});
test('continuous reward requests retain the first three-second deadline and a critical commit clears it',()=>{
 const policy=new AutoSavePolicy();
 for(let second=0;second<3;second++){
  assert.equal(policy.observe([{type:'reward'}]),false);assert.equal(policy.due(true),false);policy.advance(1);
 }
 assert.equal(policy.due(true),true);
 assert.equal(policy.observe([{type:'experience',levels:1},{type:'item'},{type:'journey_complete'}]),true);
 policy.committed(true);policy.advance(3);assert.equal(policy.due(true),false);
 assert.equal(policy.observe([{type:'experience',levels:0},{type:'attack'}]),false);
 policy.advance(3);assert.equal(policy.due(true),true);
});
test('failed autosave keeps dirty data and retries after two seconds with the newest state',()=>{
 const m=new Memory(),store=new SaveStore(m),game=new GameSession(7,world),policy=new AutoSavePolicy();
 assert.ok(store.write(game).ok);game.advance(.1,{x:1,z:0});policy.advance(15);assert.equal(policy.due(game.dirty),true);
 m.fail=true;policy.committed(store.write(game).ok);assert.equal(game.dirty,true);
 policy.advance(1);policy.observe([{type:'reward'}]);assert.equal(policy.due(game.dirty),false);
 game.advance(.1,{x:1,z:0});policy.advance(1);assert.equal(policy.due(game.dirty),true);
 m.fail=false;const result=store.write(game);policy.committed(result.ok);assert.ok(result.ok);
 assert.equal(game.dirty,false);assert.equal(new SaveStore(m).load(world).session!.state.player.x,game.state.player.x);
 // A lifecycle/manual save is allowed before any periodic deadline.
 game.advance(.1,{x:1,z:0});assert.equal(policy.due(game.dirty),false);
 policy.committed(store.write(game).ok);assert.equal(new SaveStore(m).load(world).session!.state.player.x,game.state.player.x);
});
