import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Color,JsonAsset,Material,Mesh,MeshRenderer,Node,Quat,Rect,Size,SpriteFrame,Texture2D,Vec3,Vec4,gfx,primitives,utils} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {enemyProfile} from '../../combat/common/EnemyCombat';
import {MONSTER_ACTORS} from '../../world/data/MonsterEcology';
import {campaignBattle,type CampaignBeat} from '../../cinematics/data/CampaignScenes';
import type {GameEvent} from '../../../core/Contracts';
import {impactStyle,impactKey,type ImpactStyle} from '../../combat/data/CombatImpact';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {playerActionPose,samplePlayerAction,playerHurtProgress,updateWeaponReadiness,type PlayerActionSample,type PlayerPresentation,type WeaponReadiness} from './PlayerActionPresentation';
import {playerHandOffset} from './PlayerHandAnchors';
import {fieldNpcVisible} from '../../campaign/data/FieldQuests';
import {chapterTwoEnemyRetired} from '../../campaign/common/ChapterTwoEncounters';
import {peacefulBossRetired} from '../../campaign/common/PeacefulBosses';
import {chapterTwoSideQuestNpcVisible} from '../../campaign/data/ChapterTwoSideQuests';

type Origin=[number,number]|{x:number;y:number};
type EquipmentAnchor={x:number;y:number;angle:number};
type MovementEquipment={image:string;hands?:Record<string,FlatAction>;weapons:Record<string,Partial<Record<'held'|'stowed'|'quiver',FlatAction>>>};
type FrameOrigins=Origin[]|Record<string,Origin|Origin[]>;
export type FlatAction={image?:string;frameImages?:string[];frameWidth?:number;frameHeight?:number;perFrameRects?:[number,number,number,number][];frameRectsByImage?:Record<string,[number,number,number,number][]>;origin?:Origin;frames?:number;fps?:number;columns?:number;frameIndices?:number[];directionFrameIndices?:number[];phaseStarts?:number[];worldUnitsPerPixel?:number;loop?:boolean;row?:number;absoluteFrameIndices?:boolean;perFrameOrigins?:FrameOrigins;alphaBounds?:number[][];nominalSpeedMetresPerSecond?:number;equipmentLayer?:'held'|'stowed';equipmentAnchors?:Partial<Record<'held'|'stowed',Record<string,EquipmentAnchor[]>>>;sharedBody?:string;handOcclusion?:string};
export type FlatActorManifest={frameWidth:number;frameHeight:number;origin:Origin;directions:string[];columns?:number;image?:string;alphaThreshold?:number;edgeWidth?:number;perFrameOrigins?:FrameOrigins;alphaBounds?:number[][];frameScaleFactors?:Record<string,number[]>;camera?:{worldUnitsPerPixel?:number};actions:Record<string,FlatAction>;movementEquipment?:MovementEquipment};
type FlatFrame={frame:SpriteFrame;mesh:Mesh;texture:Texture2D;origin:[number,number];index:number;scaleFactor:number};
type CachedFrame={key:string;plain:FlatFrame;meshed?:FlatFrame};
type FlatAsset={id:string;manifest:FlatActorManifest;textures:Map<string,Texture2D>;frames:Map<string,SpriteFrame>;meshes:Map<string,Mesh>;samples:WeakMap<FlatAction,Map<number,Map<number,CachedFrame>>>};
export type FlatActor={root:Node;model:Node;sprite:Node;renderer:MeshRenderer;material:Material;quadFrame?:SpriteFrame;quadTiling?:Vec4;edgeMaterial?:Material;edges?:{node:Node;renderer:MeshRenderer;x:number;y:number}[];id:string;modelId:string;asset:FlatAsset;state:string;requestedAction:string;sampledAction:string;clock:number;frame:number;ordinal:number;progress?:number;direction:number;facingAngle?:number;facingRevision?:number;angle:number;speed:number;actionId?:string;renderedWeaponId?:string;phase?:string;phaseDuration?:number;enemyPose?:string;motion?:PlayerActionSample;reusedConcept:boolean;equipment?:{root:Node;sprite:Node;renderer:MeshRenderer;handSprite:Node;handRenderer:MeshRenderer;backRoot:Node;backSprite:Node;backRenderer:MeshRenderer;material:Material}};
export type FlatPortrait={frame:SpriteFrame;texture:Texture2D;rect:Rect;origin:[number,number];worldUnitsPerPixel:number;conceptAsset:string;bounds?:number[]};

