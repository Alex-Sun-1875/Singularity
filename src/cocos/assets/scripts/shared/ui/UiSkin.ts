import {CompactGraphics} from './CompactGraphics';
import {gameResources as resources} from '../assets/GameResources';
import {ButtonComponent as Button,Color,Graphics,Node,Rect,Size,Sprite,SpriteFrame,Texture2D,UITransform,macro,dynamicAtlasManager} from 'cc';
import {MINIGAME} from 'cc/env';
import {UI_COLORS as C} from './UiTheme';
import {UI_FRAME_GOLD,UI_FRAME_LAYOUT} from './UiChrome';
import {FeedbackView as F} from './FeedbackView';
import {DoubleGoldFrame} from './DoubleGoldFrame';
import {PREPARATION_SKIN_INSETS} from './PreparationTheme';
import {FrameCache} from '../assets/FrameCache';
import {HUD_SKILL_ATLAS_ICONS} from './HudSkillAtlas';
import {HUD_PANEL_ATLAS_PATH,HUD_PANEL_ATLAS_REGIONS} from './HudPanelAtlas';
import {GOLD_FRAME_ATLAS_PATHS,GOLD_FRAME_ATLAS_REGIONS} from './GoldFrameAtlas';

const ROOT='ui/quiet-bronze/';
const INSETS:Record<string,readonly number[]>={
 ...PREPARATION_SKIN_INSETS,
 'loot-drop-panel-v1':[38,38,24,24],
 'rpg-tab-selected-v3':[24,24,12,12],'rpg-button-gold-v3':[24,24,12,12],'rpg-button-dark-v3':[24,24,12,12],'rpg-selection-frame-v3':[24,24,18,18],
 'rpg-outer-frame-v2':[32,32,32,32],'rpg-inner-frame-v2':[32,32,32,32],
 'rpg-button-gold-v2':[24,24,12,12],'rpg-button-dark-v2':[24,24,12,12],
 'unified-gold-panel-v13':[24,24,24,24],
 'menu-panel-frame-v5':[40,40,40,40],'menu-panel-inset-v5':[40,40,40,40],
 'menu-pill-frame-v5':[64,64,64,64],'menu-pill-inset-v5':[64,64,64,64],
 'double-gold-frame-v6':[48,48,48,48],'double-gold-frame-rpg-v4':[48,48,48,48],'double-gold-inset-v6':[48,48,48,48],
 'start-menu-primary-v8':[54,54,12,12],'start-menu-secondary-v8':[54,54,12,12],
 'bar-track':[24,24,8,8],'divider-horizontal':[8,8,4,4],'divider-vertical':[4,4,8,8],
};

