import {Asset,AnimationClip,Camera,Color,EventTouch,instantiate,Material,MeshRenderer,Node,PointLight,RenderTexture,SkeletalAnimation,SkinnedMeshRenderer,Sprite,SpriteFrame,UITransform,Vec3,Texture2D} from 'cc';
import {selectEquipmentWeaponVariants,weaponAttachmentKind} from './WeaponMaterials';

/** Cocos native RenderTexture: a real copy of the equipped actor, isolated from the world camera. */
export class CharacterPreview {
 private materials=new Map<Material,Material>();
 private retained=new Set<Asset>();
 private stage:Node;private camera:Camera;private texture:RenderTexture;private frame:SpriteFrame;private model:Node;private yaw=-12;
 constructor(host:Node,source:Node,w:number,h:number,equipment?:{weapon:string;head?:string|null}){
  const scene=source.scene;this.stage=new Node('CharacterPreviewStage');scene.addChild(this.stage);this.stage.setPosition(10000,0,10000);
  this.model=instantiate(source);this.stage.addChild(this.model);this.model.setPosition(0,0,0);this.model.setRotationFromEuler(0,this.yaw,0);
  const layer=1<<19,setLayer=(node:Node)=>{node.layer=layer;for(const child of node.children)setLayer(child);};setLayer(this.model);
  const kind=equipment?weaponAttachmentKind(equipment.weapon):null;
   const dress=(node:Node)=>{if(kind&&node.name.startsWith('Held_'))node.active=node.name==='Held_'+kind;if(node.name.includes('_native_hood_'))node.active=equipment?.head==='A02';if(node.name.includes('_native_hair_'))node.active=node.active&&equipment?.head!=='A02';if(node.parent?.name==='attach_arrow_r Socket')node.active=false;for(const child of node.children)dress(child);};dress(this.model);if(equipment)selectEquipmentWeaponVariants(this.model,equipment.weapon);
  for(const renderer of this.model.getComponentsInChildren(MeshRenderer)){renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   if(renderer.mesh)this.retain(renderer.mesh);if(renderer instanceof SkinnedMeshRenderer&&renderer.skeleton)this.retain(renderer.skeleton);
   for(const material of renderer.sharedMaterials)if(material){this.retain(material);for(const key of ['mainTexture','normalMap','pbrMap','emissiveMap']){const texture=material.getProperty(key);if(texture instanceof Texture2D)this.retain(texture);}}
   renderer.sharedMaterials.forEach((source,index)=>{if(!source||source.effectName==='builtin-standard')return;let material=this.materials.get(source);if(!material){const texture=source.getProperty('mainTexture') as Texture2D|null;material=new Material();material.name=source.name+'-PreviewOpaque';material.initialize({effectName:'builtin-standard',defines:{USE_ALBEDO_MAP:!!texture}});material.setProperty('mainColor',Color.WHITE);material.setProperty('roughness',.65);material.setProperty('metallic',.15);if(texture)material.setProperty('mainTexture',texture);this.materials.set(source,material);}renderer.setSharedMaterial(material,index);});
   const morph=renderer.mesh?.struct.morph,index=morph?.targetNames?.indexOf('Draw')??-1;if(morph&&index>=0)for(let sub=0;sub<morph.subMeshMorphs.length;sub++)if(morph.subMeshMorphs[sub])renderer.setWeight(0,sub,index);}
  for(const animation of this.model.getComponentsInChildren(SkeletalAnimation)){
   const staffHeld=(node:Node):boolean=>node.name==='Held_staff'?!!node.getChildByName('UnsheathedSwordModels')?.active:node.children.some(staffHeld),preferred=kind==='staff'&&staffHeld(this.model)?'idle_staff':'idle',idle=animation.clips.find(clip=>clip&&clip.name.split('|').pop()?.replace(/\.\d+$/,'')===preferred)??animation.clips.find(clip=>clip&&clip.name.split('|').pop()?.replace(/\.\d+$/,'')==='idle');
   if(idle){animation.useBakedAnimation=true;animation.play(idle.name);const state=animation.getState(idle.name);if(state)state.wrapMode=AnimationClip.WrapMode.Loop;}
  }
  const cameraNode=new Node('CharacterPreviewCamera');scene.addChild(cameraNode);this.camera=cameraNode.addComponent(Camera);this.camera.projection=Camera.ProjectionType.ORTHO;this.camera.orthoHeight=1.18;this.camera.near=.1;this.camera.far=20;this.camera.visibility=layer;this.camera.priority=-10;this.camera.clearColor=new Color(0,0,0,0);this.camera.clearFlags=Camera.ClearFlag.SOLID_COLOR;
  cameraNode.setPosition(10001.5,1.12,10005);cameraNode.lookAt(new Vec3(10000,1.03,10000));
  // Neutral key preserves the actor's texture colors; a restrained sky fill separates the silhouette.
  for(const [name,x,y,z,flux,color]of [['PortraitKey',-2,3,3,45000,new Color(255,240,214)],['PortraitFill',2,2,2,18000,new Color(219,230,243)]] as const){const n=new Node(name);this.stage.addChild(n);n.setPosition(x,y,z);const light=n.addComponent(PointLight);light.color=color;light.visibility=layer;light.range=6;light.term=0;light.luminousFlux=flux;}
  this.texture=new RenderTexture();this.texture.reset({width:Math.max(192,Math.round(768*w/h)),height:768});this.camera.targetTexture=this.texture;
  this.frame=new SpriteFrame();this.frame.texture=this.texture;this.frame.packable=false;
  const node=new Node('CharacterModel');host.addChild(node);node.layer=host.layer;node.addComponent(UITransform).setContentSize(w,h);const sprite=node.addComponent(Sprite);sprite.sizeMode=Sprite.SizeMode.CUSTOM;sprite.spriteFrame=this.frame;
  node.on(Node.EventType.TOUCH_MOVE,(event:EventTouch)=>{event.propagationStopped=true;this.rotate(event.getDeltaX()*.45);});
 }
 rotate(degrees:number){this.yaw+=degrees;if(this.model.isValid)this.model.setRotationFromEuler(0,this.yaw,0);}
  focusHead(enabled=true){this.camera.orthoHeight=enabled?.22:1.18;this.camera.node.setPosition(enabled?10000.5:10001.5,enabled?1.72:1.12,enabled?10003:10005);this.camera.node.lookAt(new Vec3(10000,enabled?1.69:1.03,10000));}
 private retain(asset:Asset){if(!this.retained.has(asset)){asset.addRef();this.retained.add(asset);}}
 destroy(){if(this.camera.isValid){this.camera.targetTexture=null;this.camera.node.destroy();}this.stage.destroy();this.frame.destroy();this.texture.destroy();this.materials.forEach(material=>material.destroy());this.materials.clear();for(const asset of this.retained){if(asset instanceof Material&&!asset.uuid){asset.decRef(false);if(asset.refCount===0)asset.destroy();}else asset.decRef();}this.retained.clear();}
}
