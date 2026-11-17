import {Vec3} from 'cc';
import type {SkillFireSprites} from './SkillFireSprites';
import type {ThunderArcField} from './ThunderArcField';

const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const smooth=(n:number)=>{n=clamp(n);return n*n*(3-2*n);};

/** Local energy gathers into the sampled casting palm, then opens along the
 * release direction. These are short hand accents, never projectiles or hits. */
export function drawSpellCast(fire:SkillFireSprites,thunder:ThunderArcField,key:string,family:'FIR'|'THU',hand:Vec3,facing:number,progress:number,releaseAge:number,ultimate:boolean,reduced:boolean){
 const releasing=releaseAge>=0;
 if(releasing&&releaseAge>=.12)return;
 const p=smooth(progress),fade=releasing?1-smooth(releaseAge/.12):1;
 const strength=(ultimate?1.18:1)*(releasing?1.12:.72+.28*p),alpha=(releasing?225:90+125*p)*fade;
 if(family==='FIR'){
  fire.drawCharge(key,hand,facing,p,releasing?releaseAge/.12:-1,strength,alpha);
  return;
 }
 const phase=reduced?0:progress*1.35;
 for(let i=0;i<3;i++){
  const angle=facing+i*Math.PI*2/3+phase,radius=(.32-.15*p)*(ultimate?1.22:1);
  const points:Vec3[]=[];
  for(let j=0;j<=8;j++){
   const t=j/8,reach=radius*(1-t),sway=Math.sin(t*Math.PI)*.045*(i%2?-1:1);
   const x=Math.cos(angle)*reach+Math.sin(angle)*sway,z=Math.sin(angle)*reach-Math.cos(angle)*sway;
   const push=releasing?Math.sin(Math.PI*t)*releaseAge*2.2:0;
   points.push(hand.clone().add(new Vec3(x+Math.sin(facing)*push,(i-1)*.07*(1-t)+Math.sin(t*Math.PI)*.07,z+Math.cos(facing)*push)));
  }
  thunder.addBeam(key,points,(.075+.022*p)*strength,Math.round(alpha*(i===0?1:.72)),'accent');
 }
}
