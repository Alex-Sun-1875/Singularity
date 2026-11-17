import type {InteractionDef,Point,WorldQuery} from '../../../core/Contracts';

/** Use the same physical reach for manual interaction, guidance and automation. */
export const interactionRange=(object:InteractionDef)=>Math.min(1.35,object.radius??1.35);
export function interactionInRange(world:WorldQuery,from:Point,object:InteractionDef,inset=0):boolean {
 return Math.hypot(from.x-object.x,from.z-object.z)<=Math.max(0,interactionRange(object)-inset)&&world.visible(from,object)&&Math.abs(world.height(from)-world.height(object))<1.2;
}

/** An interaction anchor may belong to a solid table or mechanism. Walk to a
 * visible position within its real reach, never through that prop's collider. */
export function interactionApproachPath(world:WorldQuery,from:Point,object:InteractionDef):Point[] {
 if(interactionInRange(world,from,object,.05))return [{x:from.x,z:from.z}];
 const direct=world.path?.(from,object)??[];if(direct.length)return direct;
 const radius=interactionRange(object)-.1;if(radius<=0)return [];
 const facing=Math.atan2(from.z-object.z,from.x-object.x);
 for(const scale of [1,.65])for(const offset of [0,1,-1,2,-2,3,-3,4,-4,5,-5,6,-6,7,-7,8]){
  const angle=facing+offset*Math.PI/8,point={x:object.x+Math.cos(angle)*radius*scale,z:object.z+Math.sin(angle)*radius*scale};
  if(!interactionInRange(world,point,object,.05))continue;
  const path=world.path?.(from,point)??[];if(path.length)return path;
 }
 return [];
}
