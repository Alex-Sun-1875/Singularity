import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Node,Mesh,MeshRenderer,Material,Texture2D,JsonAsset,BufferAsset,Vec3,Vec4,Color,assetManager,utils,gfx} from 'cc';
import {withTangents} from '../../actors/runtime/MeshTangents';

type Range=[number,number];
type PartData={material:string;positions:Range;normals:Range;uvs:Range;indices:Range};
type ModelData={dimensions:number[];parts:PartData[]};
type MaterialData={color:string;normal?:string;cutout:boolean;doubleSided:boolean;roughness:number;metallic:number;tint:number[]};
type Library={version:number;geometry:string;models:Record<string,ModelData>;materials:Record<string,MaterialData>};
type Model={dimensions:Vec3;parts:{mesh:Mesh;material:Material}[]};
export type PropSize={width?:number;height?:number;depth?:number;scale?:number;yaw?:number};

/** CC0 source meshes, shared for the chapter lifetime. Scene nodes never own these assets. */
export class EnvironmentAssets {
 private static models=new Map<string,Model>();
 private static materials=new Map<string,Material>();
 private static meshes=new Set<Mesh>();
 private static textures=new Set<Texture2D>();
 private static pending:Promise<void>|null=null;
 private static layoutPending:Promise<void>|null=null;
 private static dimensions=new Map<string,Vec3>();
 private static json:JsonAsset|null=null;
 /** Painted props need their authored scale and anchor, without hidden meshes or PBR maps. */
 static loadLayout():Promise<void>{
  if(!this.layoutPending)this.layoutPending=new Promise<void>((resolve,reject)=>resources.load('environment/library',JsonAsset,(error,asset)=>{
   if(error){reject(error);return;}
   try{
    const data=asset.json as Library;
    for(const [key,model] of Object.entries(data.models))this.dimensions.set(key,new Vec3(...model.dimensions as [number,number,number]));
    resolve();
   }catch(error){reject(error);}
   finally{resources.release('environment/library',JsonAsset);}
  })).catch(error=>{this.layoutPending=null;throw error;});
  return this.layoutPending;
 }
 static load():Promise<void>{
  if(this.pending)return this.pending;
  const get=<T>(path:string,type:any)=>new Promise<T>((resolve,reject)=>resources.load(path,type,(error,asset)=>error?reject(new Error('Environment asset '+path+': '+error.message)):resolve(asset as unknown as T)));
  this.pending=(async()=>{
   this.json=await get<JsonAsset>('environment/library',JsonAsset);const data=this.json.json as Library;
   const geometry=await get<BufferAsset>('environment/'+data.geometry,BufferAsset),buffer=geometry.buffer();
   const floats=(range:Range)=>Array.from(new Float32Array(buffer,range[0],range[1]));
   const indices=(range:Range)=>Array.from(new Uint32Array(buffer,range[0],range[1]));
   await Promise.all(Object.entries(data.materials).map(async([id,definition])=>{
    const [color,normal]=await Promise.all([get<Texture2D>('environment/'+definition.color+'/texture',Texture2D),definition.normal?get<Texture2D>('environment/'+definition.normal+'/texture',Texture2D):Promise.resolve(null)]);
    for(const texture of [color,normal])if(texture){texture.setWrapMode(Texture2D.WrapMode.REPEAT,Texture2D.WrapMode.REPEAT);this.textures.add(texture);}
    const material=new Material();material.name='CC0:'+id;
    // Culling alone exposes unlit backs. The standard effect also needs its
    // native two-sided normal adaptation for leaf/grass cards and open meshes.
    material.initialize({effectName:'builtin-standard',defines:{USE_ALBEDO_MAP:true,USE_NORMAL_MAP:!!normal,USE_ALPHA_TEST:definition.cutout,USE_TWOSIDE:definition.doubleSided,USE_INSTANCING:true},states:definition.doubleSided?{rasterizerState:{cullMode:gfx.CullMode.NONE}}:undefined});
    material.setProperty('mainTexture',color);material.setProperty('mainColor',new Color(255,255,255,255));
    material.setProperty('roughness',definition.roughness);material.setProperty('metallic',definition.metallic);material.setProperty('specularIntensity',.26);
    material.setProperty('tilingOffset',new Vec4(1,1,0,0));
    if(id==='lantern-1')material.setProperty('emissive',new Color(238,166,73));
    if(normal){material.setProperty('normalMap',normal);material.setProperty('normalStrength',.6);}
    if(definition.cutout)material.setProperty('alphaThreshold',.38);
    this.materials.set(id,material);
   }));
   for(const [key,model] of Object.entries(data.models)){
    const parts=model.parts.map(part=>{const mesh=utils.createMesh(withTangents({positions:floats(part.positions),normals:floats(part.normals),uvs:floats(part.uvs),indices:indices(part.indices)}));this.meshes.add(mesh);return {mesh,material:this.materials.get(part.material)!};});
    this.models.set(key,{dimensions:new Vec3(...model.dimensions as [number,number,number]),parts});
   }
   // Mesh buffers are now owned by the library; release the large source JSON arrays.
   resources.release('environment/library',JsonAsset);resources.release('environment/'+data.geometry,BufferAsset);this.json=null;
  })().catch(error=>{this.dispose();throw error;});return this.pending;
 }
 static place(key:string,parent:Node,position:Vec3,size:PropSize={},layoutOnly=false):Node {
  const model=this.models.get(key),dimensions=layoutOnly?this.dimensions.get(key):model?.dimensions;
  if(!dimensions)throw new Error('Environment library must preload before '+key);
  const root=new Node('CC0:'+key);parent.addChild(root);root.setPosition(position);
  const scale=size.scale??1,d=dimensions,uniform=size.height!==undefined?size.height/d.y:size.width!==undefined?size.width/d.x:size.depth!==undefined?size.depth/d.z:1;
  root.setScale((size.width!==undefined?size.width/d.x:uniform)*scale,(size.height!==undefined?size.height/d.y:uniform)*scale,(size.depth!==undefined?size.depth/d.z:uniform)*scale);
  if(size.yaw)root.setRotationFromEuler(0,size.yaw,0);
  if(!layoutOnly)for(const part of model!.parts){const node=new Node('Surface');root.addChild(node);const renderer=node.addComponent(MeshRenderer);renderer.mesh=part.mesh;renderer.setSharedMaterial(part.material,0);renderer.shadowCastingMode=/^(grass|fern|jug|bowl|candlestick|books)/.test(key)?0:1;renderer.receiveShadow=1;}
  return root;
 }
 /** Call only after every SceneBuilder node has been destroyed, when leaving the chapter. */
 static dispose(){
  for(const mesh of this.meshes)mesh.destroy();for(const material of this.materials.values())material.destroy();
  this.models.clear();this.meshes.clear();this.materials.clear();
  // Resource-managed textures have one shared cache owner and no per-area clones.
  for(const texture of this.textures)assetManager.releaseAsset(texture);this.textures.clear();
  if(this.json)resources.release('environment/library',JsonAsset);this.json=null;this.pending=null;
  this.dimensions.clear();this.layoutPending=null;
 }
}