const RESOURCE='flat2d/characters/';
const LAYER=1<<18;
const ENEMY_TEMPLATE_CONCEPTS:Record<string,string>={"R1-1":"raider","R1-2":"raider-shield","R1-3":"raider-archer","BOSS_R1":"captain","R2-1":"mine-worker","R2-3":"mine-crawler","R1-4":"r1-4","R2-2":"r2-2","R2-4":"r2-4","R3-1":"r3-1","R3-2":"r3-2","R3-3":"r3-3","R3-4":"r3-4","R4-1":"r4-1","R4-2":"r4-2","R4-3":"r4-3","R4-4":"r4-4","U1-1":"u1-1","U1-2":"u1-2","U1-3":"u1-3","U1-4":"u1-4","U2-1":"u2-1","U2-2":"u2-2","U2-3":"u2-3","U2-4":"u2-4","BOSS_R2":"boss-r2","BOSS_R3":"boss-r3","BOSS_R4":"boss-r4","ELITE_01":"elite-01","ELITE_02":"elite-02","ELITE_03":"elite-03","ELITE_04":"elite-04","ELITE_05":"elite-05","ELITE_06":"elite-06","ELITE_07":"elite-07","ELITE_08":"elite-08"};
const LEGACY_ENEMY_CONCEPTS:Record<string,string>={captain:'captain',archer:'raider-archer',shield:'raider-shield'};
// These source sheets have one authored primary action, not a separate drawing
// for every move. Reuse that character's action for secondary moves explicitly;
// a future independently authored pose takes precedence in action().
const ENEMY_PRIMARY_POSE_ADAPTERS:Record<string,Record<string,string>>={
 'r2-4':{attack_sword:'interact'},'r4-4':{interact:'attack_sword'},
 'boss-r3':{attack_sword:'spell'},'boss-r4':{interact:'attack_sword'},
 'elite-01':{interact:'attack_sword'},'elite-02':{interact:'attack_bow'},
 'elite-03':{interact:'attack_sword'},'elite-04':{interact:'attack_sword'},
 'elite-05':{spell:'attack_sword'},'elite-06':{spell:'attack_sword_step2'},'elite-07':{spell:'attack_sword'},
};
Object.assign(ENEMY_TEMPLATE_CONCEPTS,MONSTER_ACTORS);
const ENEMY_CONCEPTS=new Set(Object.values(ENEMY_TEMPLATE_CONCEPTS));
const CONCEPTS=new Set(['raphael','mira','lorn','nightqi','kael','evelyn'].concat(Array.from(ENEMY_CONCEPTS)));
const enemyConcept=(enemy:{templateId?:string;bossId?:string;contentId?:string;kind:string})=>ENEMY_TEMPLATE_CONCEPTS[enemy.templateId??enemy.bossId??enemy.contentId??'']??LEGACY_ENEMY_CONCEPTS[enemy.kind]??'raider';
const clamp=(n:number)=>Math.max(0,Math.min(1,n));
const xy=(origin:Origin|undefined,fallback:[number,number]):[number,number]=>Array.isArray(origin)?[origin[0],origin[1]]:origin&&'x'in origin?[origin.x,origin.y]:fallback;
const imageName=(name:string)=>name.replace(/\\/g,'/').replace(/^\.\//,'').replace(/\.(png|webp|jpg|jpeg)$/i,'');
const normalDirection=(name:string)=>name.toLowerCase().replace(/[\s_-]/g,'');
const directionAngles:Record<string,number>={up:0,upright:Math.PI/4,right:Math.PI/2,downright:Math.PI*3/4,down:Math.PI,downleft:-Math.PI*3/4,left:-Math.PI/2,upleft:-Math.PI/4};
const weaponFamily=(id:string):'bow'|'staff'|'sword'=>EQUIPMENT[id]?.kind==='bow'?'bow':EQUIPMENT[id]?.kind==='staff'?'staff':'sword';
const MONSTER_CONCEPTS=new Set(Object.values(MONSTER_ACTORS));
// Cocos transform setters invalidate descendants even if the values match.
const position=(node:Node,x:number,y:number,z:number)=>{const p=node.position;if(p.x!==x||p.y!==y||p.z!==z)node.setPosition(x,y,z);};
const scale=(node:Node,x:number,y:number,z:number)=>{const s=node.scale;if(s.x!==x||s.y!==y||s.z!==z)node.setScale(x,y,z);};
const faceCamera=(node:Node,camera:Camera)=>{const rotation=camera.node.worldRotation;if(!Quat.equals(node.worldRotation,rotation))node.setWorldRotation(rotation);};
const setActorTint=(actor:FlatActor,r:number,g:number,b:number,a:number)=>{
 const current=actor.material.getProperty('mainColor')as Color|Vec4;
 const x=current instanceof Color?current.r/255:current.x,y=current instanceof Color?current.g/255:current.y,z=current instanceof Color?current.b/255:current.z,w=current instanceof Color?current.a/255:current.w;
 if(x!==r||y!==g||z!==b||w!==a)actor.material.setProperty('mainColor',new Vec4(r,g,b,a));
};

/** Concept-image characters in the existing metre-based world; no model assets.
 * Native quad meshes reuse SpriteFrame UVs with the already bundled unlit
 * transparent technique. The holder is the ground anchor; a camera-facing
 * child carries the image and its per-frame foot correction.
 */
export class FlatActors {
 private active=new Map<string,FlatActor>();
 private arriving=new Set<string>();private arrivalFailure=new Set<string>();
 private assets=new Map<string,FlatAsset>();
 private pending=new Map<string,Promise<FlatAsset>>();
 private enemyTextures=new Set<Texture2D>();
 private readonly quad:Mesh;
 private disposed=false;
 private carryReadiness:WeaponReadiness={ready:false,until:-Infinity};
 private combatReady=false;
 reducedMotion=false;
 private impacts=new Map<string,{start:number;style:ImpactStyle;angle:number}>();
 private hurtUntil=new Map<string,number>();
 private electricHurt=new Set<string>();
 private defeatedUntil=new Map<string,number>();
 private readonly frameEnemies=new Map<string,GameSession['state']['enemies'][number]>();
 private readonly directionTargets=new WeakMap<string[],number[]>();
 private facingRotation:Quat|undefined;private facingRevision=0;
 constructor(readonly scene:Node,readonly world:SceneBuilder,readonly camera:Camera,private readonly omitPlayer=false){this.quad=utils.createMesh(primitives.quad(),undefined,{calculateBounds:true});this.quad.name='FlatActorSharedQuad';}
 onCombatEvents(events:readonly GameEvent[],time:number){
  const blocked=new Set(events.filter(e=>e.type==='block').map(impactKey));
  const electric=new Set(events.filter(e=>e.type==='skill_hit'&&String(e.skillId).startsWith('THU_')).map(e=>String(e.targetId)));
  for(const event of events){
   if(event.type==='area'){this.impacts.clear();this.hurtUntil.clear();this.electricHurt.clear();this.defeatedUntil.clear();continue;}
   if(!event.id||!this.active.has(event.id))continue;
   const impact=impactStyle(event,blocked.has(impactKey(event)));if(impact){const previous=this.impacts.get(event.id);if(!previous||time-previous.start>.07||impact.priority>previous.style.priority)this.impacts.set(event.id,{start:time,style:impact,angle:Number(event.angle??0)});}
   if(event.type==='hit'&&Number(event.hpLost)>0){this.hurtUntil.set(event.id,time+.16);if(electric.has(event.id))this.electricHurt.add(event.id);else this.electricHurt.delete(event.id);}
   if(event.type==='defeat')this.defeatedUntil.set(event.id,time+.4);
  }
 }
 private concept(modelId:string):string {
  if(!CONCEPTS.has(modelId))throw new Error(`Missing independent flat character artwork for '${modelId}'; add ${RESOURCE}${modelId}/manifest and its own concept images`);
  return modelId;
 }
 async load(modelId:string):Promise<FlatAsset>{
  if(this.disposed)throw new Error('Flat actors were destroyed before loading '+modelId);
  const id=this.concept(modelId),cached=this.assets.get(id);if(cached)return cached;
  const pending=this.pending.get(id);if(pending)return pending;
  const promise=(async()=>{
   const json=await new Promise<JsonAsset>((resolve,reject)=>this.world.loadAsset(RESOURCE+id+'/manifest',JsonAsset,(error,asset)=>error?reject(new Error(`Missing independent flat character '${id}': ${error.message}`)):resolve(asset)));
   const manifest=json.json as FlatActorManifest;
   if(!(manifest.frameWidth>0&&manifest.frameHeight>0&&manifest.directions?.length&&manifest.actions?.idle))throw new Error('Invalid flat concept manifest: '+id);
   for(const [image,factors]of Object.entries(manifest.frameScaleFactors??{}))if(!Array.isArray(factors)||factors.some(value=>!Number.isFinite(value)||value<=0))throw new Error(`Invalid flat frame scale: ${id}/${image}`);
   for(const[name,action]of Object.entries(manifest.actions)){
    const count=action.frameIndices?.length??action.frames??1,starts=action.phaseStarts;
    if(count<1||!Number.isInteger(count))throw new Error(`Invalid flat frame count: ${id}/${name}`);
    if(action.frameImages&&(action.frameImages.length!==count||action.frameImages.some(image=>typeof image!=='string'||!image)))throw new Error(`Invalid flat frameImages: ${id}/${name}`);
    if(starts&&(starts.length!==count||starts[0]!==0||starts.some((value,index)=>!Number.isFinite(value)||value<0||value>1||(index>0&&value<starts[index-1]))))throw new Error(`Invalid normalized phaseStarts: ${id}/${name}`);
    if(action.worldUnitsPerPixel!==undefined&&(!Number.isFinite(action.worldUnitsPerPixel)||action.worldUnitsPerPixel<=0))throw new Error(`Invalid flat worldUnitsPerPixel: ${id}/${name}`);
   }
   const names=new Set(Object.values(manifest.actions).flatMap(a=>(a.frameImages??[a.image??manifest.image??'atlas.png']).map(imageName)));
   if(manifest.movementEquipment)names.add(imageName(manifest.movementEquipment.image));
   const textures=new Map<string,Texture2D>();
   await Promise.all(Array.from(names,async name=>{
    const texture=await new Promise<Texture2D>((resolve,reject)=>this.world.loadAsset(RESOURCE+id+'/'+name+'/texture',Texture2D,(error,asset)=>{
     if(error){reject(error);return;}
     // Dynamic SpriteFrames/material texture properties do not own loader refs.
     // Each scene instance owns one ref per unique enemy texture. Hero/NPC
     // textures are shared with inventory portraits and are excluded here.
     if(ENEMY_CONCEPTS.has(id)){
      if(this.disposed){asset.addRef();asset.decRef();reject(new Error('Flat enemy texture arrived after scene disposal: '+id));return;}
      if(!this.enemyTextures.has(asset)){asset.addRef();this.enemyTextures.add(asset);}
     }else if(this.disposed){reject(new Error('Flat actor texture arrived after scene disposal: '+id));return;}
     resolve(asset);
    }));
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);textures.set(name,texture);
   }));
   const asset:FlatAsset={id,manifest,textures,frames:new Map(),meshes:new Map(),samples:new WeakMap()};
   if(!this.disposed)this.assets.set(id,asset);return asset;
  })().catch(error=>{this.pending.delete(id);throw error;});
  this.pending.set(id,promise);return promise;
 }
 private action(asset:FlatAsset,requested:string):[string,FlatAction]{
  const actions=asset.manifest.actions;
  if(actions[requested])return[requested,actions[requested]];
  const primary=ENEMY_PRIMARY_POSE_ADAPTERS[asset.id]?.[requested];
  if(primary&&actions[primary])return[primary,actions[primary]];
  if(requested==='attack_bow'&&actions.idle_bow)return['idle_bow',actions.idle_bow];
  if(requested==='attack_staff'&&actions.idle_staff)return['idle_staff',actions.idle_staff];
  if((requested==='run'||requested==='dodge')&&actions.walk)return['walk',actions.walk];
  return['idle',actions.idle];
 }
 private movementAction(actor:FlatActor,state:string,weapon:string,weaponId:string):string{
  weaponId=EQUIPMENT[weaponId]?.artSource??weaponId;
  const actions=actor.asset.manifest.actions;
  if(actions[state+'_'+weaponId])return state+'_'+weaponId;
  if(weapon==='sword')return state;
  const candidates=[state+'_'+weapon,...(state==='run'?['walk_'+weapon]:[]),'idle_'+weapon];
  for(const candidate of candidates)if(actions[candidate])return candidate;
  throw new Error(`Missing held-${weapon} ${state} image for ${actor.modelId}; refusing a sword-pose substitution`);
 }
 private updateCombatReady(game:GameSession){
  this.combatReady=updateWeaponReadiness(this.carryReadiness,game,this.world);
 }
 private playerAction(actor:FlatActor,state:string,weapon:string,weaponId:string):string{
  // Reuse only the authored item artwork or its registered art alias.
  weaponId=EQUIPMENT[weaponId]?.artSource??weaponId;
  const exploration='explore_'+state+'_'+weaponId;
  if(!this.combatReady&&['idle','walk','run','dodge','interact'].includes(state)&&actor.asset.manifest.actions[exploration])return exploration;
  return ['idle','walk','run'].includes(state)?this.movementAction(actor,state,weapon,weaponId):actor.asset.manifest.actions[state+'_'+weaponId]?state+'_'+weaponId:state;
 }
 private origin(asset:FlatAsset,action:FlatAction,direction:number,index:number,ordinal:number):[number,number]{
  const manifest=asset.manifest,fallback=xy(action.origin??manifest.origin,[(action.frameWidth??manifest.frameWidth)/2,action.frameHeight??manifest.frameHeight]);
  const origins=action.perFrameOrigins??manifest.perFrameOrigins;if(!origins)return fallback;
  if(Array.isArray(origins))return xy(origins[index],fallback);
  const value=origins[manifest.directions[direction]]??origins[String(index)];
  if(Array.isArray(value)&&Array.isArray(value[0]))return xy((value as Origin[])[ordinal],fallback);
  return xy(value as Origin|undefined,fallback);
 }
 private frame(asset:FlatAsset,action:FlatAction,direction:number,ordinal:number,withMesh=true):FlatFrame{
  // Loaded manifests are immutable. Share their exact sample metadata across
  // actors/head queries; keep animation clocks and live transforms uncached.
  let directions=asset.samples.get(action);
  if(!directions){directions=new Map();asset.samples.set(action,directions);}
  let ordinals=directions.get(direction);
  if(!ordinals){ordinals=new Map();directions.set(direction,ordinals);}
  let cached=ordinals.get(ordinal);
  if(!cached){
   const m=asset.manifest,name=imageName(action.frameImages?.[ordinal]??action.image??m.image??'atlas.png'),texture=asset.textures.get(name)!;
   const cellWidth=action.frameWidth??m.frameWidth,cellHeight=action.frameHeight??m.frameHeight;
   const columns=action.columns??m.columns??Math.max(1,Math.floor(texture.width/cellWidth));
   const column=action.frameIndices?.[ordinal]??ordinal;
   const index=action.directionFrameIndices?.[direction]??(action.absoluteFrameIndices?column:(action.row??direction)*columns+column);
   const rect=action.frameRectsByImage?.[name]?.[index]??action.perFrameRects?.[index],x=rect?.[0]??index%columns*cellWidth,y=rect?.[1]??Math.floor(index/columns)*cellHeight,width=rect?.[2]??cellWidth,height=rect?.[3]??cellHeight;
   if(x<0||y<0||x+width>texture.width||y+height>texture.height)throw new Error(`Flat concept frame outside atlas: ${asset.id}/${name}/${index}`);
   const key=name+':'+index+':'+[x,y,width,height].join(',');let frame=asset.frames.get(key);
   if(!frame){frame=new SpriteFrame();frame.name=asset.id+':'+key;frame.reset({texture,rect:new Rect(x,y,width,height),originalSize:new Size(width,height)});frame.packable=false;asset.frames.set(key,frame);}
   cached={key,plain:{frame,mesh:this.quad,texture,origin:this.origin(asset,action,direction,index,ordinal),index,scaleFactor:m.frameScaleFactors?.[name]?.[index]??1}};
   ordinals.set(ordinal,cached);
  }
  if(!withMesh)return cached.plain;
  if(cached.meshed)return cached.meshed;
  const {frame}=cached.plain;
  let mesh=asset.meshes.get(cached.key);
  if(!mesh){
   const geometry=primitives.quad(),uv=frame.uv;
   // SpriteFrame.uv is BL, BR, TL, TR (the same order as native Sprite's
   // simple assembler). Native quad vertices are BL, TL, TR, BR.
   geometry.uvs=[uv[0],uv[1],uv[4],uv[5],uv[6],uv[7],uv[2],uv[3]];
   mesh=utils.createMesh(geometry,undefined,{calculateBounds:true});asset.meshes.set(cached.key,mesh);
  }
  return cached.meshed={...cached.plain,mesh};
 }
 private showEquipment(actor:FlatActor,action:FlatAction,direction:number,ordinal:number){
  const carry=action.equipmentLayer,definition=actor.asset.manifest.movementEquipment;
  if(actor.id!=='player'||!carry||!definition){if(actor.equipment){actor.equipment.root.active=false;actor.equipment.handSprite.active=false;actor.equipment.backRoot.active=false;}return;}
  const weapon=actor.renderedWeaponId??'W01',fallback=weaponFamily(weapon)==='bow'?'W07':weaponFamily(weapon)==='staff'?'W11':'W01';
  const item=definition.weapons[weapon]?.[carry]??definition.weapons[EQUIPMENT[weapon]?.artSource??weapon]?.[carry]??definition.weapons[fallback]?.[carry];
  const facing=actor.asset.manifest.directions[direction],anchor=action.equipmentAnchors?.[carry]?.[facing]?.[ordinal];
  if(!item||!anchor)throw new Error(`Missing shared locomotion weapon/socket: ${weapon}/${carry}/${facing}/${ordinal}`);
  if(!actor.equipment){
   const root=new Node('MovementWeaponSocket'),sprite=new Node('MovementWeaponImage');root.layer=LAYER;sprite.layer=LAYER;actor.model.addChild(root);root.addChild(sprite);
   const material=new Material();material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_ALPHA_TEST:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
   material.setProperty('mainColor',Color.WHITE);material.setProperty('alphaThreshold',actor.asset.manifest.alphaThreshold??.025);
   const renderer=sprite.addComponent(MeshRenderer);renderer.setSharedMaterial(material,0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   const handSprite=new Node('MovementGripOcclusion');handSprite.layer=LAYER;actor.model.addChild(handSprite);const handRenderer=handSprite.addComponent(MeshRenderer);handRenderer.setSharedMaterial(material,0);handRenderer.priority=0;handRenderer.shadowCastingMode=0;handRenderer.receiveShadow=0;
   const backRoot=new Node('MovementQuiverSocket'),backSprite=new Node('MovementQuiverImage');backRoot.layer=LAYER;backSprite.layer=LAYER;actor.model.addChild(backRoot);backRoot.addChild(backSprite);const backRenderer=backSprite.addComponent(MeshRenderer);backRenderer.setSharedMaterial(material,0);backRenderer.priority=0;backRenderer.shadowCastingMode=0;backRenderer.receiveShadow=0;
   actor.equipment={root,sprite,renderer,handSprite,handRenderer,backRoot,backSprite,backRenderer,material};
  }
  const gear=actor.equipment,sample=this.frame(actor.asset,item,direction,0),upp=item.worldUnitsPerPixel??.0025,w=sample.frame.rect.width,h=sample.frame.rect.height;
  gear.root.active=true;gear.root.setPosition(anchor.x,anchor.y,(carry==='held'?normalDirection(facing)!=='up':normalDirection(facing)==='up')?.045:.025);gear.root.setRotationFromEuler(0,0,anchor.angle);
  gear.sprite.setScale(w*upp,h*upp,1);gear.sprite.setPosition((w/2-sample.origin[0])*upp,(sample.origin[1]-h/2)*upp,0);
  if(gear.renderer.mesh!==sample.mesh)gear.renderer.mesh=sample.mesh;
  if(gear.material.getProperty('mainTexture')!==sample.texture)gear.material.setProperty('mainTexture',sample.texture);
  const quiver=carry==='held'?(definition.weapons[weapon]?.quiver??definition.weapons[EQUIPMENT[weapon]?.artSource??weapon]?.quiver??definition.weapons[fallback]?.quiver):undefined,backAnchor=action.equipmentAnchors?.stowed?.[facing]?.[ordinal];gear.backRoot.active=!!quiver&&!!backAnchor;
  if(quiver&&backAnchor){const back=this.frame(actor.asset,quiver,direction,0),unit=quiver.worldUnitsPerPixel??.0025,bw=back.frame.rect.width,bh=back.frame.rect.height;gear.backRoot.setPosition(backAnchor.x,backAnchor.y,normalDirection(facing)==='up'?.045:.025);gear.backRoot.setRotationFromEuler(0,0,backAnchor.angle);gear.backSprite.setScale(bw*unit,bh*unit,1);gear.backSprite.setPosition((bw/2-back.origin[0])*unit,(back.origin[1]-bh/2)*unit,0);if(gear.backRenderer.mesh!==back.mesh)gear.backRenderer.mesh=back.mesh;}
  const handDef=definition.hands?.[action.handOcclusion??''];gear.handSprite.active=!!handDef;
  if(handDef){const hand=this.frame(actor.asset,handDef,direction,ordinal),unit=handDef.worldUnitsPerPixel??.004,hw=hand.frame.rect.width,hh=hand.frame.rect.height;gear.handSprite.setScale(hw*unit,hh*unit,1);gear.handSprite.setPosition((hw/2-hand.origin[0])*unit,(hand.origin[1]-hh/2)*unit,.055);if(gear.handRenderer.mesh!==hand.mesh)gear.handRenderer.mesh=hand.mesh;}
 }
 async create(id:string,modelId:string,x:number,z:number):Promise<FlatActor|undefined>{
  const asset=await this.load(modelId);if(this.disposed||!this.world.root.isValid)return;
  const previous=this.active.get(id);if(previous)return previous;
  const root=new Node(id),model=new Node('FlatConcept:'+modelId),sprite=new Node('ConceptImage');
  this.world.root.addChild(root);root.setPosition(x,this.world.height({x,z}),z);root.addChild(model);model.addChild(sprite);
  for(const node of[root,model,sprite])node.layer=LAYER;
  const material=new Material();material.name='FlatConcept:'+id;
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_ALPHA_TEST:!!asset.manifest.alphaThreshold},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  if(!material.passes.length){root.destroy();material.destroy();throw new Error('Flat actor requires the bundled builtin-unlit transparent technique');}
  material.setProperty('mainColor',Color.WHITE);
  // Some generated cutouts retain 1–5/255 alpha in otherwise empty pixels.
  // The native shader discards that noise without changing source image bytes.
  if(asset.manifest.alphaThreshold)material.setProperty('alphaThreshold',asset.manifest.alphaThreshold);
  const renderer=sprite.addComponent(MeshRenderer);renderer.setSharedMaterial(material,0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  const actor:FlatActor={root,model,sprite,renderer,material,id,modelId,asset,state:'idle',requestedAction:'idle',sampledAction:'idle',clock:0,frame:-1,ordinal:0,direction:-1,angle:Math.atan2(-this.camera.node.forward.x,-this.camera.node.forward.z),speed:0,reusedConcept:false};
  const edgeWidth=id==='player'?asset.manifest.edgeWidth??0:0;
  if(edgeWidth>0){
   // Reuse native cutout quads for a subpixel dark contour on busy ground.
   // The four offsets share the current frame/texture, rather than a second atlas.
   const edgeMaterial=new Material();edgeMaterial.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_ALPHA_TEST:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
   edgeMaterial.setProperty('mainColor',new Color(8,13,19,180));edgeMaterial.setProperty('alphaThreshold',asset.manifest.alphaThreshold??.025);actor.edgeMaterial=edgeMaterial;
   actor.edges=[[-edgeWidth,0],[edgeWidth,0],[0,-edgeWidth],[0,edgeWidth]].map(([x,y])=>{
    const node=new Node('ReadabilityEdge');node.layer=LAYER;model.addChild(node);const edge=node.addComponent(MeshRenderer);edge.setSharedMaterial(edgeMaterial,0);edge.priority=0;edge.shadowCastingMode=0;edge.receiveShadow=0;return{node,renderer:edge,x,y};
   });
  }
  try{this.show(actor,'idle',0);this.active.set(id,actor);return actor;}catch(error){root.destroy();actor.edgeMaterial?.destroy();material.destroy();throw error;}
 }
 async build(game:GameSession,onProgress?:(completed:number,total:number)=>void){
  const s=game.state,requests=this.omitPlayer?[]:[this.create('player','raphael',s.player.x,s.player.z)];
  const scheduled=new Set<string>(['player']);
  for(const object of this.world.area.objects){if(!object.actor)continue;const id=object.actor.toLowerCase();if(scheduled.has(id))continue;scheduled.add(id);requests.push(this.create(id,object.actorModel??id,object.x+(object.action==='meeting'?2.3:0),object.z).then(actor=>{if(actor&&id.startsWith('field-npc-'))actor.root.active=fieldNpcVisible(id,s.flags);return actor;}));}
  if(this.world.area.id==='U1-04')for(const[id,x,z]of[['mira',-3,3],['kael',3,3]]as const)if(!scheduled.has(id)){scheduled.add(id);requests.push(this.create(id,id,x,z));}
  for(const enemy of s.enemies)requests.push(this.create(enemy.id,enemyConcept(enemy),enemy.x,enemy.z));
  for(const wave of campaignBattle(s.area)?.waves??[])for(const enemy of wave.enemies)requests.push(this.load(enemyConcept(enemy)).then(()=>undefined));
  if(['H08','U1-06'].includes(s.area))for(let i=0;i<3;i++)requests.push(this.create('campaign-sentry-'+i,'u1-1',s.player.x+(i-1)*2.3,s.player.z+5).then(actor=>{if(actor)actor.root.active=false;return actor;}));
  if(s.area==='H03')for(let i=0;i<3;i++)requests.push(this.create('campaign-worker-'+i,'mine-worker',(i-1)*5,-16));
  let completed=0;await Promise.all(requests.map(request=>request.then(result=>{onProgress?.(++completed,requests.length);return result;})));
  // The loading/menu pause can precede the first gameplay update. Sample the
  // actual equipped item now rather than leaving a default sword on restores.
  this.update(game,0,false);
 }
 private direction(actor:FlatActor):number{
  const rotation=this.camera.node.worldRotation,previous=this.facingRotation;
  if(!previous||previous.x!==rotation.x||previous.y!==rotation.y||previous.z!==rotation.z||previous.w!==rotation.w){if(previous)previous.set(rotation);else this.facingRotation=rotation.clone();this.facingRevision++;}
  // Keep animation clocks/recoil at full rate. Only the identical camera/angle
  // calculation is reused, so authored frame and facing changes stay immediate.
  if(actor.direction>=0&&actor.facingAngle===actor.angle&&actor.facingRevision===this.facingRevision)return actor.direction;
  const angle=actor.angle,directions=actor.asset.manifest.directions;
  let targets=this.directionTargets.get(directions);if(!targets){targets=directions.map(name=>directionAngles[normalDirection(name)]??0);this.directionTargets.set(directions,targets);}
  const dx=Math.sin(angle),dz=Math.cos(angle),right=this.camera.node.right,up=this.camera.node.up;
  const screen=Math.atan2(dx*right.x+dz*right.z,dx*up.x+dz*up.z);
  let best=0,distance=Infinity;
  for(let index=0;index<targets.length;index++){const target=targets[index],d=Math.abs(Math.atan2(Math.sin(screen-target),Math.cos(screen-target)));if(d<distance){best=index;distance=d;}}
  actor.facingAngle=angle;actor.facingRevision=this.facingRevision;
  return best;
 }
 private show(actor:FlatActor,state:string,dt:number,progress?:number,restart=false,requested=state){
  if(actor.state!==state||actor.requestedAction!==requested||restart){
   // Drawing or stowing a weapon must not restart an otherwise continuous stride.
   if(actor.state!==state||restart||!['walk','run'].includes(state))actor.clock=0;
   else actor.clock+=dt;
   actor.state=state;actor.requestedAction=requested;
  }else actor.clock+=dt;
  const[name,action]=this.action(actor.asset,requested),count=action.frameIndices?.length??action.frames??1;
  const loop=action.loop??['idle','walk','run'].includes(state);
  let ordinal=loop?Math.floor(actor.clock*(action.fps??8))%count:Math.min(count-1,Math.floor(actor.clock*(action.fps??8)));
  if(progress!==undefined){
   const p=clamp(progress),starts=action.phaseStarts;
   if(starts){ordinal=0;for(let i=1;i<starts.length&&starts[i]<=p;i++)ordinal=i;}
   else ordinal=Math.min(count-1,Math.floor(p*count));
   // 每张图集自己的阶段索引决定拉弓、释放与收势；玩家蓄力进度止于.74。
  }
  const direction=this.direction(actor);
  faceCamera(actor.model,this.camera);
  // Preserve the full animation clock and phase. Atlas geometry only changes
  // on an authored frame/direction change; recoil/flash still update below.
  if(actor.id!=='player'&&actor.frame>=0&&actor.sampledAction===name&&actor.direction===direction&&actor.ordinal===ordinal){actor.progress=progress;return;}
  const sample=this.frame(actor.asset,action,direction,ordinal,false);actor.sampledAction=name;
  const upp=(action.worldUnitsPerPixel??actor.asset.manifest.camera?.worldUnitsPerPixel??.008)*sample.scaleFactor;
  // primitives.quad is one metre at unit scale; SpriteFrame's UI pixelsToUnit
  // is intentionally not part of this geometry's size conversion.
  const width=sample.frame.rect.width,height=sample.frame.rect.height;
  scale(actor.sprite,width*upp,height*upp,1);
  position(actor.sprite,(width/2-sample.origin[0])*upp,(sample.origin[1]-height/2)*upp,.035);
  if(actor.renderer.mesh!==this.quad)actor.renderer.mesh=this.quad;
  // Every body frame is the same quad. Move its atlas rectangle through the
  // existing unlit UV uniform, retaining native SubModels and uniform buffers.
  if(actor.quadFrame!==sample.frame){const uv=sample.frame.uv,tiling=actor.quadTiling??(actor.quadTiling=new Vec4());tiling.set(uv[2]-uv[0],uv[5]-uv[1],uv[0],uv[1]);actor.material.setProperty('tilingOffset',tiling);actor.edgeMaterial?.setProperty('tilingOffset',tiling);actor.quadFrame=sample.frame;}
  if(actor.material.getProperty('mainTexture')!==sample.texture)actor.material.setProperty('mainTexture',sample.texture);
  this.showEquipment(actor,action,direction,ordinal);
  if(actor.edges){
   if(actor.edgeMaterial!.getProperty('mainTexture')!==sample.texture)actor.edgeMaterial!.setProperty('mainTexture',sample.texture);
   for(const edge of actor.edges){scale(edge.node,actor.sprite.scale.x,actor.sprite.scale.y,1);position(edge.node,actor.sprite.position.x+edge.x,actor.sprite.position.y+edge.y,.03);if(edge.renderer.mesh!==this.quad)edge.renderer.mesh=this.quad;}
  }
  actor.direction=direction;actor.frame=sample.index;actor.ordinal=ordinal;actor.progress=progress;
 }
 update(game:GameSession,dt:number,moving:boolean,paused=false,moveAmount=1){
  if(this.disposed)return;
  const enemies=game.state.enemies;
  if(this.frameEnemies.size!==enemies.length||enemies.some(enemy=>!this.frameEnemies.has(enemy.id)))this.frameEnemies.clear();
  for(const enemy of enemies)this.frameEnemies.set(enemy.id,enemy);
  for(const actor of this.active.values()){if(chapterTwoEnemyRetired(game.state,actor.id)||peacefulBossRetired(game.state,actor.id))actor.root.active=false;else if(actor.id.startsWith('field-npc-'))actor.root.active=fieldNpcVisible(actor.id,game.state.flags);else if(actor.id.startsWith('side-npc-'))actor.root.active=chapterTwoSideQuestNpcVisible(actor.id,game.state);}
  if(paused){this.impacts.clear();for(const actor of this.active.values())if(actor.id!=='player'&&!(this.frameEnemies.get(actor.id)?.hp<=0)){scale(actor.model,1,1,1);if(actor.sprite.eulerAngles.z!==0)actor.sprite.setRotationFromEuler(0,0,0);setActorTint(actor,1,1,1,1);}
   // Preserve sampled ordinals/progress as well as clocks. Re-sampling from
   // FPS here would jump a manually held bow pose backwards while paused.
   const player=this.active.get('player'),equipped=game.state.equipment.weapon;
   if(player&&player.renderedWeaponId!==equipped){
    // Equipment menus freeze time, but their changed item must appear now.
    // Begin a complete idle pose for the new item, never an old bow phase.
    const weapon=weaponFamily(equipped);
    player.renderedWeaponId=equipped;
    this.show(player,'idle',0,undefined,true,this.playerAction(player,'idle',weapon,equipped));
    player.renderedWeaponId=equipped;player.actionId=undefined;
   }
   for(const actor of this.active.values())if(!(this.frameEnemies.get(actor.id)?.hp<=0))faceCamera(actor.model,this.camera);
   return;
  }
  const p=game.state.player,action=game.state.action,player=this.active.get('player');
  if(player){
   this.updateCombatReady(game);
   const dx=p.x-player.root.position.x,dz=p.z-player.root.position.z,speed=Math.hypot(dx,dz)/Math.max(.001,dt);player.speed=speed;
   player.angle=action&&action.kind!=='bowAim'?action.angle:moving&&speed>.08?Math.atan2(dx,dz):p.angle;
   position(player.root,p.x,this.world.height(p),p.z);
   const weapon=weaponFamily(game.state.equipment.weapon);
   const hurtProgress=playerHurtProgress(p.hurtTime),flinch=p.hp>0&&hurtProgress!==undefined;
   // Input selects the gait; actual displacement only determines whether the
   // feet should move. Capsule contacts/slopes must not turn a full run into a walk.
   const gait=moving?moveAmount>.7?'run':'walk':speed>2.5?'run':'walk';
   let state=p.hp<=0?'death':flinch?'hit':speed>.08?gait:'idle';
   if(p.hp>0&&action&&!flinch)state=playerActionPose(action,weapon);
   const equipped=game.state.equipment.weapon;
   let variant=this.playerAction(player,state,weapon,equipped),progress:number|undefined;
   player.motion=undefined;
   if(flinch)progress=hurtProgress;
   if(action&&state!=='hit'&&state!=='death'){
    const[,clip]=this.action(player.asset,variant),cast=game.state.combat.casts.find(c=>c.id===action.id);
    player.motion=samplePlayerAction(action,state,clip,cast,game.state.equipment.hands==='A10'?.72:.8);
    if(player.motion.rushRun){
     state='run';variant=this.playerAction(player,state,weapon,equipped);
     progress=cast?.rush?Math.min(.999,cast.rush.elapsed/cast.rush.duration/.72):0;
    }else if(player.motion.settle){
     state=speed>.08?gait:'idle';variant=this.movementAction(player,state,weapon,equipped);
    }else progress=player.motion.progress;
   }

   player.renderedWeaponId=equipped;
   const cadence=state==='walk'?Math.max(.4,moveAmount*1.5):state==='run'?Math.max(.55,Math.min(1.3,speed/3.6)):1;
   this.show(player,state,dt*cadence,progress,!!action&&player.actionId!==action.id,variant);player.actionId=action?.id;
  }
  for(const enemy of game.state.enemies){
   const actor=this.active.get(enemy.id);if(!actor){if(!this.arriving.has(enemy.id)&&!this.arrivalFailure.has(enemy.id)){this.arriving.add(enemy.id);void this.create(enemy.id,enemyConcept(enemy),enemy.x,enemy.z).catch(error=>{this.arrivalFailure.add(enemy.id);console.error('[Campaign] Reinforcement could not load',error);}).finally(()=>this.arriving.delete(enemy.id));}continue;}
   const previous=actor.root.position,dx=enemy.x-previous.x,dz=enemy.z-previous.z;actor.speed=dx||dz?Math.hypot(dx,dz)/Math.max(.001,dt):0;actor.angle=enemy.angle;
   if(dx||dz)position(actor.root,enemy.x,this.world.height(enemy),enemy.z);
   const attacking=['windup','active','recovery'].includes(enemy.phase),genericPose=enemyProfile(enemy)?.attacks[enemy.combat?.moveId??'']?.pose;
   const stepPose=genericPose&&`${genericPose}_step${enemy.combat?.stepIndex??0}`,pose=stepPose&&actor.asset.manifest.actions[stepPose]?stepPose:genericPose;
   // Keep the completed move's pose during recovery after core clears moveId.
   if(pose)actor.enemyPose=pose;else if(!attacking)actor.enemyPose=undefined;
   // The shared stone base glides as a formation; it has no walking frames.
   const gliding=actor.modelId==='elite-06';
   const reaction=game.enemyHitReaction(enemy.id),state=enemy.hp<=0?'death':enemy.phase==='stagger'||reaction?.flinch&&!attacking?'hit':attacking?(pose??actor.enemyPose??(enemy.kind==='archer'?'attack_bow':'attack_sword')):enemy.phase==='approach'&&actor.speed>.08&&!gliding?'walk':'idle';
   if(actor.phase!==enemy.phase){actor.phase=enemy.phase;actor.phaseDuration=Math.max(.001,enemy.phaseTime);}
   const variant=enemy.kind==='archer'&&(state==='idle'||state==='walk')&&actor.asset.manifest.actions[state+'_bow']?state+'_bow':state;
   const[sampled,clip]=this.action(actor.asset,variant),count=clip.frameIndices?.length??clip.frames??1;
   const activeStart=clip.phaseStarts?.[Math.max(0,count-2)]??(sampled==='attack_bow'?.75:.28),recoveryStart=clip.phaseStarts?.[count-1]??(sampled==='attack_bow'?.875:.6);
   const fraction=clamp(1-enemy.phaseTime/(actor.phaseDuration??1));
   // Phase timing belongs to the resolved source pose: a reused bow action
   // still draws until its .75 release, even when the move requested interact.
   const progress=attacking?(enemy.phase==='windup'?fraction*Math.max(0,activeStart-.000001):enemy.phase==='active'?activeStart+fraction*Math.max(0,recoveryStart-activeStart-.000001):recoveryStart+fraction*(1-recoveryStart)):undefined;
   const nominal=state==='walk'?actor.asset.manifest.actions[variant]?.nominalSpeedMetresPerSecond:undefined;
   const dead=enemy.hp<=0,deathAge=dead?Math.max(0,game.state.time-(enemy.diedAt??game.state.time)):0,authoredDeath=!!actor.asset.manifest.actions.death;
   const fall=dead?(this.reducedMotion?1:clamp(deathAge/.4)):0;
   const impact=this.impacts.get(enemy.id),age=impact?game.state.time-impact.start:Infinity,hold=!this.reducedMotion&&!attacking&&age<(impact?.style.hold??0);
   if(dead){
    // Hold the authored final death frame; concepts without one use their own
    // idle image collapsed at the death anchor, including after reload.
    const deathClip=actor.asset.manifest.actions.death,frames=deathClip?.frameIndices?.length??deathClip?.frames??1;
    this.show(actor,authoredDeath?'death':'idle',0,authoredDeath?clamp(deathAge*(deathClip?.fps??8)/frames):0);
   }else if(!hold)this.show(actor,state,nominal?dt*Math.max(.1,Math.min(2,actor.speed/nominal)):dt,progress,false,variant);
   const pulse=impact&&age<.22?Math.sin(Math.min(1,age/.22)*Math.PI):0,side=Math.sign(Math.sin(impact?.angle??reaction?.angle??0)*this.camera.node.right.x+Math.cos(impact?.angle??reaction?.angle??0)*this.camera.node.right.z)||1;
   const heavyContact=impact&&['heavy','critical','kill'].includes(impact.style.kind);
   const strength=(this.reducedMotion?0:reaction?.resisted?(heavyContact?.65:.4):1)*(impact?.style.recoil??0)/.2;
   const lowBody=MONSTER_CONCEPTS.has(actor.modelId)||['mine-crawler','u1-2'].includes(actor.modelId);
   scale(actor.model,dead&&!authoredDeath?(lowBody?.9:.72):1+pulse*.09*strength,dead&&!authoredDeath?1-fall*(lowBody?.65:.32):1-pulse*.12*strength,1);
   const roll=dead?(authoredDeath?0:-(lowBody?12:78)*fall):-side*pulse*(impact?.style.kind==='armor'?3:10)*strength;
   if(Math.abs(actor.sprite.eulerAngles.z-roll)>.000001)actor.sprite.setRotationFromEuler(0,0,roll);
   const alpha=Math.round(255*game.corpseOpacity(enemy));
   const flash=!this.reducedMotion&&impact?.style.kind!=='burn'&&age>=0&&age<(heavyContact?.08:.055),tint=F.color(impact?.style.role??'damage.physical');
   setActorTint(actor,flash?tint.r/255*1.9:1,flash?tint.g/255*1.9:1,flash?tint.b/255*1.9:1,alpha/255);
   if(age>.3)this.impacts.delete(enemy.id);
   actor.root.active=alpha>0;
   if((this.hurtUntil.get(enemy.id)??Infinity)<=game.state.time){this.hurtUntil.delete(enemy.id);this.electricHurt.delete(enemy.id);}
   if((this.defeatedUntil.get(enemy.id)??Infinity)<=game.state.time)this.defeatedUntil.delete(enemy.id);
  }
  for(const actor of this.active.values())if(actor.id!=='player'&&!actor.id.startsWith('campaign-')&&!this.frameEnemies.has(actor.id)){
   if(actor.id.startsWith('field-npc-')){
    const objects=this.world.area.objects.filter(o=>o.npcId===actor.id||o.actor===actor.id),target=objects.find(o=>game.interactionVisible(o));
    actor.root.active=fieldNpcVisible(actor.id,game.state.flags);
    const at=target??objects[0];if(at)actor.root.setPosition(at.x,this.world.height(at),at.z);
   }
   this.show(actor,'idle',dt);
  }
  if(game.state.area==='H03')for(let i=0;i<3;i++){const actor=this.active.get('campaign-worker-'+i);if(!actor)continue;const key=i<2?`campaign:wave-time:workshop-defense:${i}`:'campaign:battle-time:workshop-defense',start=game.state.receipts[key],progress=typeof start==='number'?Math.min(1,Math.max(0,(game.state.time-start)/7)):game.state.flags['campaign:battle:workshop-defense:complete']?1:0;const x=(i-1)*(5+progress*3),z=-16-progress*11;actor.root.setPosition(x,this.world.height({x,z}),z);actor.angle=Math.PI;this.show(actor,progress>0&&progress<1?'walk':'idle',dt);}
  // Every point on a camera-facing image has the holder's ground depth plus
  // the same small bias. Keep the shared transparent priority at zero so the
  // native back-to-front queue also sorts correctly against other flat props
  // and effects, rather than forcing all characters above those renderers.
 }
 /** Existing CharacterPreview assumes a skinned 3D model. Use playerPortrait. */
 playerModel():Node|null{return null;}
 presentCampaign(beat:CampaignBeat|undefined,time:number,game:GameSession){
  for(let i=0;i<3;i++){const a=this.active.get('campaign-sentry-'+i);if(!a)continue;a.root.active=!!beat?.turnArmy;if(!a.root.active)continue;const p=game.state.player,u=this.camera.node.up,r=this.camera.node.right,n=Math.max(.01,Math.hypot(u.x,u.z)),x=p.x+u.x/n*4+(i-1)*r.x*2.3,z=p.z+u.z/n*4+(i-1)*r.z*2.3;a.root.setPosition(x,this.world.height({x,z}),z);a.angle=Math.PI*.5*Math.min(1,time/1.4);this.show(a,time<1.4?'walk':'attack_sword',.02,time<1.4?undefined:.35);}
 }
 /** Stable visible head height from this character's own idle alpha bounds.
  * Raised weapons and transparent atlas margins must not lift a health bar. */
 enemyHeadPoint(id:string):Vec3|undefined {
  const actor=this.active.get(id);if(!actor||!actor.root.activeInHierarchy)return;
  const idle=actor.asset.manifest.actions.idle_bow?'idle_bow':'idle';
  const[,action]=this.action(actor.asset,idle),sample=this.frame(actor.asset,action,actor.direction,0,false);
  const bounds=(action.alphaBounds??actor.asset.manifest.alphaBounds)?.[sample.index];
  const upp=(action.worldUnitsPerPixel??actor.asset.manifest.camera?.worldUnitsPerPixel??.008)*sample.scaleFactor;
  const top=Math.max(.30,(sample.origin[1]-(bounds?.[1]??sample.frame.rect.height*.1))*upp);
  return actor.root.worldPosition.clone().add(Vec3.multiplyScalar(new Vec3(),this.camera.node.up,top+.10)).add(Vec3.multiplyScalar(new Vec3(),this.camera.node.forward,-.07));
 }
 /** A calibrated camera-plane hand/staff point on the currently sampled pose.
  * Effects consume it after update(); it never changes projectile collision. */
 playerPresentation():PlayerPresentation|undefined {
  const actor=this.active.get('player');if(!actor)return;
  const offset=playerHandOffset(actor.sampledAction,actor.ordinal,actor.asset.manifest.directions[actor.direction]??'down');
  const hand=new Vec3(actor.root.position.x,actor.root.position.y,actor.root.position.z);
  hand.add(Vec3.multiplyScalar(new Vec3(),this.camera.node.right,offset.x));hand.add(Vec3.multiplyScalar(new Vec3(),this.camera.node.up,offset.y));
  hand.add(Vec3.multiplyScalar(new Vec3(),this.camera.node.forward,-.065));
  return {actionId:actor.actionId,phase:actor.motion?.phase,beat:actor.motion?.beat??0,facing:actor.angle,hand,pose:actor.sampledAction,ordinal:actor.ordinal};
 }
 /** Share the equipped atlas with the original inventory's directional views. */
 playerPortraitViews(weapon:string):SpriteFrame[]{
  const actor=this.active.get('player');if(!actor)return[];
  weapon=EQUIPMENT[weapon]?.artSource??weapon;
  const family=weaponFamily(weapon),requested=actor.asset.manifest.actions['idle_'+weapon]?'idle_'+weapon:family==='sword'?'idle':'idle_'+family;
  const[name,action]=this.action(actor.asset,requested),m=actor.asset.manifest;
  return ['down','right','up','left'].map(direction=>{
   const row=Math.max(0,m.directions.findIndex(d=>normalDirection(d)===direction)),sample=this.frame(actor.asset,action,row,0,false),bounds=(action.alphaBounds??m.alphaBounds)?.[sample.index];
   if(!bounds)return sample.frame;
   const key='portrait:'+name+':'+sample.index;let frame=actor.asset.frames.get(key);
   if(!frame){const r=sample.frame.rect,rect=new Rect(r.x+bounds[0],r.y+bounds[1],bounds[2]-bounds[0],bounds[3]-bounds[1]);frame=new SpriteFrame();frame.reset({texture:sample.texture,rect,originalSize:new Size(rect.width,rect.height)});frame.packable=false;actor.asset.frames.set(key,frame);}
   return frame;
  });
 }
 playerPortrait():FlatPortrait|null{
  const actor=this.active.get('player');if(!actor)return null;
  const[name,action]=this.action(actor.asset,'idle'),direction=Math.max(0,actor.asset.manifest.directions.findIndex(d=>normalDirection(d)==='down'));
  const sample=this.frame(actor.asset,action,direction,0,false);
  return{frame:sample.frame,texture:sample.texture,rect:sample.frame.rect.clone(),origin:sample.origin,worldUnitsPerPixel:(action.worldUnitsPerPixel??actor.asset.manifest.camera?.worldUnitsPerPixel??.008)*sample.scaleFactor,conceptAsset:actor.asset.id,bounds:(action.alphaBounds??actor.asset.manifest.alphaBounds)?.[sample.index]};
 }
 inspect(){return Array.from(this.active.values()).map(actor=>({id:actor.id,profile:'flat-concept-v1',renderer:'native-unlit-quad',materialPasses:actor.material.passes.length,modelId:actor.modelId,conceptAsset:actor.asset.id,reusedConcept:actor.id.startsWith('field-npc-'),source:actor.id.startsWith('field-npc-')?'generic-npc-atlas':'design-image-atlas',sharedBody:actor.asset.manifest.actions[actor.sampledAction]?.sharedBody,weaponLayerVisible:!!actor.equipment?.root.activeInHierarchy,gripOcclusionVisible:!!actor.equipment?.handSprite.activeInHierarchy,quiverVisible:!!actor.equipment?.backRoot.activeInHierarchy,clips:Object.keys(actor.asset.manifest.actions),state:actor.state,actionPhase:actor.motion?.phase,actionBeat:actor.motion?.beat,actionBeats:actor.motion?.beats,releaseAt:actor.motion?.releaseAt,requestedAction:actor.requestedAction,sampledAction:actor.sampledAction,weaponCarry:actor.id==='player'?(actor.sampledAction.startsWith('explore_')?'stowed':'ready'):undefined,combatReady:actor.id==='player'?this.combatReady:undefined,primaryPoseReused:actor.requestedAction!==actor.sampledAction&&ENEMY_PRIMARY_POSE_ADAPTERS[actor.asset.id]?.[actor.requestedAction]===actor.sampledAction,staticFallback:actor.requestedAction!==actor.sampledAction&&actor.sampledAction.startsWith('idle'),frame:actor.frame,ordinal:actor.ordinal,progress:actor.progress,direction:actor.asset.manifest.directions[actor.direction],speed:actor.speed,visible:actor.root.active,position:{x:actor.root.position.x,y:actor.root.position.y,z:actor.root.position.z},skeletons:[],loaded3DModel:false}));}
 inspectTextureOwnership(){const textures=Array.from(this.enemyTextures).map(texture=>({uuid:texture.uuid,width:texture.width,height:texture.height,refCount:texture.refCount,rgbaBytes:texture.width*texture.height*4}));return{disposed:this.disposed,enemyTextureCount:textures.length,estimatedEnemyRgbaBytes:textures.reduce((sum,texture)=>sum+texture.rgbaBytes,0),textures,heroAndNpcRefsOwned:false};}
 destroy(){
  if(this.disposed)return;this.disposed=true;
  this.impacts.clear();this.hurtUntil.clear();this.electricHurt.clear();this.defeatedUntil.clear();this.frameEnemies.clear();
  for(const actor of this.active.values()){if(actor.root.isValid)actor.root.destroy();actor.edgeMaterial?.destroy();actor.equipment?.material.destroy();actor.material.destroy();}this.active.clear();
  for(const asset of this.assets.values()){for(const frame of asset.frames.values())frame.destroy();for(const mesh of asset.meshes.values())mesh.destroy();}this.assets.clear();this.pending.clear();
  this.quad.destroy();
  // decRef schedules the engine's reference-aware release check; force release
  // would invalidate a texture already held by the next scene instance.
  for(const texture of this.enemyTextures)texture.decRef();this.enemyTextures.clear();
 }
}