/** Shared original asset frames; Cocos handles sprite rendering and nine-slicing. */
export class UiSkin {
 private static frames=new FrameCache();
 private static hudSkillFrames=new FrameCache();
 static releaseOwner(owner:Node){this.hudSkillFrames.releaseOwner(owner);this.frames.releaseOwner(owner);}
 static dispose(){this.hudSkillFrames.dispose();this.frames.dispose();}
 /** HUD medallions own their border; crop the painted tile's baked square rim. */
 static hudSkillFrame(path:string,owner?:Node,group=''):Promise<SpriteFrame>{
  if(!path.startsWith('ui/combat-relief/'))return this.frame(path,0,owner);
  const name=path.slice('ui/combat-relief/'.length),index=HUD_SKILL_ATLAS_ICONS[group]?.indexOf(name)??-1;
  const sourcePath=index<0?path.replace('ui/combat-relief/','ui/combat-relief/hud-circular/'):`ui/combat-relief/hud-circular/atlases/${group.toLowerCase()}`;
  return this.hudSkillFrames.get(path+':'+(index<0?'':group),owner,()=>{
   // Ordinary Cocos texture + SpriteFrame regions. Tiles retain all authored
   // RGBA pixels and the same fractional crop; alternative skills still load
   // their original images. No runtime atlas packing or engine overrides.
   return this.frame(sourcePath,0,owner).then(source=>{
    const r=source.rect,w=index<0?r.width:256,h=index<0?r.height:256,x=index<0?r.x:index%4*256,y=index<0?r.y:Math.floor(index/4)*256;
    const inset=name.startsWith('rpg-')?Math.min(w,h)*.047:0,frame=new SpriteFrame();
    frame.reset({texture:source.texture,rect:new Rect(x+inset,y+inset,w-2*inset,h-2*inset),originalSize:new Size(w-2*inset,h-2*inset)});frame.packable=false;return frame;
   });
  });
 }
 private static panelRegion(path:string){return dynamicAtlasManager.enabled?undefined:HUD_PANEL_ATLAS_REGIONS[path]??GOLD_FRAME_ATLAS_REGIONS[path];}
 /** Texture-only prewarm follows the same native atlas policy as drawable frames. */
 static texturePath(path:string){return (this.panelRegion(path)?(GOLD_FRAME_ATLAS_PATHS[path]??HUD_PANEL_ATLAS_PATH):path)+'/texture';}
 static frame(path:string,inset=0,owner?:Node):Promise<SpriteFrame>{
  const region=this.panelRegion(path),source=this.texturePath(path),key=path+':'+inset+(region?':panel':'');
  return this.frames.get(key,owner,()=>{
   const cached=resources.get(source,Texture2D);if(cached)return this.makeFrame(path,inset,cached,region);
   return new Promise((resolve,reject)=>resources.load(source,Texture2D,(error,texture)=>{if(error){reject(error);return;}resolve(this.makeFrame(path,inset,texture,region));}));
  });
 }
 static readyFrame(path:string,inset:number,owner:Node){return this.frames.getReady(path+':'+inset+(this.panelRegion(path)?':panel':''),owner);}
 private static makeFrame(path:string,inset:number,texture:Texture2D,region?:readonly [number,number,number,number]):SpriteFrame{
   const mipmappedChrome=path.startsWith('ui/combat-relief/')||path===ROOT+'hud-skill-face-v19'||path===ROOT+'unified-gold-skill-v18'||path===ROOT+'unified-gold-skill-v14'||path===ROOT+'unified-gold-skill-v15'||path===ROOT+'unified-gold-ring-v15'||path===ROOT+'unified-gold-skill-v16'||path===ROOT+'unified-gold-ring-v16'||path===ROOT+'skill-soft-shadow-v17'||path===ROOT+'skill-soft-halo-v17';
   if(path.startsWith(ROOT)||path.startsWith('ui/combat-relief/')){
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);
    // A mip sampler does not allocate mip levels. TapTap can discard decoded
    // images after upload, so keep single-level textures on bilinear filtering
    // and never re-upload them while image-cache cleanup is enabled.
    const image=mipmappedChrome&&!MINIGAME&&!macro.CLEANUP_IMAGE_CACHE&&texture.mipmapLevel===1?texture.image:null;
    if(image?.isValid&&image.data){texture.setMipFilter(Texture2D.Filter.LINEAR);texture.image=image;}
    // WebGL 1 cannot generate mipmaps for non-power-of-two textures either.
    texture.setMipFilter(mipmappedChrome&&texture.mipmapLevel>1?Texture2D.Filter.LINEAR:Texture2D.Filter.NONE);
   }
   // Keep fine lines and portraits on their source textures; native builds may discard CPU image data.
   const frame=new SpriteFrame();frame.packable=!region&&!path.startsWith('portraits/')&&!path.startsWith('ui/cinematics/')&&!mipmappedChrome&&!path.includes('double-gold-')&&!path.includes('start-menu-');frame.texture=texture;
   // Native Sprite regions retain each original size, border inset and shader.
   // Static regions serve platforms where the engine's dynamic atlas is off.
   if(region){const[x,y,w,h]=region;frame.reset({texture,rect:new Rect(x,y,w,h),originalSize:new Size(w,h)});frame.packable=false;}
   const id=path.slice(ROOT.length),edges=path.startsWith(ROOT)?INSETS[id]??(/^prep-(button|scope|categories|chip|badge|plaque|point-counter|skill-cost|step)/.test(id)?[20,20,12,12]:id.startsWith('button-')||id.startsWith('panel-')||id==='mask-disabled'?[24,24,24,24]:[0,0,0,0]):[inset,inset,inset,inset];
   [frame.insetLeft,frame.insetRight,frame.insetTop,frame.insetBottom]=edges;return frame;
 }
 static sprite(parent:Node,path:string,w:number,h:number,tint=Color.WHITE,sliced=false):Sprite {
  const node=new Node('Skin:'+path);node.layer=parent.layer;parent.addChild(node);
  // Keep source-pixel nine-slice corners at one logical pixel. Labels/hits stay on the parent.
  const scale=path.startsWith(ROOT)?2:1;node.addComponent(UITransform).setContentSize(w*scale,h*scale);node.setScale(1/scale,1/scale,1);
  const sprite=node.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.trim=false;sprite.type=sliced?Sprite.Type.SLICED:Sprite.Type.SIMPLE;sprite.color=tint;
  const pending=this.frame(path,sliced?12:0,node),ready=this.readyFrame(path,sliced?12:0,node);
  if(ready)sprite.spriteFrame=ready;else void pending.then(frame=>{if(node.isValid)sprite.spriteFrame=frame;}).catch(()=>{});
  return sprite;
 }
 // panel-surface is a neutral 3.5% polish; the parent Graphics owns its semantic base fill.
 static asset(parent:Node,id:string,w:number,h:number,sliced=true,pixelScale?:number):Sprite{const sprite=this.sprite(parent,ROOT+id,w,h,Color.WHITE,sliced);if(pixelScale){sprite.node.getComponent(UITransform)!.setContentSize(w/pixelScale,h/pixelScale);sprite.node.setScale(pixelScale,pixelScale,1);}return sprite;}
 /** One component owns menu metal, material, shadow and optional crest. */
 static panel(parent:Node,w:number,h:number,fill=C.inset,shape:'panel'|'capsule'|'legacy'='panel',crest=false,pixelScale=1,borderSkin?:string):void {
  if(shape!=='legacy'){
   const frame=parent.getComponent(DoubleGoldFrame)??parent.addComponent(DoubleGoldFrame);
   frame.configure(w,h,{shape,fill,crest,pixelScale,borderSkin},id=>{const pending=this.frame(ROOT+id,0,parent);return this.readyFrame(ROOT+id,0,parent)??pending;});return;
  }
  const body=new Node('PanelBody');body.layer=parent.layer;parent.addChild(body);body.addComponent(UITransform).setContentSize(w,h);
  const g=body.addComponent(CompactGraphics);g.fillColor=fill;g.roundRect(-w/2,-h/2,w,h,Math.min(UI_FRAME_LAYOUT.cornerRadius,w/2,h/2));g.fill();
  this.asset(parent,UI_FRAME_LAYOUT.skin,w,h).node.name='SharedGoldFrame';
 }
 static rule(parent:Node,w:number,scale=1):Graphics {
  const g=parent.addComponent(CompactGraphics);g.strokeColor=new Color(UI_FRAME_GOLD.metal.r,UI_FRAME_GOLD.metal.g,UI_FRAME_GOLD.metal.b,140);g.lineWidth=1.2*scale;g.moveTo(-w/2,0);g.lineTo(w/2,0);g.stroke();return g;
 }
 /** Rendering only; the owning row retains one accessible-sized input target. */
 static toggle(parent:Node,w:number,h:number,on:boolean,scale=1,trailingThumb=false):void {
  const g=parent.addComponent(CompactGraphics);g.fillColor=on?F.color('state.success',55):C.toggleOff;g.roundRect(-w/2,-h/2,w,h,h/2);g.fill();
  this.asset(parent,'double-gold-toggle-track-v6',w,h,false);
  const d=h-3*scale,x=(on||trailingThumb?1:-1)*(w/2-h/2);this.asset(parent,'double-gold-toggle-thumb-v6',d,d,false).node.setPosition(x,0);
 }
 static button(node:Node,w:number,h:number):Button {
  const skin=this.asset(node,'button-normal',w,h),button=node.addComponent(Button);button.target=skin.node;button.transition=Button.Transition.SPRITE;button.duration=.1;
  for(const [id,key]of [['normal','normalSprite'],['hover','hoverSprite'],['pressed','pressedSprite'],['disabled','disabledSprite']]as const)
   void this.frame(ROOT+'button-'+id,0,node).then(frame=>{if(button.isValid){button[key]=frame;if(key==='normalSprite'&&!skin.spriteFrame)skin.spriteFrame=frame;}}).catch(()=>{});
  return button;
 }
 static selected(parent:Node,w:number,h:number):Sprite {const mark=this.asset(parent,'indicator-selected',12,Math.min(32,h-12),false);mark.node.setPosition(-w/2+16,0);return mark;}
 static bar(parent:Node,w:number,kind:'health'|'focus'):Sprite {
  this.asset(parent,'bar-track',w,16);
  const fill=this.asset(parent,'bar-'+kind+'-fill',w-12,6,false);fill.fillType=Sprite.FillType.HORIZONTAL;fill.fillStart=0;fill.fillRange=1;fill.type=Sprite.Type.FILLED;
  this.asset(parent,'bar-cap-left',12,16,false).node.setPosition(-w/2+6,0);
  this.asset(parent,'bar-cap-right',12,16,false).node.setPosition(w/2-6,0);return fill;
 }
}
