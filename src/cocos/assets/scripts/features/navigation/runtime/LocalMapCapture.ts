import {Camera,Color,Director,Layers,Node,RenderTexture,Sprite,SpriteFrame,UITransform,Vec3,director} from 'cc';
import type {AreaDef} from '../../../core/Contracts';

/** One native top-camera frame; actor layer18 is excluded, and capture stops. */
export class LocalMapCapture {
 private camera:Camera|null=null;private texture:RenderTexture|null=null;private frame:SpriteFrame|null=null;private image:Node|null=null;private disposed=false;
 constructor(parent:Node,area:AreaDef,x:number,y:number,w:number,h:number){
  const scene=director.getScene();if(!scene)return;
  try{
   const width=768,height=Math.max(128,Math.round(width*area.depth/area.width)),texture=new RenderTexture();texture.reset({width,height});this.texture=texture;
   const image=new Node('CapturedTerrain');image.layer=Layers.Enum.UI_2D;parent.addChild(image);image.setPosition(x+w/2,-y-h/2);image.addComponent(UITransform).setContentSize(w,h);const sprite=image.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;
   const frame=new SpriteFrame();frame.texture=texture;frame.packable=false;frame.flipUVX=true;this.frame=frame;sprite.spriteFrame=frame;sprite.color=Color.WHITE;image.active=false;this.image=image;
   const node=new Node('LocalMapCaptureCamera');scene.addChild(node);node.setPosition(0,180,0);node.lookAt(Vec3.ZERO,new Vec3(0,0,1));const camera=node.addComponent(Camera);this.camera=camera;camera.enabled=false;camera.projection=Camera.ProjectionType.ORTHO;camera.orthoHeight=area.depth/2;camera.near=.1;camera.far=250;camera.visibility=Layers.Enum.DEFAULT;camera.clearColor=new Color(7,9,9,255);camera.clearFlags=Camera.ClearFlag.SOLID_COLOR;camera.priority=-10;camera.targetTexture=texture;
   director.once(Director.EVENT_AFTER_DRAW,()=>{if(this.disposed||!camera.isValid)return;camera.enabled=true;director.once(Director.EVENT_AFTER_DRAW,()=>{if(this.disposed||!camera.isValid)return;camera.enabled=false;if(image.isValid)image.active=true;});});
  }catch(error){this.destroy();console.warn('[Map] Native terrain capture unavailable; coordinate chart retained',String(error));}
 }
 destroy():void{this.disposed=true;if(this.camera){this.camera.enabled=false;this.camera.targetTexture=null;this.camera.node.destroy();}this.image?.destroy();this.frame?.destroy();this.texture?.destroy();this.camera=null;this.image=null;this.frame=null;this.texture=null;}
}
