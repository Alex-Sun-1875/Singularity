import {gameResources as resources,usesAssetBundles} from '../../../shared/assets/GameResources';
import {NATIVE_TEXTURE_REUSE} from '../../../shared/assets/NativeTextureReuse';
import {Color,Material,MeshRenderer,Node,Texture2D,gfx} from 'cc';

type NativeMaps = {albedo?:string; normal?:string; orm?:string; roughness?:string};
export interface NativeMaterialRecord {
 runtimeName:string;
 parts?:string[];
 maps:NativeMaps;
 sourcePBR?:{
  roughness?:number; metallic?:number;
  linked?:{roughness?:boolean; metallic?:boolean};
  effectiveFactors?:{roughness?:number; metallic?:number};
 };
 ormChannels?:{occlusion?:string; roughness?:string; metallic?:string};
 alphaClip?:boolean;doubleSided?:boolean;alphaThreshold?:number;
}
export interface NativeActorMaterialManifest {runtimeProfile?:string; materials?:NativeMaterialRecord[]}
export interface NativeMaterialReport {adapted:number; preserved:number; unmatched:string[]}
type LoadedMaps = {albedo?:Texture2D; normal?:Texture2D; orm?:Texture2D; roughness?:Texture2D};
type PBRFactors = {roughness:number; metallic:number; occlusion:number};
const importedTexturePaths=new Set(Object.values(NATIVE_TEXTURE_REUSE).flatMap(match=>match.paths));

/** Restores the author's native UV maps that FBX's specular importer omits.
 * One owner per Actors instance: await apply after prefab instantiation, then
 * destroy after its actor nodes. Only generated materials and this owner's
 * texture references are released; imported materials remain asset-owned.
 */
