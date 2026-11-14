import test from 'node:test';
import assert from 'node:assert/strict';
import {AREAS,getArea} from '../assets/scripts/features/world/data/WorldData';
import {getTerrain} from '../assets/scripts/features/world/runtime/Terrain';
import type {Point} from '../assets/scripts/core/Contracts';
import {Navigation} from '../assets/scripts/features/navigation/runtime/Navigation';

test('mapped high ground and the echo cave dry ramp have real continuous elevation',()=>{
  const cave=getTerrain(getArea('U1-02'));
  assert.equal(cave.height({x:-30,z:-24}),0);
  assert.equal(cave.height({x:12,z:-24}),5);
  const ramp=cave.ramps.find(r=>r.id==='u102-dry-ramp')!;
  assert.ok(ramp);
  assert.ok(cave.height(getArea('U1-02').objects.find(o=>o.id==='u102-ramp')!)>1);
  assert.ok(cave.height(ramp.end)-cave.height(ramp.start)>=4.9);
  for(const id of ['S04','S08','S11','S13','S17']){
    const terrain=getTerrain(getArea(id));
    assert.ok(terrain.ramps.some(r=>r.rise>=2.5),`${id} has visible landscape elevation`);
  }
});

test('stonebridge, the south landing and the broken tower bridge have actual water crossings',()=>{
  for(const [id,material]of [['S01','stone'],['S02','wood'],['S11','wood']] as const){
    const terrain=getTerrain(getArea(id));
    assert.ok(terrain.waters.length>0,`${id} has real water geometry`);
    const bridge=terrain.bridges.find(b=>b.material===material)!;
    assert.ok(bridge,`${id} has an intact bridge`);
    assert.ok(terrain.waters.some(w=>Math.abs(bridge.x-w.x)<w.width/2&&Math.abs(bridge.z-w.z)<w.depth/2));
    assert.ok(bridge.deckHeight-terrain.waters[0].y>=.5,'deck is visibly above water');
    const half=(bridge.axis==='x'?bridge.width:bridge.depth)/2;
    for(let d=-half;d<=half;d+=.5){
      const point=bridge.axis==='x'?{x:bridge.x+d,z:bridge.z}:{x:bridge.x,z:bridge.z+d};
      assert.ok(Math.abs(terrain.height(point)-bridge.deckHeight)<.001,`${bridge.id} deck meets its actual walk surface`);
      assert.ok(!terrain.barriers.some(b=>Math.abs(point.x-b.x)<b.width/2+.42&&Math.abs(point.z-b.z)<b.depth/2+.42),`${bridge.id} has an unobstructed crossing`);
    }
  }
  assert.ok(getTerrain(getArea('S11')).brokenBridges.some(b=>b.gapWidth>=5),'the old broken span remains visibly distinct from the complete bridge');
});

test('every terrain slope is at most35degrees including water banks and bridge approaches',()=>{
  const max=Math.tan(35*Math.PI/180),epsilon=.1;
  for(const area of Object.values(AREAS)){
    const terrain=getTerrain(area);
    for(let x=-area.width/2+1;x<area.width/2;x+=1.5)for(let z=-area.depth/2+1;z<area.depth/2;z+=1.5){
      const dx=(terrain.height({x:x+epsilon,z})-terrain.height({x:x-epsilon,z}))/(2*epsilon);
      const dz=(terrain.height({x,z:z+epsilon})-terrain.height({x,z:z-epsilon}))/(2*epsilon);
      assert.ok(Number.isFinite(dx)&&Number.isFinite(dz)&&Math.hypot(dx,dz)<=max+.001,`${area.id} too steep at${x},${z}: ${Math.atan(Math.hypot(dx,dz))*180/Math.PI}degrees`);
    }
    for(const ramp of terrain.ramps)assert.ok(1.5*ramp.rise/Math.hypot(ramp.end.x-ramp.start.x,ramp.end.z-ramp.start.z)<=max);
  }
});

test('terrain water barriers preserve real walking approaches to every object, exit and return entry',()=>{
  const cached=new Map<string,{nav:Navigation;seen:Set<string>}>();
  for(const area of Object.values(AREAS)){
    const terrain=getTerrain(area),nav=new Navigation(area.width,area.depth,[...area.obstacles,...terrain.barriers]);
    for(const ramp of terrain.ramps){
      assert.ok(!nav.blocked(ramp.start,.6)&&!nav.blocked(ramp.end,.6),`${area.id}/${ramp.id} has dry unobstructed ramp endpoints`);
      assert.ok(nav.path(ramp.start,ramp.end).length,`${area.id}/${ramp.id} has a physical route between its levels`);
    }
    const start={x:Math.round(area.spawn.x),z:Math.round(area.spawn.z)},queue=[start],seen=new Set([`${start.x},${start.z}`]);
    assert.ok(!nav.blocked(start,.6),`${area.id} terrain preserves its spawn`);
    for(let i=0;i<queue.length;i++)for(const [dx,dz]of [[1,0],[-1,0],[0,1],[0,-1]]){
      const current=queue[i],point={x:current.x+dx,z:current.z+dz},key=`${point.x},${point.z}`;
      if(seen.has(key)||nav.blocked(point,.6))continue;
      assert.ok(Math.abs(terrain.height(point)-terrain.height(current))<=Math.tan(35*Math.PI/180)+.001,`${area.id} step is too steep`);
      seen.add(key);queue.push(point);
    }
    cached.set(area.id,{nav,seen});
    for(const point of [...area.objects,...area.exits,...area.enemies]){
      assert.ok(!nav.blocked(point,.6),`${area.id}/${point.id} is on dry land or an intact bridge`);
      assert.ok(seen.has(`${Math.round(point.x)},${Math.round(point.z)}`),`${area.id}/${point.id} remains reachable after terrain water is introduced`);
    }
  }
  for(const area of Object.values(AREAS))for(const exit of area.exits){
    const {nav,seen}=cached.get(exit.to)!;
    assert.ok(!nav.blocked(exit.entry,.6),`${exit.id} return landing is dry`);
    assert.ok(seen.has(`${Math.round(exit.entry.x)},${Math.round(exit.entry.z)}`),`${exit.id} can walk inward from its reciprocal landing`);
  }
});
