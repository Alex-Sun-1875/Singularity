import {test} from 'node:test';import assert from 'node:assert/strict';
import {Navigation} from '../assets/scripts/features/navigation/runtime/Navigation';
import {GameSession} from '../assets/scripts/core/GameSession';
import type {AreaDef,Point,WorldQuery} from '../assets/scripts/core/Contracts';
import {getArea,AREAS} from '../assets/scripts/features/world/data/WorldData';
import {journeyGuidance} from '../assets/scripts/features/journey/common/JourneyGuide';
import {JOURNEY_TASKS} from '../assets/scripts/features/journey/data/ChapterJourney';
import {Automation} from '../assets/scripts/features/automation/common/Automation';
import {availableRoutes,enemyApproachPath} from '../assets/scripts/features/automation/common/AutomationRoute';
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
test('shared regional routes preserve one-way exits and immediately reflect level and door changes',()=>{
 const exit=(id:string,to:string,extra:Partial<AreaDef['exits'][number]>={})=>({id,to,label:id,x:0,z:0,entry:{x:0,z:0},...extra});
 const areas:Record<string,AreaDef>={
  S01:{...getArea('S01'),exits:[exit('level','S02',{requiredLevel:5}),exit('door','S03',{requires:'open'})]},
  S02:{...getArea('S02'),exits:[exit('onward','S04')]},
  S03:{...getArea('S03'),exits:[exit('alternate','S04')]},
  S04:{...getArea('S04'),exits:[]},
 };
 const game=new GameSession(1,{move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0});
 assert.deepEqual([...availableRoutes(game,areas).keys()],['S01']);
 game.state.progression.level=5;
 assert.deepEqual(availableRoutes(game,areas).get('S04')!.map(e=>e.id),['level','onward']);
 game.state.progression.level=1;game.state.flags.open=true;
 assert.deepEqual(availableRoutes(game,areas).get('S04')!.map(e=>e.id),['door','alternate']);
 game.state.area='S04';assert.equal(availableRoutes(game,areas).has('S01'),false);
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

test('H14 guidance skips the embedded nearest monster and retains genuine blocked results',()=>{
 const area=getArea('H14'),nav=new Navigation(area.width,area.depth,[...area.obstacles,{kind:'rock',x:18.091021411510045,z:-31.96191826854661,width:1.3,depth:1.1,height:1}]);
 const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:(a,b)=>nav.visible(a,b),height:()=>0,path:(a,b)=>nav.path(a,b)};
 const game=new GameSession(1,world);game.enter(area);game.state.progression.level=18;
 for(const task of JOURNEY_TASKS.filter(t=>t.chapter===2))game.state.receipts[`journey:task:${task.id}`]=true;
 const embedded=game.state.enemies.find(e=>e.id==='hunt-H14-0-2')!,other=game.state.enemies.find(e=>e.id==='hunt-H14-1-1')!;
 Object.assign(game.state.player,{x:15,z:-33});for(const enemy of game.state.enemies)if(enemy!==embedded&&enemy!==other)enemy.hp=0;
 assert.equal(nav.blocked(embedded,0),true);assert.ok(nav.path(game.state.player,other).length);
 const guide=journeyGuidance(game,AREAS,world,undefined,'hunt',2)!;
 assert.equal(guide.blocked,false);assert.equal(guide.targetId,other.id);
 other.hp=0;
 assert.equal(journeyGuidance(game,AREAS,world,undefined,'hunt',2)!.blocked,true,'a truly inaccessible remaining monster stays blocked');
 embedded.x=21;
 const recovered=journeyGuidance(game,AREAS,world,undefined,'hunt',2)!;
 assert.equal(recovered.blocked,false);assert.equal(recovered.targetId,embedded.id,'moving targets are rechecked');
});

test('automation walks to a firing position and lands real bow damage without crossing a low barrier',()=>{
 const area:AreaDef={...getArea('H14'),id:'navigation-range',width:30,depth:30,spawn:{x:-9,z:0},enemies:[{id:'prey',kind:'raider',x:4,z:0,respawnSeconds:28}],objects:[],exits:[],buildings:[],obstacles:[{x:0,z:0,width:1,depth:30,height:.4}]};
 const nav=new Navigation(area.width,area.depth,area.obstacles);
 const world:WorldQuery={move:(from,delta,radius)=>{
  const p={x:from.x,z:from.z},steps=Math.max(1,Math.ceil(Math.hypot(delta.x,delta.z)/.15));
  for(let i=0;i<steps;i++){const x=p.x+delta.x/steps,z=p.z+delta.z/steps;if(!nav.blockedAt(x,p.z,radius))p.x=x;if(!nav.blockedAt(p.x,z,radius))p.z=z;}return p;
 },visible:()=>true,height:()=>0,path:(a,b)=>nav.path(a,b)};
 const game=new GameSession(1,world);game.enter(area);assert.ok(game.equip('W07'));game.setMovementSpeed(6.5);
 const enemy=game.state.enemies[0],hp=enemy.hp;enemy.phase='recovery';enemy.phaseTime=60;
 assert.deepEqual(nav.path(game.state.player,enemy),[]);
 const approach=enemyApproachPath(game,world,enemy);assert.ok(approach.length>1);
 const endpoint=approach[approach.length-1];assert.ok(endpoint.x<-.82);assert.ok(Math.hypot(endpoint.x-enemy.x,endpoint.z-enemy.z)<game.basicAttackProfile().rangeMetres);
 const auto=new Automation();auto.setMode('idle');
 for(let i=0;i<300&&enemy.hp===hp;i++){const step=auto.update(game,world,{[area.id]:area},.05);game.advance(.05,step.input);}
 assert.equal(auto.paused,false);assert.ok(game.state.player.x>-9&&game.state.player.x<-.82);assert.ok(enemy.hp<hp,'ordinary bow projectile damages the target from the reachable side');
 // The same footprint as a tall wall must still block both approach and attack.
 const opaque={...world,visible:(a:Point,b:Point)=>nav.visible(a,b)};
 assert.deepEqual(enemyApproachPath(game,opaque,enemy),[]);
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
