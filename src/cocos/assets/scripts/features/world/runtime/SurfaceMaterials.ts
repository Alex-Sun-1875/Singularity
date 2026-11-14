import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Color,Material,Texture2D,Vec3,Vec4,gfx} from 'cc';
import type {AreaDef} from '../../../core/Contracts';

export type Surface='wood'|'cobble'|'grass'|'earth'|'rock'|'plaster'|'leather'|'fabric'|'roof'|'metal';
const SURFACES:Surface[]=['wood','cobble','grass','earth','rock','plaster','leather','fabric','roof','metal'];
type Maps={color:Texture2D;normal:Texture2D;pbr?:Texture2D};
const ROUGHNESS:Record<Surface,number>={wood:.78,cobble:.89,grass:.96,earth:.98,rock:.92,plaster:.94,leather:.64,fabric:.96,roof:.86,metal:.43};
const MATCHED=new Set<Surface>(['wood','cobble','rock','fabric','earth','grass']);
// Fabric and grass are design scales: their providers publish no measured size.
const TILE_METRES:Record<Surface,number>={wood:1.5,cobble:2,rock:1.8,fabric:.25,earth:2.11,grass:2,plaster:2,leather:1,roof:2,metal:1};

/** Shared, compact image assets; callers own the materials, never these textures. */
export class SurfaceMaterials {
 private static maps=new Map<Surface,Maps>();
 private static pending:Promise<void>|null=null;

