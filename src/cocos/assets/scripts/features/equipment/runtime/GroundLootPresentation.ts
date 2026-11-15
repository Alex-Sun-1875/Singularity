import {Camera,Color,Label,Material,Mesh,MeshRenderer,Node,SpriteFrame,Vec3,Vec4,gfx,primitives,screen,sys,utils} from 'cc';
import type {GameSession,GroundLoot} from '../../../core/GameSession';
import {EQUIPMENT} from '../data/Equipment';
import {SUPPLIES,isSupplyId} from '../data/Supplies';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {EquipmentArt} from './EquipmentArt';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UiSkin} from '../../../shared/ui/UiSkin';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import type {Hud} from '../../../app/Hud';
import type {ItemDef} from '../data/Equipment';
import {equipmentDropPriority,highlightedEquipment} from '../common/LootFeedback';
import {equipmentText} from '../locales';

type Pile={root:Node;card:Node;halo:Node;aura?:Node;auraMaterial?:Material;alpha:number;label?:Label;highlighted:boolean;art:string;grounded:boolean;footprint:number;yaw:number;groundVertices:{x:number;y:number;z:number}[];available:boolean;cardMaterial?:Material;materials:Material[];meshes:Mesh[]};
type GroundArt={drop:GroundLoot;size:number;yaw:number};
const GROUND_CLEARANCE=.008;

/** Authored equipment and physical bottle props, grounded independently of corpses.
 * No colliders or input interception: SceneInteraction owns the pickup button.
 */
