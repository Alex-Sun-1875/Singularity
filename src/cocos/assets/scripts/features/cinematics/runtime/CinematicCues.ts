import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {Camera,Color,Graphics,Node,Vec3,screen} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import type {CampaignBeat} from '../common/CinematicTypes';
/** Existing authored story cues, isolated from subtitle layout and camera control. */
export class CinematicCues {
 private canvas:Graphics;
 constructor(root:Node,private hud:Hud,private camera:Camera,private world:SceneBuilder,private game:GameSession){const layer=hud.node('CinematicCues',root,0,0,hud.width,hud.height);layer.setSiblingIndex(0);this.canvas=layer.addComponent(CompactGraphics);}
 private project(x:number,z:number,y=.1){const p=this.camera.worldToScreen(new Vec3(x,this.world.height({x,z})+y,z)),pixels=screen.windowSize;return{x:p.x*this.hud.width/Math.max(1,pixels.width)-this.hud.width/2,y:p.y*this.hud.height/Math.max(1,pixels.height)-this.hud.height/2};}
 draw(b:CampaignBeat,time:number){
  const g=this.canvas,w=this.hud.width,h=this.hud.height,t=time,p=this.game.state.player;g.clear();
  if(b.cue==='dusk'){g.fillColor=new Color(10,15,43,Math.round(135*Math.sin(Math.min(1,t/4)*Math.PI)));g.rect(-w/2,-h/2,w,h);g.fill();}
  const origin=b.focus??{x:p.x,z:p.z+5},at=this.project(origin.x,origin.z,.2),pulse=1+Math.sin(t*3)*.1;
  if(['beacon','crown','command','furnace','bells'].includes(b.cue??'')){
   const blue=b.cue==='command'||b.cue==='bells',color=blue?new Color(130,199,239,210):new Color(247,191,100,210);g.strokeColor=color;g.lineWidth=2;
   if(b.cue==='beacon'){for(let i=0;i<3;i++){g.strokeColor=new Color(255,211,132,155-i*35);g.lineWidth=4+i*5;g.moveTo(at.x,at.y);g.lineTo(at.x,at.y+105+pulse*12);g.stroke();}}
   else if(b.cue==='furnace'){
    // The living light recoils from a visible restraint ring, not a loot crystal.
    const recoil=Math.sin(Math.min(1,t/3)*Math.PI/2)*36;g.ellipse(at.x,at.y,48,18);g.stroke();g.moveTo(at.x-48,at.y);g.lineTo(at.x-48,at.y+34);g.moveTo(at.x+48,at.y);g.lineTo(at.x+48,at.y+34);g.stroke();
    for(let i=3;i>0;i--){g.fillColor=new Color(255,170+i*18,80,30+i*12);g.circle(at.x-recoil,at.y+32,8+i*6*pulse);g.fill();}
   }else if(b.cue==='crown'){g.moveTo(at.x-44,at.y+4);g.lineTo(at.x-52,at.y+50);g.lineTo(at.x-23,at.y+30);g.lineTo(at.x,at.y+67);g.lineTo(at.x+23,at.y+30);g.lineTo(at.x+52,at.y+50);g.lineTo(at.x+44,at.y+4);g.close();g.stroke();g.ellipse(at.x,at.y,64*pulse,20*pulse);g.stroke();}
   else {for(let i=0;i<3;i++){const r=30+(t*30+i*38)%120;g.strokeColor=new Color(color.r,color.g,color.b,Math.round(180*(1-r/160)));g.ellipse(at.x,at.y,r,r*.32);g.stroke();}}
  }
 }
 clear(){this.canvas.clear();}
}
