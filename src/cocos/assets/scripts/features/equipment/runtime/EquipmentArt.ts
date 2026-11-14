import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Node,Sprite,SpriteFrame,Texture2D,UITransform,Rect,Size,JsonAsset,Color} from 'cc';
import type {ItemDef,EquipmentSlot} from '../data/Equipment';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {equipmentIcon} from './EquipmentPresentation';
import {equipmentIconFrame} from './EquipmentIconFrame';
import {FrameCache} from '../../../shared/assets/FrameCache';

export type EquipmentFamily='sword'|'bow'|'staff'|'oath'|'wind'|'seeker'|'jewelry';
export type EquipmentArtDef={image:string;rect:[number,number,number,number];family:EquipmentFamily;grade:number;name:string;existingIds?:string[];grip?:[number,number];slotRects?:Partial<Record<EquipmentSlot,[number,number,number,number]>>;description?:string;materials?:string[];features?:string[]};
export type EquipmentArtManifest={images:Record<string,{resource:string}>;items:Record<string,EquipmentArtDef>};

/** 复用原生SpriteFrame切片；图谱只读，不向游戏目录或库存注入设计款。 */
export class EquipmentArt {
 private static pending:Promise<EquipmentArtManifest>|null=null;
 private static campaignPending:Promise<{icons:Record<string,{resource:string;rect:[number,number,number,number]}>}>|null=null;
 private static frames=new FrameCache();
 static dispose(){this.frames.dispose();this.pending=null;this.campaignPending=null;}
 static async preloadItems(items:ItemDef[],owner:Node){await Promise.all(items.map(item=>item.kind==='spell'?UiSkin.frame('ui/icons/'+equipmentIcon(item),0,owner):this.itemFrame(item,owner)));}
 static manifest():Promise<EquipmentArtManifest>{
  if(!this.pending)this.pending=new Promise<EquipmentArtManifest>((resolve,reject)=>resources.load('equipment/v3/manifest',JsonAsset,(error,asset)=>{
   if(error){this.pending=null;reject(error);return;}
   const data=asset.json as EquipmentArtManifest;
   if(!data?.images||!data?.items){this.pending=null;reject(new Error('装备图谱元数据不完整'));return;}resolve(data);
  }));return this.pending;
 }
 static async frame(art:EquipmentArtDef,slot?:EquipmentSlot,owner?:Node):Promise<SpriteFrame>{
  const data=await this.manifest(),image=data.images[art.image];if(!image)throw new Error('Missing equipment image '+art.image);
  return this.resourceFrame(image.resource,slot&&art.slotRects?.[slot]||art.rect,owner);
 }
 private static async campaignFrame(id:string,owner?:Node):Promise<SpriteFrame|undefined>{
  if(!this.campaignPending)this.campaignPending=new Promise((resolve,reject)=>resources.load('equipment/campaign-v1/index',JsonAsset,(error,asset)=>{if(error){this.campaignPending=null;reject(error);return;}const data=asset.json as {icons:Record<string,{resource:string;rect:[number,number,number,number]}>};if(!data?.icons){this.campaignPending=null;reject(new Error('Campaign equipment icon index is incomplete'));return;}resolve(data);}));
  const entry=(await this.campaignPending).icons[id];return entry?this.resourceFrame(entry.resource,entry.rect,owner):undefined;
 }
 private static async resourceFrame(resource:string,rect:[number,number,number,number],owner?:Node):Promise<SpriteFrame>{
  const key=resource+':'+rect.join(',');
  return this.frames.get(key,owner,async()=>{
   const texture=await new Promise<Texture2D>((resolve,reject)=>resources.load(resource+'/texture',Texture2D,(error,texture)=>{
    if(error){reject(error);return;}
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);resolve(texture);
   }));
   if(rect[0]<0||rect[1]<0||rect[2]<=0||rect[3]<=0||rect[0]+rect[2]>texture.width||rect[1]+rect[3]>texture.height)throw new Error('Equipment art rect outside image: '+key);
   const frame=new SpriteFrame();frame.reset({texture,rect:new Rect(...rect),originalSize:new Size(rect[2],rect[3])});frame.packable=false;return frame;
  });
 }
 static mount(parent:Node,art:EquipmentArtDef,width:number,height:number,slot?:EquipmentSlot):Node{
  const node=new Node('EquipmentArt:'+art.family+':'+art.grade);node.layer=parent.layer;parent.addChild(node);node.addComponent(UITransform).setContentSize(width,height);
  const sprite=node.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.trim=false;
  void this.frame(art,slot,node).then(frame=>{if(!node.isValid)return;const r=frame.rect,s=Math.min(width/r.width,height/r.height);node.getComponent(UITransform)!.setContentSize(r.width*s,r.height*s);sprite.spriteFrame=frame;}).catch(error=>{if(node.isValid)console.warn('[EquipmentArt]',String(error));});return node;
 }
 static async itemFrame(item:ItemDef,owner?:Node):Promise<SpriteFrame>{
  const data=await this.manifest(),visualId=item.artSource??item.id,art=Object.values(data.items).find(a=>a.existingIds?.includes(visualId));
  if(art)return this.frame(art,item.slot==='spell'?undefined:item.slot,owner);
  const campaign=await this.campaignFrame(visualId,owner);if(campaign)return campaign;
  const family=['sword','bow','staff'].includes(item.kind)?item.kind:item.kind==='ring'?'ring':item.slot;
  return UiSkin.frame('ui/quiet-bronze/rpg-equipment-'+family,0,owner);
 }
 static icon(parent:Node,item:ItemDef,width:number,height:number,showcase=false):Node{
  if(item.kind==='spell')return this.rawIcon(parent,item,width,height,showcase);
  const frame=equipmentIconFrame(parent,width,height,{quality:item.quality,scale:Math.min(width,height)/48});this.rawIcon(frame.content,item,width-3,height-3,showcase);return frame.host;
 }
 /** The approved painted tiles match the inventory and workshop at reward scale. */
 static paintedIcon(parent:Node,item:ItemDef,width:number,height:number):Node{
  const unit=Math.min(width,height)/48,frame=equipmentIconFrame(parent,width,height,{quality:item.quality,scale:unit}),kind=['sword','bow','staff'].includes(item.kind)?item.kind:item.kind==='ring'?'ring':item.slot;
  UiSkin.asset(frame.content,'rpg-painted-'+kind+'-v5',width-2*unit,height-2*unit,false);return frame.host;
 }
 static rawIcon(parent:Node,item:ItemDef,width:number,height:number,showcase=false):Node{
  if(item.id==='DG_L01'){if(showcase){const h=Math.min(height,width*2);return UiSkin.asset(parent,'last-watch-sword-v2',h*.5,h,false).node;}const size=Math.min(width,height);return UiSkin.asset(parent,'rpg-equipment-sword',size,size,false).node;}
  const painted=['sword','bow','staff'].includes(item.kind)?item.kind:item.kind==='ring'?'ring':item.slot==='ringLeft'||item.slot==='ringRight'?'ring':item.slot;
  const fallback=item.kind==='spell'?UiSkin.sprite(parent,'ui/icons/'+equipmentIcon(item),width,height,Color.WHITE).node:UiSkin.asset(parent,'rpg-equipment-'+painted,width,height,false).node;
  if(item.kind==='spell')return fallback;
  void this.manifest().then(async data=>{
   if(!fallback.isValid)return;const visualId=item.artSource??item.id,art=Object.values(data.items).find(art=>art.existingIds?.includes(visualId));
   const frame=art?await this.frame(art,item.slot==='spell'?undefined:item.slot,parent):await this.campaignFrame(visualId,parent);
   if(!frame||!fallback.isValid)return;const node=new Node('EquipmentIcon:'+item.id);node.layer=parent.layer;parent.addChild(node);node.setSiblingIndex(fallback.getSiblingIndex());const r=frame.rect,s=Math.min(width/r.width,height/r.height);node.addComponent(UITransform).setContentSize(r.width*s,r.height*s);const sprite=node.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.trim=false;sprite.spriteFrame=frame;fallback.destroy();
  }).catch(error=>{if(fallback.isValid)console.warn('[EquipmentArt]',String(error));});return fallback;
 }
}