export class GroundLootPresentation {
 private piles=new Map<string,Pile>();
 private disposed=false;
 private labels:Node|undefined;
 private projected=new Vec3();private foot=new Vec3();
 constructor(private world:SceneBuilder,private camera:Camera,private hud:Hud){}
 private tint(material:Material,color:Color){material.setProperty('mainColor',new Vec4(Math.pow(color.r/255,2.2),Math.pow(color.g/255,2.2),Math.pow(color.b/255,2.2),color.a/255));}
 private node(name:string,parent:Node){const node=new Node(name);node.layer=this.world.root.layer;parent.addChild(node);return node;}
 private mount(parent:Node,frame:SpriteFrame,tint:Color,pile:Pile,ground?:GroundArt){
  const uv=frame.uv,geometry=primitives.quad();
  geometry.uvs=[uv[0],uv[1],uv[4],uv[5],uv[6],uv[7],uv[2],uv[3]];
  if(ground){
   const positions=geometry.positions!,base=this.world.height(ground.drop),c=Math.cos(ground.yaw),s=Math.sin(ground.yaw);
   // Map the authored top-down cutout onto XZ and sample each terrain corner.
   // Bottle and baked contact shadow share these vertices, so neither can stand up.
   for(let i=0;i<positions.length;i+=3){
    const longest=Math.max(frame.rect.width,frame.rect.height),u=positions[i]*ground.size*frame.rect.width/longest,v=positions[i+1]*ground.size*frame.rect.height/longest,x=u*c-v*s,z=u*s+v*c;
    const point={x:ground.drop.x+x,z:ground.drop.z+z},height=this.world.height(point);
    positions[i]=x;positions[i+1]=height-base;positions[i+2]=z;
    pile.groundVertices.push({...point,y:height+pile.root.position.y-base+parent.position.y});
   }
   geometry.normals=positions.map((_,i)=>i%3===1?1:0);
   geometry.minPos={x:Math.min(...positions.filter((_,i)=>i%3===0)),y:Math.min(...positions.filter((_,i)=>i%3===1)),z:Math.min(...positions.filter((_,i)=>i%3===2))};
   geometry.maxPos={x:Math.max(...positions.filter((_,i)=>i%3===0)),y:Math.max(...positions.filter((_,i)=>i%3===1)),z:Math.max(...positions.filter((_,i)=>i%3===2))};
  }
  const mesh=utils.createMesh(geometry),material=new Material();
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  material.setProperty('mainTexture',frame.texture);this.tint(material,tint);
  const renderer=parent.addComponent(MeshRenderer);renderer.mesh=mesh;renderer.setSharedMaterial(material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  pile.meshes.push(mesh);pile.materials.push(material);
  return material;
 }
 private create(drop:GroundLoot,available:boolean){
  const supply=isSupplyId(drop.item)?SUPPLIES[drop.item]:undefined,item=EQUIPMENT[drop.item],role=supply?.feedback??qualityFeedbackRole(item.quality);
  const hash=Array.from(drop.id).reduce((n,c)=>(n*31+c.charCodeAt(0))>>>0,0),yaw=hash*2.399963229728653%(2*Math.PI),highlighted=!supply&&highlightedEquipment(item.quality);
  const root=this.node('GroundLoot:'+drop.id,this.world.root),card=this.node('Item:'+drop.item,root),halo=this.node('Quality',root),pile:Pile={root,card,halo,highlighted,alpha:-1,art:supply?.groundArt??'equipment:'+drop.item,grounded:!!supply||highlighted,footprint:supply?.groundSize??1,yaw,groundVertices:[],available,materials:[],meshes:[]};
  // Painted ground accents sit 0.047m above the height field. Equipment rests
  // above that presentation surface; supplies keep their established geometry.
  root.setPosition(drop.x,this.world.height(drop)+(supply ? GROUND_CLEARANCE : .06),drop.z);
  halo.setRotationFromEuler(-90,0,0);halo.setScale(.95,.95,1);halo.active=!supply;
  if(!supply)void UiSkin.frame('ui/quiet-bronze/'+(highlighted?'loot-drop-ground-v1':'skill-soft-halo-v17'),0,root).then(frame=>{
   if(this.disposed||this.piles.get(drop.id)!==pile||!root.isValid)return;
   if(highlighted){halo.setRotationFromEuler(0,0,0);halo.setScale(1,1,1);halo.setPosition(0,.006,0);}
   this.mount(halo,frame,F.color(role,highlighted?235:190),pile,highlighted?{drop,size:1.5,yaw:0}:undefined);
  }).catch(error=>console.warn('[GroundLoot] Quality marker',String(error)));
  if(highlighted){
   const aura=pile.aura=this.node('LootSoftAura',root),legendary=equipmentDropPriority(item.quality)>=2;
   aura.setScale(legendary?1.1:.95,legendary?1.25:1.05,1);aura.setPosition(0,legendary?.52:.44,0);
   void UiSkin.frame('ui/quiet-bronze/loot-drop-aura-v1',0,root).then(frame=>{if(!this.disposed&&this.piles.get(drop.id)===pile&&root.isValid)pile.auraMaterial=this.mount(aura,frame,F.color(role,235),pile);}).catch(error=>console.warn('[GroundLoot] Soft aura',String(error)));
  }
  // Supplies only load their physical prop. Equipment retains its existing fallback.
  const artwork=supply?UiSkin.frame(supply.groundArt,0,root):EquipmentArt.itemFrame(item,root).catch(()=>UiSkin.frame('ui/icons/'+(item.kind==='sword'?'attack':item.kind==='bow'?'bow':item.kind==='staff'?'skill':'inventory'),0,root));
  void artwork.then(frame=>{
   if(this.disposed||this.piles.get(drop.id)!==pile||!root.isValid)return;
   if(highlighted)card.setPosition(0,.015,0);
   pile.cardMaterial=this.mount(card,frame,Color.WHITE,pile,pile.grounded?{drop,size:pile.footprint,yaw}:undefined);
   if(!pile.grounded){const scale=.8/Math.max(frame.rect.width,frame.rect.height);card.setScale(frame.rect.width*scale,frame.rect.height*scale,1);card.setPosition(0,.16+frame.rect.height*scale/2,0);}
  }).catch(error=>console.warn('[GroundLoot] Equipment artwork',String(error)));
  this.piles.set(drop.id,pile);return pile;
 }
 private label(pile:Pile,item:ItemDef){
  if(!this.labels?.isValid){this.labels=this.hud.node('GroundLootNames',this.hud.root,0,0,1,1);this.labels.setSiblingIndex(0);}
  if(!pile.label?.isValid){
   const unit=sys.isMobile?this.hud.height/(screen.windowSize.height/Math.max(1,screen.devicePixelRatio)):1.25;
   pile.label=this.hud.text(this.labels,equipmentText('loot.groundName',{quality:item.quality,name:item.name}),0,0,280*unit,12*unit,F.color(qualityFeedbackRole(item.quality)),22*unit);
   pile.label.node.name='LootName:'+pile.root.name;pile.label.horizontalAlign=Label.HorizontalAlign.CENTER;pile.label.enableWrapText=false;pile.label.overflow=Label.Overflow.CLAMP;
   pile.label.enableOutline=true;pile.label.outlineColor=F.color('text.outline',245);pile.label.outlineWidth=1.2*unit;
  }
  return pile.label;
 }
 update(game:GameSession,labelsVisible=true){
  if(this.disposed)return;
  const drops=game.state.groundLoot.filter(d=>d.area===game.state.area),ids=new Set(drops.map(d=>d.id));
  for(const [id,pile]of this.piles)if(!ids.has(id)){this.remove(pile);this.piles.delete(id);}
  const names:{drop:GroundLoot;pile:Pile;distance:number}[]=[];
  for(const drop of drops){
   if(!this.piles.has(drop.id)&&Math.hypot(drop.x-game.state.player.x,drop.z-game.state.player.z)>=30)continue;
   const available=game.canPickupLoot(drop),pile=this.piles.get(drop.id)??this.create(drop,available);
   pile.available=available;
   if(!pile.grounded)pile.card.setWorldRotation(this.camera.node.worldRotation);
   pile.root.active=Math.hypot(drop.x-game.state.player.x,drop.z-game.state.player.z)<30;
   if(pile.aura){
    pile.aura.setWorldRotation(this.camera.node.worldRotation);
    const up=this.camera.node.up,h=pile.aura.scale.y/2-.03;pile.aura.setPosition(up.x*h,up.y*h,up.z*h);
    const alpha=this.hud.reducedMotion?228:Math.round(228+12*Math.sin(game.state.time*1.6+pile.yaw));
    if(pile.auraMaterial&&alpha!==pile.alpha){pile.alpha=alpha;this.tint(pile.auraMaterial,F.color(qualityFeedbackRole(EQUIPMENT[drop.item].quality),alpha));}
   }
   if(pile.highlighted){const label=this.label(pile,EQUIPMENT[drop.item]);label.node.active=false;if(pile.root.active&&labelsVisible)names.push({drop,pile,distance:Math.hypot(drop.x-game.state.player.x,drop.z-game.state.player.z)});}
  }
  names.sort((a,b)=>equipmentDropPriority(EQUIPMENT[b.drop.item].quality)-equipmentDropPriority(EQUIPMENT[a.drop.item].quality)||a.distance-b.distance);
  for(const {drop,pile} of names.slice(0,3)){
   this.foot.set(drop.x,this.world.height(drop)+.03,drop.z);this.camera.worldToScreen(this.foot,this.projected);
   const x=this.projected.x/Math.max(1,screen.windowSize.width)*this.hud.width-this.hud.width/2,y=this.projected.y/Math.max(1,screen.windowSize.height)*this.hud.height-this.hud.height/2;
   const unit=sys.isMobile?this.hud.height/(screen.windowSize.height/Math.max(1,screen.devicePixelRatio)):1.25;
   if(!Number.isFinite(x+y)||this.projected.z<0||this.projected.z>1||Math.abs(x)>this.hud.width/2-140*unit||Math.abs(y)>this.hud.height/2-24*unit)continue;
   pile.label!.node.setPosition(x,y-16*unit);pile.label!.node.active=true;
  }
 }
 private remove(pile:Pile){pile.label?.node.destroy();pile.root.destroy();for(const material of pile.materials)material.destroy();for(const mesh of pile.meshes)mesh.destroy();}
 inspect(){return Array.from(this.piles,([id,p])=>({id,visible:p.root.active,available:p.available,art:p.art,grounded:p.grounded,highlighted:p.highlighted,auraReady:!!p.auraMaterial,nameVisible:!!p.label?.node.active,name:p.label?.string,yaw:p.yaw,groundVertices:p.groundVertices,position:{x:p.root.position.x,y:p.root.position.y,z:p.root.position.z},size:{width:p.grounded?p.footprint:p.card.scale.x,height:p.grounded?p.footprint:p.card.scale.y},artReady:!!p.cardMaterial}));}
 destroy(){this.disposed=true;for(const pile of this.piles.values())this.remove(pile);this.piles.clear();if(this.labels?.isValid)this.labels.destroy();}
}
