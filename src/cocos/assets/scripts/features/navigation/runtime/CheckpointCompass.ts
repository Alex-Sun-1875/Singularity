import type {AreaDef,Point} from '../../../core/Contracts';
import {playableArea,playableExits} from '../../journey/data/ChapterJourney';
import {Navigation} from './Navigation';
import {getTerrain} from '../../world/runtime/Terrain';
export interface HomeDirection {area:string;target:Point;distance:number}
/** Shortest discovered walking route; ordinary exits retain their actual locks. */
export class CheckpointCompass {
 private nav=new Map<string,Navigation>();
 private movingCosts=new Map<string,number>();private fixedCosts=new Map<string,number>();
 private last:{key:string;result:HomeDirection|null}|undefined;
 constructor(private areas:Record<string,AreaDef>){}
 private length(id:string,a:Point,b:Point,moving:boolean){
  const costs=moving?this.movingCosts:this.fixedCosts;
  const key=`${id}:${moving?a.x.toFixed(1):a.x},${moving?a.z.toFixed(1):a.z}>${b.x},${b.z}`,cached=costs.get(key);
  if(cached!==undefined){costs.delete(key);costs.set(key,cached);return cached;}
  let nav=this.nav.get(id);if(!nav){const area=this.areas[id];nav=new Navigation(area.width,area.depth,[...area.obstacles,...getTerrain(area).barriers],true);this.nav.set(id,nav);}
  const path=nav.path(a,b);let length=path.length?0:Infinity;
  for(let i=1;i<path.length;i++)length+=Math.hypot(path[i].x-path[i-1].x,path[i].z-path[i-1].z);
  // Evict one old entry; moving the player must never clear fixed exit costs.
  if(costs.size>=(moving?128:2048))costs.delete(costs.keys().next().value!);
  costs.set(key,length);return length;
 }
 find(area:string,position:Point,flags:Record<string,boolean>,level=1):HomeDirection|null {
  if(!playableArea(area))return null;
  const flagsKey=Object.keys(flags).filter(key=>flags[key]).sort().join('\0');
  const key=`${area}:${position.x},${position.z}:${level}:${flagsKey}`;
  if(this.last?.key===key)return this.last.result;
  const queue=[{id:area,point:position,cost:0,first:null as Point|null,key:area+'#start'}],best=new Map<string,number>();let result:HomeDirection|null=null;
  while(queue.length){queue.sort((a,b)=>a.cost-b.cost);const current=queue.shift()!;if(current.cost>(best.get(current.key)??Infinity))continue;if(result&&current.cost>=result.distance)break;const def=this.areas[current.id];
   if(flags[`checkpoint:${current.id}`]){const targets=def.objects.filter(o=>o.action==='checkpoint').map(o=>({x:o.x,z:o.z}));if(def.checkpoint||!targets.length)targets.push(def.spawn);for(const target of targets){const cost=current.cost+this.length(current.id,current.point,target,current.first===null);if(Number.isFinite(cost)&&(!result||cost<result.distance))result={area:current.id,target:current.first??target,distance:cost};}}
   for(const exit of playableExits(def)){if(!flags[`visited:${exit.to}`]||(exit.requiredLevel!==undefined?level<exit.requiredLevel:exit.requires&&!flags[exit.requires]))continue;const cost=current.cost+this.length(current.id,current.point,exit,current.first===null),key=exit.to+'#'+exit.id;if(cost>=(best.get(key)??Infinity))continue;best.set(key,cost);queue.push({id:exit.to,point:exit.entry,cost,first:current.first??exit,key});}
  }
  this.last={key,result};return result;
 }
}