export class NativeActorMaterials {
 /** Warm only maps this adapter will load; verified imported aliases remain
  * prefab-owned in releases and must not be uploaded a second time. */
 static async preload(manifest:NativeActorMaterialManifest){
  const paths=new Set((manifest.materials??[]).filter(record=>!record.parts?.includes('hair')).flatMap(record=>Object.values(record.maps).filter((path):path is string=>!!path).map(path=>'actors/'+path.replace(/\\/g,'/').replace(/^\.\.\//,'').replace(/\.[^/.]+$/,'')+'/texture')));
  await Promise.all(Array.from(paths).filter(path=>!usesAssetBundles||!importedTexturePaths.has(path)).map(path=>new Promise<Texture2D>((resolve,reject)=>resources.load(path,Texture2D,(error,texture)=>error?reject(error):resolve(texture)))));
 }
 private materials = new Map<string,Promise<Material>>();
 private textures = new Map<string,Promise<Texture2D>>();
 private ownedMaterials = new Set<Material>();
 private ownedTextures = new Set<Texture2D>();
 private disposed = false;

 async apply(model:Node,manifest:NativeActorMaterialManifest,albedoByPart?:Readonly<Record<string,string>>,options:{excludeHair?:boolean;current?:()=>boolean}={}):Promise<NativeMaterialReport> {
  const report:NativeMaterialReport = {adapted:0,preserved:0,unmatched:[]};
  if(manifest.runtimeProfile !== 'native-kit-v1')return report;
  const records = new Map((manifest.materials??[]).map(record=>[record.runtimeName,record]));
  await Promise.all(model.getComponentsInChildren(MeshRenderer).map(async renderer=>{
   if(options.excludeHair&&renderer.node.name.includes('_native_hair_'))return;
   await Promise.all(renderer.sharedMaterials.map(async (source,index)=>{
    if(!source)return;
    let record = records.get(source.name.replace(/-NativePBR$/,''));
    if(!record){report.unmatched.push(source.name);return;}
    const part=renderer.node.name.match(/_native_([^_]+)_/)?.[1],override=part&&albedoByPart?.[part];
    if(override&&(part==='hair'||record.runtimeName.includes('Ranger')))record={...record,maps:{...record.maps,albedo:override}};
    const material = await this.adapt(source,record);
    if(this.disposed||!model.isValid||!renderer.isValid||options.current&&!options.current())return;
    if(material===source)report.preserved++;
    else {renderer.setSharedMaterial(material,index);report.adapted++;}
   }));
  }));
  report.unmatched = Array.from(new Set(report.unmatched));
  return report;
 }

 private adapt(source:Material,record:NativeMaterialRecord):Promise<Material> {
  const {runtimeName,parts,...properties}=record;
  const key = JSON.stringify(properties);
  const cached = this.materials.get(key);
  if(cached)return cached;
  const pending = this.create(source,record);
  this.materials.set(key,pending);
  pending.catch(()=>this.materials.delete(key));
  return pending;
 }

 private async create(source:Material,record:NativeMaterialRecord):Promise<Material> {
  const [albedo,normal,orm,roughness] = await Promise.all(
   [record.maps.albedo,record.maps.normal,record.maps.orm,record.maps.roughness].map((path,index)=>path?this.texture(path,source.getProperty(['mainTexture','normalMap','pbrMap','pbrMap'][index]) as Texture2D|undefined):Promise.resolve(undefined)));
  if(this.disposed)throw new Error('Native actor materials were destroyed during loading');
  const maps:LoadedMaps = {albedo,normal,orm,roughness};
  const pbr = record.sourcePBR;
  // Effective factors are the author's glTF multipliers, including zero metal on skin.
  // Palette adjustments are already baked into albedo; use a white multiplier.
  const factors:PBRFactors = {
   roughness:pbr?.effectiveFactors?.roughness??(orm||roughness?1:pbr?.roughness??.5),
   metallic:pbr?.effectiveFactors?.metallic??(orm?1:pbr?.metallic??0),
   occlusion:orm?1:0,
  };
  if(this.matches(source,maps,factors,record))return source;
  const material = new Material();
  material.name = record.runtimeName+'-NativePBR';
  material.initialize({effectName:'builtin-standard',defines:{
   USE_ALBEDO_MAP:!!albedo,USE_NORMAL_MAP:!!normal,USE_PBR_MAP:!!(orm||roughness),
   USE_ALPHA_TEST:!!record.alphaClip,USE_TWOSIDE:!!record.doubleSided,
   OCCLUSION_CHANNEL:this.channel(record.ormChannels?.occlusion,'r'),
   ROUGHNESS_CHANNEL:this.channel(record.ormChannels?.roughness,'g'),
   METALLIC_CHANNEL:this.channel(record.ormChannels?.metallic,'b'),
  },states:record.doubleSided?{rasterizerState:{cullMode:gfx.CullMode.NONE}}:undefined});
  material.setProperty('mainColor',Color.WHITE);
  material.setProperty('roughness',factors.roughness);
  material.setProperty('metallic',factors.metallic);
  material.setProperty('occlusion',factors.occlusion);
  if(record.alphaClip)material.setProperty('alphaThreshold',record.alphaThreshold??.35);
  if(albedo)material.setProperty('mainTexture',albedo);
  if(normal){material.setProperty('normalMap',normal);material.setProperty('normalStrength',1);}
  if(orm||roughness)material.setProperty('pbrMap',orm??roughness!);
  material.addRef();this.ownedMaterials.add(material);
  return material;
 }

 private channel(value:string|undefined,fallback:string):string {
  const channel = value?.toLowerCase();
  return channel&&['r','g','b','a'].includes(channel)?channel:fallback;
 }

 private matches(source:Material,maps:LoadedMaps,factors:PBRFactors,record:NativeMaterialRecord):boolean {
  if(source.effectName!=='builtin-standard')return false;
  const defines = source.passes[0]?.defines;
  if(!defines||!!defines.USE_ALBEDO_MAP!==!!maps.albedo||!!defines.USE_NORMAL_MAP!==!!maps.normal||!!defines.USE_PBR_MAP!==!!(maps.orm||maps.roughness))return false;
  if(!!defines.USE_ALPHA_TEST!==!!record.alphaClip||!!defines.USE_TWOSIDE!==!!record.doubleSided)return false;
  const color = source.getProperty('mainColor') as Color|undefined;
  if(!color||color.r!==255||color.g!==255||color.b!==255||color.a!==255)return false;
  if(maps.albedo&&source.getProperty('mainTexture')!==maps.albedo)return false;
  if(maps.normal&&(source.getProperty('normalMap')!==maps.normal||source.getProperty('normalStrength')!==1))return false;
  if((maps.orm||maps.roughness)&&source.getProperty('pbrMap')!==(maps.orm??maps.roughness))return false;
  if(maps.orm||maps.roughness){
   const roughnessChannel = this.channel(record.ormChannels?.roughness,'g');
   if((defines.ROUGHNESS_CHANNEL??'g')!==roughnessChannel)return false;
   if((defines.OCCLUSION_CHANNEL??'r')!==this.channel(record.ormChannels?.occlusion,'r'))return false;
   if((defines.METALLIC_CHANNEL??'b')!==this.channel(record.ormChannels?.metallic,'b'))return false;
  }
  return source.getProperty('roughness')===factors.roughness&&source.getProperty('metallic')===factors.metallic&&source.getProperty('occlusion')===factors.occlusion;
 }

 private texture(relativePath:string,imported?:Texture2D):Promise<Texture2D> {
  // Manifest paths are relative to actors/{id}/; native-shared lives in resources.
  const path = 'actors/'+relativePath.replace(/\\/g,'/').replace(/^\.\.\//,'').replace(/\.[^/.]+$/,'')+'/texture';
  const cached = this.textures.get(path);
  if(cached)return cached;
  // The prefab already uploaded these images. Reuse only build-time verified
  // pixel/sampler matches; a name match would hide intentional art overrides.
  const match=usesAssetBundles&&imported?.isValid&&NATIVE_TEXTURE_REUSE[imported.uuid];
  if(match&&match.paths.includes(path)){
   imported.setAnisotropy(match.anisotropy);
   if(!this.ownedTextures.has(imported)){imported.addRef();this.ownedTextures.add(imported);}
   const ready=Promise.resolve(imported);this.textures.set(path,ready);return ready;
  }
  const pending = new Promise<Texture2D>((resolve,reject)=>resources.load(path,Texture2D,(error,texture)=>{
   if(error){reject(new Error('Native actor texture '+path+': '+error.message));return;}
   if(this.disposed){texture.addRef();texture.decRef();reject(new Error('Native actor materials were destroyed during loading'));return;}
   if(!this.ownedTextures.has(texture)){texture.addRef();this.ownedTextures.add(texture);}resolve(texture);
  }));
  this.textures.set(path,pending);
  pending.catch(()=>this.textures.delete(path));
  return pending;
 }

 destroy():void {
  if(this.disposed)return;
  this.disposed = true;
  // Generated materials have no loader UUID. Release them directly at zero;
  // the loader's deferred UUID queue is for imported assets, not runtime mats.
  for(const material of this.ownedMaterials){material.decRef(false);if(material.refCount===0)material.destroy();}
  for(const texture of this.ownedTextures)texture.decRef();
  this.ownedMaterials.clear();this.ownedTextures.clear();
  this.materials.clear();this.textures.clear();
 }
}
