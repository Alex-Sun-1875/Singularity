import {CompactGraphics} from './CompactGraphics';
import {_decorator,Color,Component,Graphics,Node,Sprite,SpriteFrame,UITransform} from 'cc';
import {UI_FRAME_LAYOUT} from './UiChrome';
import {UI_COLORS as C} from './UiTheme';

const {ccclass,requireComponent}=_decorator;
export interface DoubleGoldFrameOptions {
 shape?:'panel'|'capsule';
 /** Native reference pixels per 720-high design canvas, independent of input mode. */
 pixelScale?:number;
 crest?:boolean;
 fill?:Color;
 /** Optional derived border; geometry and source corner widths stay shared. */
 borderSkin?:string;
}
type FrameLoader=(id:string)=>SpriteFrame|Promise<SpriteFrame>;

/** Shared double metal lip, inset material and optional stag from approved art.
 * It owns decoration only; callers keep their content and input regions. */
@ccclass('DoubleGoldFrame')
@requireComponent(UITransform)
export class DoubleGoldFrame extends Component {
 loaded=false;
 loadError='';
 ready:Promise<void>=Promise.resolve();
 private version=0;
 private owned:Node[]=[];
 private options:DoubleGoldFrameOptions={};
 private loader:FrameLoader|null=null;
 configure(width:number,height:number,options:DoubleGoldFrameOptions,loader:FrameLoader):void {
  this.options={...options};this.loader=loader;this.resize(width,height);
 }
 resize(width:number,height:number):void {
  this.node.getComponent(UITransform)!.setContentSize(width,height);const version=++this.version;this.loaded=false;this.loadError='';
  for(const node of this.owned){node.removeFromParent();node.destroy();}this.owned=[];
  const capsule=this.options.shape==='capsule',pixelScale=this.options.pixelScale??1,radius=capsule?height/2:26*pixelScale;
  const shadow=this.part('GoldFrameShadow',width+12*pixelScale,height+12*pixelScale),g=shadow.addComponent(CompactGraphics);
  for(const [spread,alpha]of [[6,14],[4,22],[2,36]]){g.fillColor=new Color(C.background.r,C.background.g,C.background.b,alpha);g.roundRect(-width/2-spread*pixelScale,-height/2-spread*pixelScale-2*pixelScale,width+2*spread*pixelScale,height+2*spread*pixelScale,radius+spread*pixelScale);g.fill();}
  // Identical transform and lifetime: append the base after its shadow paths.
  g.fillColor=this.options.fill??C.inset;g.roundRect(-width/2,-height/2,width,height,radius);g.fill();
  // Panel art uses native pixels. Capsule caps fit the loaded source height;
  // only the straight middle stretches, so the ends retain their proportions.
  const material=capsule?'menu-pill-inset-v5':UI_FRAME_LAYOUT.panelMaterial;
  const border=capsule?UI_FRAME_LAYOUT.capsuleSkin:this.options.borderSkin??UI_FRAME_LAYOUT.panelSkin;
  const pending=[this.layer('GoldFrameMaterial',material,width,height,pixelScale,true,version,capsule),this.layer('SharedGoldFrame',border,width,height,pixelScale,true,version,capsule)];
  if(this.options.crest&&!capsule){
   const {crestWidth,crestHeight,crestOffset,crestShadowPadding}=UI_FRAME_LAYOUT;
   const backing=this.part('GoldFrameCrestShadow',(crestWidth+2*crestShadowPadding)*pixelScale,(crestHeight+2*crestShadowPadding)*pixelScale);backing.setPosition(0,height/2+crestOffset*pixelScale);
   pending.push(this.loadSprite(backing,UI_FRAME_LAYOUT.crestShadowSkin,false,version));
   const crest=this.part('GoldFrameCrest',crestWidth*pixelScale,crestHeight*pixelScale);crest.setPosition(0,height/2+crestOffset*pixelScale);
   pending.push(this.loadSprite(crest,UI_FRAME_LAYOUT.crestSkin,false,version));
  }
  this.ready=Promise.all(pending).then(()=>{if(this.isValid&&version===this.version)this.loaded=true;}).catch(error=>{if(this.isValid&&version===this.version){this.loadError=String(error);console.warn('DoubleGoldFrame could not load its shared skin:',error);}});
 }
 /** Content remains clipped independently; the complete metal lip stays above it. */
 bringBorderToFront():void {this.node.getChildByName('SharedGoldFrame')?.setSiblingIndex(this.node.children.length-1);}
 private part(name:string,width:number,height:number):Node {
  const node=new Node(name);node.layer=this.node.layer;this.node.addChild(node);node.setSiblingIndex(this.owned.length);node.addComponent(UITransform).setContentSize(width,height);this.owned.push(node);return node;
 }
 private layer(name:string,id:string,width:number,height:number,pixelScale:number,sliced:boolean,version:number,fitHeight=false):Promise<void> {
  const node=this.part(name,width/pixelScale,height/pixelScale);node.setScale(pixelScale,pixelScale,1);return this.loadSprite(node,id,sliced,version,fitHeight?{width,height}:undefined);
 }
 private async loadSprite(node:Node,id:string,sliced:boolean,version:number,fitSize?:{width:number;height:number}):Promise<void> {
  const sprite=node.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.type=sliced?Sprite.Type.SLICED:Sprite.Type.SIMPLE;sprite.trim=false;sprite.color=Color.WHITE;
  const result=this.loader!(id),frame=result instanceof SpriteFrame?result:await result;
  if(this.isValid&&version===this.version&&node.isValid&&node.parent===this.node){
   if(fitSize){const scale=fitSize.height/Math.max(1,frame.rect.height);node.getComponent(UITransform)!.setContentSize(fitSize.width/scale,frame.rect.height);node.setScale(scale,scale,1);}
   sprite.spriteFrame=frame;
  }
 }
}
