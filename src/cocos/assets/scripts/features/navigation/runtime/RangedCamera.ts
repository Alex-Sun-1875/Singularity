import {Camera,Vec3} from 'cc';
import type {Point} from '../../../core/Contracts';
import type {CombatSkillRank} from '../../combat/data/PureSkills';

/** Presentation bounds sampled from authored skill geometry; never used for damage. */
export function skillFramingPoints(player:Point,target:Point,angle:number,rank:CombatSkillRank|undefined,height:(p:Point)=>number):Vec3[]{
 const points=[new Vec3(player.x,height(player),player.z),new Vec3(player.x,height(player)+1.9,player.z)];
 const g=rank?.geometry;if(!g||g.kind.startsWith('self'))return points;
 const add=(p:Point)=>points.push(new Vec3(p.x,height(p)+.7,p.z));
 const local=(origin:Point,side:number,forward:number,a=angle)=>({x:origin.x+Math.cos(a)*side+Math.sin(a)*forward,z:origin.z-Math.sin(a)*side+Math.cos(a)*forward});
 const disk=(origin:Point,radius:number)=>{add(origin);for(let i=0;i<12;i++)add({x:origin.x+Math.sin(i*Math.PI/6)*radius,z:origin.z+Math.cos(i*Math.PI/6)*radius});};
 const rect=(origin:Point,length:number,width:number,center=true,a=angle)=>{for(const side of [-width/2,width/2])for(const forward of center?[-length/2,length/2]:[0,length])add(local(origin,side,forward,a));};
 const kind=g.kind;
 if(kind==='meleeFan'){add(player);for(let i=0;i<=12;i++){const a=angle+(i/12-.5)*(g.angleDegrees??110)*Math.PI/180;add(local(player,0,g.radiusMetres??2.4,a));}}
 else if(kind==='meleeRushCross'){disk(target,g.radiusMetres??1);add(target);}
 else if(kind==='meleeImpactDisk')disk(target,g.radiusMetres??2);
 else if(['sweptCorridor','projectileCorridor','instantCorridor'].includes(kind))rect(player,g.lengthMetres??rank.castRangeMetres,g.widthMetres??1,false);
 else if(kind==='crossStrips')for(const a of g.anglesDegrees??[-35,35])rect(target,g.lengthMetres??4,g.widthMetres??1,true,angle+a*Math.PI/180);
 else if(kind==='impactAndStrip'){disk(target,g.radiusMetres??2);rect(target,g.lengthMetres??4,g.widthMetres??2,false);}
 else if(kind==='placedStrip')rect(target,g.lengthMetres??4,g.widthMetres??2);
 else if(kind==='targetVolley'||kind==='filledWaveRectangle')rect(target,g.depthMetres??4,g.widthMetres??5);
 else if(kind==='boundedArcFan'){add(target);for(let i=0;i<=8;i++){const a=angle+((i/8-.5)*(g.angleDegrees??90))*Math.PI/180;add(local(target,0,g.radiusMetres??4,a));}}
 else if(g.radiusMetres)disk(target,g.radiusMetres);
 else add(target);
 return points;
}

/** Fits caster and far geometry using the existing native orthographic camera. */
export function rangedCameraFrame(camera:Camera,points:Vec3[],player:Point,groundY:number,aspect:number,minHeight:number){
 const right=camera.node.right,up=camera.node.up;let minX=Infinity,maxX=-Infinity,minY=Infinity,maxY=-Infinity;
 for(const p of points){const x=(p.x-player.x)*right.x+(p.y-groundY)*right.y+(p.z-player.z)*right.z,y=(p.x-player.x)*up.x+(p.y-groundY)*up.y+(p.z-player.z)*up.z;minX=Math.min(minX,x);maxX=Math.max(maxX,x);minY=Math.min(minY,y);maxY=Math.max(maxY,y);}
 // Normal casts retain generous HUD margins. The largest legal areas use more
 // of the central viewport instead of shrinking the actor to an unreadable dot.
 const ordinary=Math.max(minHeight,(maxY-minY+1.2)/(2*.76),(maxX-minX+1.8)/(2*Math.max(.8,aspect)*.77));
 const expansion=Math.max(0,Math.min(1,(ordinary-8)/2));
 const halfHeight=Math.min(13.5,Math.max(minHeight,(maxY-minY+1.2-.6*expansion)/(2*(.76+.18*expansion)),(maxX-minX+1.8-.8*expansion)/(2*Math.max(.8,aspect)*(.77+.07*expansion))));
 // Focus slightly right so the battlefield occupies the clearer left/centre,
 // away from the compass and the right thumb controls. Blend continuously.
 const cx=(minX+maxX)/2+halfHeight*aspect*.10,cy=(minY+maxY)/2-halfHeight*.08*(1-expansion)-up.y*.65;
 const determinant=right.x*up.z-right.z*up.x;
 const dx=Math.abs(determinant)>.01?(cx*up.z-right.z*cy)/determinant:0,dz=Math.abs(determinant)>.01?(right.x*cy-cx*up.x)/determinant:0;
 return {height:halfHeight,focus:{x:player.x+dx,z:player.z+dz}};
}
