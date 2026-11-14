import type {AreaDef,ExitDef,Obstacle,Point} from '../../../core/Contracts';
import {Navigation} from '../../navigation/runtime/Navigation';

/** One fixed world pose shared by the rune renderer and its projected label. */
export const SIGIL_FRAME=Object.freeze({size:2.5,centerHeight:1.3,yaw:Math.atan2(15,18)*180/Math.PI,pitch:-39.55});

export interface PortalMount {
 readonly id:string;
 readonly exit:ExitDef;
 readonly kind:'side-waystone'|'floor-inlay'|'exit-sigil';
 /** Base at the unchanged walk-surface elevation, before any visual decal lift. */
 readonly position:Point & {readonly y:number};
 readonly yaw:number;
 readonly width:number;
 readonly height:number;
 readonly depth:number;
 /** Actual axis-aligned physics/navigation footprint, already rotated by yaw. */
 readonly collider?:Obstacle;
 readonly offset:number;
}
export interface PortalPlacementInput {
 readonly area:AreaDef;
 readonly obstacles:readonly Obstacle[];
 readonly incomingEntries:readonly Point[];
 readonly approaches?:readonly (readonly Point[])[];
 readonly forbidden:readonly {x:number;z:number;width:number;depth:number}[];
 readonly height:(point:Point)=>number;
}
export interface PortalPlacementReport {
 /** Pure visual sigils do not perform physical placement or route checks. */
 mode?:'non-solid-exit-sigils';
 exits:number;
 standing:number;
 floor:number;
 attempts:number;
 navigationChecks:number;
 protectedPoints:number;
 protectedChecks?:number;
 routeTargets:number;
 baselineUnreachable:Point[];
 rejected:Record<string,number>;
}
export interface PortalPlacementPlan {
 readonly mounts:PortalMount[];
 readonly obstacles:Obstacle[];
 readonly report:PortalPlacementReport;
}

const YAW=39.8 as const,WIDTH=1.6,HEIGHT=2.65,DEPTH=.38,RADIUS=.42;
const angle=YAW*Math.PI/180,AABB_WIDTH=WIDTH*Math.cos(angle)+DEPTH*Math.sin(angle),AABB_DEPTH=WIDTH*Math.sin(angle)+DEPTH*Math.cos(angle);
const pointKey=(point:Point)=>point.x.toFixed(6)+','+point.z.toFixed(6);
const unique=(points:readonly Point[])=>Array.from(new Map(points.map(point=>[pointKey(point),point])).values());
const overlaps=(a:{x:number;z:number;width:number;depth:number},b:{x:number;z:number;width:number;depth:number},margin=0)=>Math.abs(a.x-b.x)<(a.width+b.width)/2+margin&&Math.abs(a.z-b.z)<(a.depth+b.depth)/2+margin;
const covers=(box:Obstacle,point:Point)=>Math.abs(point.x-box.x)<box.width/2+RADIUS&&Math.abs(point.z-box.z)<box.depth/2+RADIUS;

function outward(area:AreaDef,exit:ExitDef,approach?:readonly Point[]):Point {
 if(approach)for(let i=approach.length-2;i>=0;i--){
  const x=exit.x-approach[i].x,z=exit.z-approach[i].z,length=Math.hypot(x,z);
  if(length>.25)return {x:x/length,z:z/length};
 }
 const sides=[{x:1,z:0,d:area.width/2-exit.x},{x:-1,z:0,d:area.width/2+exit.x},{x:0,z:1,d:area.depth/2-exit.z},{x:0,z:-1,d:area.depth/2+exit.z}];
 const side=sides.sort((a,b)=>a.d-b.d)[0];return {x:side.x,z:side.z};
}

/** Native Navigation supplies every connectivity decision. .42m clearance is
 * deliberately stricter than the actual .32m player capsule, including its
 * direct-path shortcut; an unsafe mounting never changes a travel endpoint. */
function legalRoute(nav:Navigation,from:Point,to:Point,saved?:readonly Point[]):Point[] {
 if(nav.blocked(from,RADIUS)||nav.blocked(to,RADIUS))return [];
 const valid=(route:readonly Point[])=>route.length>0&&pointKey(route[0])===pointKey(from)&&pointKey(route[route.length-1])===pointKey(to)&&route.slice(1).every((point,index)=>nav.visible(route[index],point,RADIUS));
 // Existing native routes usually remain clear: side stones are deliberately
 // outside their final approach. Revalidate those segments against the new
 // Navigation before asking its A* to find a replacement.
 if(saved&&valid(saved))return saved.map(point=>({...point}));
 const route=nav.path(from,to);return valid(route)?route:[];
}

/** Plan after ordinary dressing. Only the far SW tangent is considered; the
 * foreground NE side is never used as a fallback. Existing obstacle and entry
 * coordinates remain immutable, and floor mounts have no physical footprint. */
