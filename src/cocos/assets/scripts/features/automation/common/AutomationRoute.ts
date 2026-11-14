import type {AreaDef,ExitDef} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';

/** The actual directional exits, release boundaries and level gates. */
export function availableRoute(game:GameSession,areas:Record<string,AreaDef>,target:string):ExitDef[]|null {
 const queue=[{area:game.state.area,route:[] as ExitDef[]}],seen=new Set([game.state.area]);
 if(target===game.state.area)return [];
 for(let i=0;i<queue.length;i++)for(const exit of areas[queue[i].area]?.exits??[]){
  if(game.exitRequirement(exit)||seen.has(exit.to))continue;
  const route=[...queue[i].route,exit];if(exit.to===target)return route;
  seen.add(exit.to);queue.push({area:exit.to,route});
 }
 return null;
}
