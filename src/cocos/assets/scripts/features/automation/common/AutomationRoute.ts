import type {AreaDef,ExitDef,Point,WorldQuery} from '../../../core/Contracts';
import type {EnemyState,GameSession} from '../../../core/GameSession';
import {enemyHurtRadius} from '../../combat/common/EnemyCombat';
import {playableArea} from '../../journey/data/ChapterJourney';
import {journeyText as text} from '../../journey/locales';

export interface NavigationBlockage {code:'level'|'prerequisite'|'unreleased'|'route'|'path'|'stuck';summary:string;reason:string;hint:string}
export const navigationBlockageText=(blockage:NavigationBlockage)=>`${blockage.reason}\n${blockage.hint}`;

/** Describe the same gate that travel enforces, including its actual opening side. */
export function exitBlockage(game:GameSession,areas:Record<string,AreaDef>,from:string,exit:ExitDef):NavigationBlockage|undefined {
 const requirement=game.exitRequirement(exit);if(!requirement)return;
 const values={from:areas[from]?.name??from,to:areas[exit.to]?.name??exit.to,requirement};
 const reason=text('block.exit',values);
 if(!playableArea(exit.to))return {code:'unreleased',summary:text('block.unreleased'),reason,hint:text('block.unreleasedHint')};
 if(exit.requiredLevel!==undefined&&game.state.progression.level<exit.requiredLevel)return {code:'level',summary:text('block.level',{level:exit.requiredLevel}),reason,hint:text('block.levelHint')};
 const opening=exit.requires&&Object.values(areas).flatMap(area=>area.exits.filter(candidate=>candidate.unlock===exit.requires).map(candidate=>({area,candidate})))[0];
 return {code:'prerequisite',summary:text('block.prerequisite'),reason,hint:opening?text('block.openingHint',{area:opening.area.name,exit:opening.candidate.label}):text('block.prerequisiteHint')};
}

/** Explain a gate on a real directed route to this destination, never an unrelated exit.
 * Prefer the fewest closed gates, then the shortest route. This is diagnostic only. */
export function routeBlockage(game:GameSession,areas:Record<string,AreaDef>,target:string):NavigationBlockage|undefined {
 if(!areas[target])return {code:'unreleased',summary:text('block.unreleased'),reason:text('block.missingArea'),hint:text('block.unreleasedHint')};
 type Candidate={area:string;gates:number;hops:number;first?:{from:string;exit:ExitDef}};
 const start:Candidate={area:game.state.area,gates:0,hops:0},best=new Map<string,Candidate>([[start.area,start]]),pending=[start];
 const compare=(a:Candidate,b:Candidate)=>a.gates-b.gates||a.hops-b.hops;
 while(pending.length){
  pending.sort(compare);const current=pending.shift()!;if(best.get(current.area)!==current)continue;
  if(current.area===target)return current.first?exitBlockage(game,areas,current.first.from,current.first.exit):undefined;
  for(const exit of areas[current.area]?.exits??[]){
   if(!areas[exit.to])continue;
   const closed=!!game.exitRequirement(exit),next:Candidate={area:exit.to,gates:current.gates+Number(closed),hops:current.hops+1,first:current.first??(closed?{from:current.area,exit}:undefined)},old=best.get(exit.to);
   if(old&&compare(old,next)<=0)continue;best.set(exit.to,next);pending.push(next);
  }
 }
 return {code:'route',summary:text('block.noConnection'),reason:text('block.noConnectionReason',{area:areas[target].name}),hint:text('block.noConnectionHint')};
}

export function pathBlockage(target:string,enemy=false,stuck=false):NavigationBlockage {
 return {code:stuck?'stuck':'path',summary:text(stuck?'block.stuck':'block.path'),reason:text(stuck?'block.stuckReason':enemy?'block.enemyReason':'block.pathReason',{target}),hint:text(stuck?'block.stuckHint':'block.pathHint')};
}

/** Combat needs a reachable firing/contact position, not the enemy's centre.
 * Every alternative still requires a real walking route and a clear attack ray. */
export function enemyApproachPath(game:GameSession,world:WorldQuery,enemy:EnemyState):Point[] {
 const p=game.state.player,profile=game.basicAttackProfile();
 const reach=profile.rangeMetres+(profile.angleDegrees?enemyHurtRadius(enemy):0)-.2;
 const clear=(q:Point)=>world.visible(q,enemy)&&Math.abs(world.height(q)-world.height(enemy))<1.2;
 if(Math.hypot(p.x-enemy.x,p.z-enemy.z)<=reach&&clear(p))return [{x:p.x,z:p.z}];
 const direct=world.path?.(p,enemy)??[];if(direct.length)return direct;
 const angle=Math.atan2(p.z-enemy.z,p.x-enemy.x),radius=reach*.85;
 for(const offset of [0,1,-1,2,-2,3,-3,4]){
  const a=angle+offset*Math.PI/4,q={x:enemy.x+Math.cos(a)*radius,z:enemy.z+Math.sin(a)*radius};
  if(!clear(q))continue;
  const path=world.path?.(p,q)??[];if(path.length)return path;
 }
 return [];
}

/** One breadth-first tree serves every destination in a guidance refresh.
 * Rebuild on each refresh so level/door changes are visible immediately. */
export function availableRoutes(game:GameSession,areas:Record<string,AreaDef>,target?:string):Map<string,ExitDef[]> {
 const start=game.state.area,queue=[start],routes=new Map<string,ExitDef[]>([[start,[]]]);
 if(target===start)return routes;
 for(let i=0;i<queue.length;i++)for(const exit of areas[queue[i]]?.exits??[]){
  if(routes.has(exit.to)||game.exitRequirement(exit))continue;
  routes.set(exit.to,[...routes.get(queue[i])!,exit]);
  if(exit.to===target)return routes;
  queue.push(exit.to);
 }
 return routes;
}
/** The actual directional exits, release boundaries and level gates. */
export function availableRoute(game:GameSession,areas:Record<string,AreaDef>,target:string):ExitDef[]|null {
 return availableRoutes(game,areas,target).get(target)??null;
}
