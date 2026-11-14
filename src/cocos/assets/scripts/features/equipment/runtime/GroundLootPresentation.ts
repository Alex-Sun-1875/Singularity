import {Camera,Color,Material,Mesh,MeshRenderer,Node,SpriteFrame,gfx,primitives,utils} from 'cc';
import type {GameSession,GroundLoot} from '../../../core/GameSession';
import {EQUIPMENT} from '../data/Equipment';
import {SUPPLIES,isSupplyId} from '../data/Supplies';
import {qualityFeedbackRole} from '../../../shared/ui/FeedbackPalette';
import {EquipmentArt} from './EquipmentArt';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UiSkin} from '../../../shared/ui/UiSkin';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';

type Pile={root:Node;card:Node;halo:Node;art:string;grounded:boolean;footprint:number;yaw:number;groundVertices:{x:number;y:number;z:number}[];available:boolean;cardMaterial?:Material;materials:Material[];meshes:Mesh[]};
type GroundArt={drop:GroundLoot;size:number;yaw:number};
const GROUND_CLEARANCE=.008;

/** Authored equipment and physical bottle props, grounded independently of corpses.
 * No colliders or input interception: SceneInteraction owns the pickup button.
 */
export class GroundLootPresentation {
 private piles=new Map<string,Pile>();
 private disposed=false;
 constructor(private world:SceneBuilder,private camera:Camera){}
 private node(name:string,parent:Node){const node=new Node(name);node.layer=this.world.root.layer;parent.addChild(node);return node;}
 private mount(parent:Node,frame:SpriteFrame,tint:Color,pile:Pile,ground?:GroundArt){
  const uv=frame.uv,geometry=primitives.quad();
  geometry.uvs=[uv[0],uv[1],uv[4],uv[5],uv[6],uv[7],uv[2],uv[3]];
  if(ground){
   const positions=geometry.positions!,base=this.world.height(ground.drop),c=Math.cos(ground.yaw),s=Math.sin(ground.yaw);
   // Map the authored top-down cutout onto XZ and sample each terrain corner.
   // Bottle and baked contact shadow share these vertices, so neither can stand up.
   for(let i=0;i<positions.length;i+=3){
    const u=positions[i]*ground.size,v=positions[i+1]*ground.size,x=u*c-v*s,z=u*s+v*c;
    const point={x:ground.drop.x+x,z:ground.drop.z+z},height=this.world.height(point);
    positions[i]=x;positions[i+1]=height-base;positions[i+2]=z;
    pile.groundVertices.push({...point,y:height+GROUND_CLEARANCE});
   }
   geometry.normals=positions.map((_,i)=>i%3===1?1:0);
   geometry.minPos={x:Math.min(...positions.filter((_,i)=>i%3===0)),y:Math.min(...positions.filter((_,i)=>i%3===1)),z:Math.min(...positions.filter((_,i)=>i%3===2))};
   geometry.maxPos={x:Math.max(...positions.filter((_,i)=>i%3===0)),y:Math.max(...positions.filter((_,i)=>i%3===1)),z:Math.max(...positions.filter((_,i)=>i%3===2))};
  }
  const mesh=utils.createMesh(geometry),material=new Material();
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  material.setProperty('mainTexture',frame.texture);material.setProperty('mainColor',tint);
  const renderer=parent.addComponent(MeshRenderer);renderer.mesh=mesh;renderer.setSharedMaterial(material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  pile.meshes.push(mesh);pile.materials.push(material);
  return material;
 }
 private create(drop:GroundLoot,available:boolean){
  const supply=isSupplyId(drop.item)?SUPPLIES[drop.item]:undefined,item=EQUIPMENT[drop.item],role=supply?.feedback??qualityFeedbackRole(item.quality);
  const hash=Array.from(drop.id).reduce((n,c)=>(n*31+c.charCodeAt(0))>>>0,0),yaw=hash*2.399963229728653%(2*Math.PI);
  const root=this.node('GroundLoot:'+drop.id,this.world.root),card=this.node('Item:'+drop.item,root),halo=this.node('Quality',root),pile:Pile={root,card,halo,art:supply?.groundArt??'equipment:'+drop.item,grounded:!!supply,footprint:supply?.groundSize??.8,yaw,groundVertices:[],available,materials:[],meshes:[]};
  root.setPosition(drop.x,this.world.height(drop)+(supply ? GROUND_CLEARANCE : .06),drop.z);
  halo.setRotationFromEuler(-90,0,0);halo.setScale(.95,.95,1);halo.active=!supply;
  if(!supply)void UiSkin.frame('ui/quiet-bronze/skill-soft-halo-v17',0,root).then(frame=>{if(!this.disposed&&this.piles.get(drop.id)===pile&&root.isValid)this.mount(halo,frame,F.color(role,190),pile);}).catch(error=>console.warn('[GroundLoot] Quality marker',String(error)));
  // Supplies only load their physical prop. Equipment retains its existing fallback.
  const artwork=supply?UiSkin.frame(supply.groundArt,0,root):EquipmentArt.itemFrame(item,root).catch(()=>UiSkin.frame('ui/icons/'+(item.kind==='sword'?'attack':item.kind==='bow'?'bow':item.kind==='staff'?'skill':'inventory'),0,root));
  void artwork.then(frame=>{
   if(this.disposed||this.piles.get(drop.id)!==pile||!root.isValid)return;pile.cardMaterial=this.mount(card,frame,Color.WHITE,pile,supply?{drop,size:supply.groundSize,yaw}:undefined);
   if(!supply){const scale=.8/Math.max(frame.rect.width,frame.rect.height);card.setScale(frame.rect.width*scale,frame.rect.height*scale,1);card.setPosition(0,.16+frame.rect.height*scale/2,0);}
  }).catch(error=>console.warn('[GroundLoot] Equipment artwork',String(error)));
  this.piles.set(drop.id,pile);return pile;
 }
 update(game:GameSession){
  if(this.disposed)return;
  const drops=game.state.groundLoot.filter(d=>d.area===game.state.area),ids=new Set(drops.map(d=>d.id));
  for(const [id,pile]of this.piles)if(!ids.has(id)){this.remove(pile);this.piles.delete(id);}
  for(const drop of drops){
   if(!this.piles.has(drop.id)&&Math.hypot(drop.x-game.state.player.x,drop.z-game.state.player.z)>=30)continue;
   const available=game.canPickupLoot(drop),pile=this.piles.get(drop.id)??this.create(drop,available);
   pile.available=available;
   if(!pile.grounded)pile.card.setWorldRotation(this.camera.node.worldRotation);
   pile.root.active=Math.hypot(drop.x-game.state.player.x,drop.z-game.state.player.z)<30;
  }
 }
 private remove(pile:Pile){pile.root.destroy();for(const material of pile.materials)material.destroy();for(const mesh of pile.meshes)mesh.destroy();}
 inspect(){return Array.from(this.piles,([id,p])=>({id,visible:p.root.active,available:p.available,art:p.art,grounded:p.grounded,yaw:p.yaw,groundVertices:p.groundVertices,position:{x:p.root.position.x,y:p.root.position.y,z:p.root.position.z},size:{width:p.grounded?p.footprint:p.card.scale.x,height:p.grounded?p.footprint:p.card.scale.y},artReady:!!p.cardMaterial}));}
 destroy(){this.disposed=true;for(const pile of this.piles.values())this.remove(pile);this.piles.clear();}
}
