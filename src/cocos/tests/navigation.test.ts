import {GameSession} from '../assets/scripts/core/GameSession';
import {getArea} from '../assets/scripts/features/world/data/WorldData';
import type {WorldQuery} from '../assets/scripts/core/Contracts';
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

test('waypoints require reaching an authored safe point; old checkpoint activations migrate once',()=>{
 const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0},game=new GameSession(1,world),town=getArea('S01');
 game.enter(town,{x:40,z:-35});
 assert.equal(game.state.flags['visited:S01'],true);assert.equal(game.state.flags['waypoint:S01'],undefined);
 assert.equal(game.fastTravelAvailability(town).available,false);
 game.enter(town,town.objects.find(o=>o.action==='checkpoint'));
 assert.equal(game.state.flags['waypoint:S01'],true);
 const old=game.snapshot();delete old.receipts['waypoint:v1'];delete old.flags['waypoint:S01'];
 const restored=GameSession.restore(old,world);assert.equal(restored.state.flags['waypoint:S01'],true);assert.equal(restored.state.receipts['waypoint:v1'],true);
 const unknown=getArea('S02');restored.state.flags['visited:S02']=true;assert.equal(restored.fastTravelAvailability(unknown).available,false);
});

test('map travel preserves resources, encounters, merchant stock and quest progress, including same-area return',()=>{
 const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0},game=new GameSession(2,world),town=getArea('S01'),pass=getArea('S04');
 game.enter(town);game.enter(pass);game.state.enemies[0].hp=17;game.enter(town,{x:35,z:-32});
 game.state.player.hp=37;game.state.player.focus=12;game.state.player.healthPotions=0;game.state.cooldowns.consumable=3;
 const before=game.snapshot();assert.equal(game.fastTravelAvailability(pass).available,true);assert.equal(game.fastTravel(pass),true);
 assert.equal(game.fastTravel(pass),false,'a second request cannot start during loading');
 game.enter(pass,pass.objects.find(o=>o.action==='checkpoint'),true);game.completeFastTravel(true);
 assert.equal(game.state.player.hp,37);assert.equal(game.state.player.focus,12);assert.equal(game.state.player.healthPotions,0);assert.equal(game.state.cooldowns.consumable,3);
 assert.equal(game.state.enemies[0].hp,17);assert.deepEqual(game.state.merchantStock,before.merchantStock);assert.deepEqual(game.state.receipts,before.receipts);assert.deepEqual(game.state.progression,before.progression);
 assert.equal(game.fastTravelAvailability(pass).available,false,'already beside the rune');
 game.state.player.x=30;game.state.player.z=-35;assert.equal(game.fastTravelAvailability(pass).available,true);
 assert.equal(game.fastTravel(pass),true);game.enter(pass,pass.objects.find(o=>o.action==='checkpoint'),true);game.completeFastTravel(true);assert.equal(game.state.enemies[0].hp,17);
});

test('map travel rejects combat, projectiles and unfinished interactions; failure restores the whole snapshot',()=>{
 const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0},game=new GameSession(3,world),town=getArea('S01');
 game.enter(town,{x:30,z:-30});game.state.flags['waypoint:S01']=true;
 const ready=()=>game.fastTravelAvailability(town).available;assert.equal(ready(),true);
 game.state.dialogue={id:'test',speaker:'test',text:'test',options:[]} as any;assert.equal(ready(),false);game.state.dialogue=null;
 game.state.projectiles.push({owner:'enemy',x:29,z:-30,remaining:1} as any);assert.equal(ready(),false);game.state.projectiles=[];
 game.state.enemies.push({id:'nearby',x:29,z:-30,hp:10,kind:'raider',phase:'approach'} as any);assert.equal(ready(),false);game.state.enemies=[];
 const before=game.snapshot();assert.equal(game.fastTravel(town),true);game.enter(town,town.spawn,true);game.completeFastTravel(false);assert.deepEqual(game.snapshot(),before);assert.equal(ready(),true);
});