 static load():Promise<void>{
  if(this.pending)return this.pending;
  const load=(path:string)=>new Promise<Texture2D>((resolve,reject)=>resources.load(path+'/texture',Texture2D,(error,texture)=>{
   if(error){reject(new Error('Surface texture '+path+': '+error.message));return;}
   texture.setWrapMode(Texture2D.WrapMode.REPEAT,Texture2D.WrapMode.REPEAT);
   texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);
   if(path.includes('/pbr-v3/')){texture.setMipFilter(Texture2D.Filter.LINEAR);texture.setAnisotropy(4);}
   resolve(texture);
  }));
  this.pending=Promise.all(SURFACES.map(async name=>{
   const prefix='surfaces/'+(MATCHED.has(name)?'pbr-v3/':'')+name;
   const [color,normal,pbr]=await Promise.all([load(prefix+'-color'),load(prefix+'-normal'),MATCHED.has(name)?load(prefix+'-pbr'):Promise.resolve(undefined)]);
   this.maps.set(name,{color,normal,pbr});
  })).then(()=>undefined).catch(error=>{this.pending=null;throw error;});
  return this.pending;
 }

 /** Metres per source tile, for world-size UVs; see pbr-v3/provenance.json. */
 static tileMetres(surface:Surface):number{return TILE_METRES[surface];}

 static ground(area:AreaDef):Surface {
  if(area.kind==='interior')return area.id==='S01-T6'?'cobble':'wood';
  if(area.kind==='underground'||area.palette==='cave'||area.palette==='stone')return 'rock';
  // Reuse the matched grass maps for forest verges. Earth remains the path and
  // wetland surface, so woodland no longer reads as one uninterrupted dirt sheet.
  if(area.kind==='town')return 'grass';
  return area.palette==='marsh'?'earth':'grass';
 }

 static scenery(name:string,area:AreaDef):Surface|undefined {
  if(name==='Ground')return this.ground(area);
  if(name==='Road')return area.kind==='town'?'cobble':area.kind==='underground'?'rock':'earth';
  if(/metal|Anvil/i.test(name))return 'metal';
  if(name==='Roof')return 'roof';
  if(/Plaster/.test(name))return 'plaster';
  if(/WovenRug|Canvas|TableRunner/.test(name))return 'fabric';
  if(/Stone|Rubble|Pillar|Cliff/.test(name))return /Foundation|WallFoot|Forge|Chimney|Gate|Bridge/.test(name)?'cobble':'rock';
  if(/Timber|Wood|Bark|Door|Frame|Cask|Coffer|Cart|Wheel|Shelf|Table|Bench|Sign|Waypost|RoofRidge|crate/i.test(name))return 'wood';
  return undefined;
 }

 static create(name:string,surface:Surface|undefined,tint:Color,tiling=1,texture?:Texture2D,alphaTest=false,states?:Parameters<Material['initialize']>[0]['states'],vertexColors=false):Material {
  const maps=surface?this.maps.get(surface):undefined;
  if(surface&&!maps)throw new Error('Surface library must load before creating '+surface);
  const m=new Material();m.name=name;
  const colorMap=surface==='metal'?texture:(maps?.color??texture);
  m.initialize({effectName:'builtin-standard',defines:{USE_ALBEDO_MAP:!!colorMap,USE_NORMAL_MAP:!!maps,USE_PBR_MAP:!!maps?.pbr,USE_ALPHA_TEST:alphaTest,USE_VERTEX_COLOR:name==='Road'||vertexColors,USE_INSTANCING:true},states:states??(alphaTest?{rasterizerState:{cullMode:gfx.CullMode.NONE}}:undefined)});
  m.setProperty('mainColor',tint);m.setProperty('roughness',maps?.pbr?1:surface?ROUGHNESS[surface]:.86);
  m.setProperty('metallic',surface==='metal'?.48:0);
  m.setProperty('specularIntensity',.5);
  if(colorMap)m.setProperty('mainTexture',colorMap);
  if(maps){m.setProperty('normalMap',maps.normal);m.setProperty('normalStrength',surface==='fabric'?.45:surface==='grass'?.55:maps.pbr?1:.65);}
  if(maps?.pbr){m.setProperty('pbrMap',maps.pbr);m.setProperty('occlusion',1);}
  m.setProperty('tilingOffset',new Vec4(tiling,tiling,0,0));
  return m;
 }

 static actor(source:Material):Material {
  const name=source.name.toLowerCase(),part=name.split('_').pop()??'';
  const dye=source.getProperty('mainColor') as Color|null;
  const oldTexture=(source.getProperty('mainTexture')??source.getProperty('albedoMap')) as Texture2D|null;
  let surface:Surface|undefined;
  if(['vest','belt'].includes(part))surface='leather';
  if(['linen','trousers','mantle','parchment'].includes(part))surface='fabric';
  if(['steel','armor'].includes(part))surface='metal';
  if(part==='wood')surface='wood';
  const tint=surface&&surface!=='metal'?(dye?.clone()??Color.WHITE.clone()):Color.WHITE.clone();
  const alphaCard=['brows','haircards','lashes'].includes(part);
  const m=this.create(source.name+'-PBR',surface,tint,surface==='fabric'?4:1,!surface||surface==='metal'?(oldTexture??undefined):undefined,alphaCard);
  if(alphaCard)m.setProperty('alphaThreshold',part==='lashes'?.3:.35);
  if(surface==='leather')m.setProperty('albedoScale',new Vec3(2.5,2.62,3.55));
  if(surface==='metal'){
   m.setProperty('metallic',.5);m.setProperty('normalStrength',.14);
  }
  if(!surface&&oldTexture){
   // Skin, eyes, brows, hair and brass already have colored UV maps. A white
   // multiplier removes the FBX importer's second application of their dye.
   m.setProperty('mainTexture',oldTexture);
  }
  if(part==='skin'){m.setProperty('roughness',.73);m.setProperty('specularIntensity',.25);}
  if(part==='hair'||part==='haircards'){m.setProperty('roughness',.88);m.setProperty('specularIntensity',.12);}
  if(part==='lashes')m.setProperty('roughness',.9);
  if(part==='eyes'){m.setProperty('roughness',.24);m.setProperty('specularIntensity',.55);}
  if(part==='brass'){m.setProperty('metallic',.58);m.setProperty('roughness',.4);}
  return m;
 }
}
