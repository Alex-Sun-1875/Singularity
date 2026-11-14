import {Vec3} from 'cc';
import type {Point} from '../../../core/Contracts';
import {FEEDBACK_PALETTE as P} from '../../../shared/ui/FeedbackPalette';

export interface MeleeVfxHost {
 at(p:Point,height?:number):Vec3;
 line(points:Vec3[],color:string,width?:number,alpha?:number,taper?:boolean,style?:import('../../../shared/assets/VfxAssets').VfxLineStyle):void;
 blade?(key:string,p:Point,height:number,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,normal?:Vec3):void;
}
const point=(p:Point,a:number,r:number):Point=>({x:p.x+Math.sin(a)*r,z:p.z+Math.cos(a)*r});
/** All blade vertices remain within the supplied real radius. Thickness grows inward. */
export function drawMeleeSweep(host:MeleeVfxHost,key:string,p:Point,angle:number,radius:number,span:number,stage:number,t:number,alpha:number){
 if(!(radius>0&&span>0&&alpha>0))return;
 const reverse=stage===2,tilt=stage===3?.58:stage===2?-.16:.30;
 const normal=new Vec3(Math.cos(angle)*Math.sin(tilt),Math.cos(tilt),-Math.sin(angle)*Math.sin(tilt));
 host.blade?.(key,p,1.08,angle,radius,span,Math.min(radius*.13,.12+stage*.025),alpha,reverse?1-t:t,normal);
}
/** Small local contact rays, never another swept damage area. */
export function drawMeleeContact(host:MeleeVfxHost,key:string,p:Point,angle:number,strength:number,t:number,reduced=false){
 const fade=Math.pow(Math.max(0,1-t),1.8),alpha=Math.round((reduced?110:245)*fade),reach=(.17+Math.min(2,strength)*.075)*(1-t*.4);
 if(alpha<=0)return;
 const center=host.at(p,.68);
 for(let i=0;i<(reduced?3:5);i++){
  const phi=angle+i*Math.PI/5,q=point(p,phi,reach),end=host.at(q,.68+Math.cos(i*2.1)*reach);
  host.line([center,end],P['impact.core'],.018+(strength>1.7?.012:0),alpha,true,'core');
  if(!reduced)host.line([center,end],P['impact.metal'],.07,Math.round(alpha*.28),true,'glow');
 }
 if(strength<1.7||reduced)return;
 // A broken, short-lived pressure accent stays at the actual victim's feet.
 const dust:Vec3[]=[];for(let i=0;i<=12;i++){const a=angle-Math.PI*.65+i/12*Math.PI*1.3;dust.push(host.at(point(p,a,.22+.12*t),.035));}
 host.line(dust,P['impact.metal'],.025,Math.round(alpha*.42));
}
