import {EventTouch,Node,Sprite,SpriteFrame,UITransform} from 'cc';

/** Concept-art paper doll inside the existing equipment panel. The caller owns the frame. */
export class FlatCharacterPreview {
 private readonly image:Node;
 private yaw=0;
 private readonly sprite:Sprite;
 constructor(host:Node,frame:SpriteFrame,private readonly width:number,private readonly height:number,private readonly views:SpriteFrame[]=[]){
  this.image=new Node('FlatCharacterArt');host.addChild(this.image);this.image.layer=host.layer;
  this.image.addComponent(UITransform);
  this.sprite=this.image.addComponent(Sprite);this.sprite.sizeMode=Sprite.SizeMode.CUSTOM;this.sprite.trim=false;this.show(frame);
  this.image.on(Node.EventType.TOUCH_MOVE,(event:EventTouch)=>{event.propagationStopped=true;this.rotate(event.getDeltaX()*.45);});
 }
 private show(frame:SpriteFrame){const rect=frame.rect,scale=Math.min(this.width/Math.max(1,rect.width),this.height/Math.max(1,rect.height));this.image.getComponent(UITransform)!.setContentSize(rect.width*scale,rect.height*scale);this.sprite.spriteFrame=frame;}
 rotate(degrees:number){if(!this.image.isValid)return;this.yaw+=degrees;if(this.views.length){const index=((Math.round(this.yaw/90)%this.views.length)+this.views.length)%this.views.length;this.show(this.views[index]);}}
 destroy(){if(this.image.isValid)this.image.destroy();}
}
