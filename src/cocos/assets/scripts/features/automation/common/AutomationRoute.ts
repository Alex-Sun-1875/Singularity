import type {AreaDef,ExitDef,Point,WorldQuery} from '../../../core/Contracts';
import type {EnemyState,GameSession} from '../../../core/GameSession';
import {enemyHurtRadius} from '../../combat/common/EnemyCombat';

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