export function planPortalMounts(input:PortalPlacementInput):PortalPlacementPlan {
 const {area}=input,obstacles:Obstacle[]=[],mounts:PortalMount[]=[];
 const protectedPoints=unique([area.spawn,...input.incomingEntries,...area.objects,...area.exits,...area.enemies]);
 const targets=unique([...area.exits,...input.incomingEntries]);
 const report:PortalPlacementReport={exits:area.exits.length,standing:0,floor:0,attempts:0,navigationChecks:0,protectedPoints:protectedPoints.length,routeTargets:targets.length,baselineUnreachable:[],rejected:{}};
 const baseline=new Navigation(area.width,area.depth,[...input.obstacles]);
 let routes=targets.map(target=>legalRoute(baseline,area.spawn,target,input.approaches?.[area.exits.findIndex(exit=>pointKey(exit)===pointKey(target))]));
 for(const [index,target]of targets.entries())if(!routes[index].length)report.baselineUnreachable.push({x:target.x,z:target.z});
 const reject=(reason:string)=>{report.rejected[reason]=(report.rejected[reason]??0)+1;};
 for(const [index,exit]of area.exits.entries()){
  let accepted:PortalMount|undefined;
  if(!report.baselineUnreachable.length){
   const direction=outward(area,exit,input.approaches?.[index]);
   let tangent={x:-direction.z,z:direction.x};
   // This is the fixed camera's world-space NE view direction, not live camera
   // rotation. Select its opposite-depth side even for a diagonal approach.
   if(tangent.x*15+tangent.z*18>0)tangent={x:-tangent.x,z:-tangent.z};
   for(const offset of [1.35,1.5,1.65]){
    report.attempts++;
    const point={x:exit.x+tangent.x*offset,z:exit.z+tangent.z*offset};
    const box:Obstacle={...point,width:AABB_WIDTH,depth:AABB_DEPTH,height:HEIGHT,kind:'waystone'};
    if(Math.abs(point.x)+box.width/2+.05>area.width/2||Math.abs(point.z)+box.depth/2+.05>area.depth/2){reject('bounds');continue;}
    if(protectedPoints.some(point=>covers(box,point))){reject('protected-point');continue;}
    if([...input.obstacles,...obstacles].some(obstacle=>overlaps(box,obstacle,.06))){reject('existing-obstacle');continue;}
    if(input.forbidden.some(region=>overlaps(box,region,.08))){reject('water-or-gorge');continue;}
    const y=input.height(point),support=[{x:point.x-box.width/2,z:point.z-box.depth/2},{x:point.x+box.width/2,z:point.z-box.depth/2},{x:point.x-box.width/2,z:point.z+box.depth/2},{x:point.x+box.width/2,z:point.z+box.depth/2}].map(input.height);
    if(!Number.isFinite(y)||support.some(height=>!Number.isFinite(height)||Math.abs(height-y)>.22)){reject('uneven-ground');continue;}
    const nav=new Navigation(area.width,area.depth,[...input.obstacles,...obstacles,box]);
    report.navigationChecks++;
    const candidateRoutes=targets.map((target,index)=>legalRoute(nav,area.spawn,target,routes[index]));
    if(candidateRoutes.some(route=>!route.length)){reject('connectivity');continue;}
    accepted={id:exit.id,exit,kind:'side-waystone',position:{...point,y},yaw:YAW,width:WIDTH,height:HEIGHT,depth:DEPTH,collider:box,offset};
    obstacles.push(box);routes=candidateRoutes;report.standing++;break;
   }
  }else reject('baseline-unreachable');
  if(!accepted){accepted={id:exit.id,exit,kind:'floor-inlay',position:{x:exit.x,y:input.height(exit),z:exit.z},yaw:YAW,width:1.7,height:.08,depth:1.7,offset:0};report.floor++;}
  mounts.push(accepted);
 }
 return {mounts,obstacles,report};
}

/** Visual-only rune at the authoritative interaction point. This planner
 * neither searches for room nor mutates any obstacle, route or ExitDef. */
export function planExitSigils(area:AreaDef,height:(point:Point)=>number):PortalPlacementPlan {
 const mounts:PortalMount[]=area.exits.map(exit=>({id:exit.id,exit,kind:'exit-sigil',position:{x:exit.x,y:height(exit),z:exit.z},yaw:SIGIL_FRAME.yaw,width:SIGIL_FRAME.size,height:SIGIL_FRAME.size,depth:.01,offset:0,collider:undefined}));
 return {mounts,obstacles:[],report:{mode:'non-solid-exit-sigils',exits:mounts.length,standing:mounts.length,floor:0,attempts:0,navigationChecks:0,protectedPoints:0,protectedChecks:0,routeTargets:0,baselineUnreachable:[],rejected:{}}};
}
