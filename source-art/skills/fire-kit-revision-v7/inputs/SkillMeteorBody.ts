import {Vec3} from 'cc';
import {SkillFireSprites} from './SkillFireSprites';

type Point={x:number;z:number};
type Comet={key:string;position:Vec3;active:boolean;touched:boolean};

/** Incandescent comet silhouette following the existing cast clock. The fire
 * pool owns its cards; no bare rock mesh, extra light, or damage is created. */
export class SkillMeteorBody {
 private readonly comets:Comet[]=[];
 private readonly direction=new Vec3(2.6,-8,-1.8).normalize();
 constructor(private readonly groundHeight:(p:Point)=>number,private readonly fire:SkillFireSprites){}
 begin(){for(const comet of this.comets)comet.touched=false;}
 draw(key:string,target:Point,rank:number,progress:number,time:number){
  if(progress>=1)return;
  let comet=this.comets.find(c=>c.key===key)??this.comets.find(c=>!c.active);
  if(!comet){if(this.comets.length>=4)return;comet={key,position:new Vec3(),active:false,touched:false};this.comets.push(comet);}
  const t=Math.max(0,Math.min(1,progress)),fall=.4*t+.6*t*t,size=1.05+rank*.11;
  // Use real world Y, matching the resolved target and impact clock. The long
  // wake points opposite this descent rather than rotating a separate stone.
  comet.position.set(target.x-2.6*(1-fall),this.groundHeight(target)+8*(1-fall)+size*.30,target.z+1.8*(1-fall));
  comet.key=key;comet.touched=true;comet.active=true;
  this.fire.drawComet(key,comet.position,this.direction,size,time,255);
 }
 end(){for(const comet of this.comets)if(!comet.touched)comet.active=false;}
 clear(){for(const comet of this.comets){comet.active=false;comet.touched=false;comet.key='';}}
 inspect(){return{model:'incandescent-comet-v10',capacity:4,opaqueRockMeshes:0,active:this.comets.filter(c=>c.active).map(c=>({key:c.key,position:{x:c.position.x,y:c.position.y,z:c.position.z}}))};}
 destroy(){this.comets.length=0;}
}
