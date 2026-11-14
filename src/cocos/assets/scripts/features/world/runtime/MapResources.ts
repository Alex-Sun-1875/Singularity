import {Asset,Texture2D} from 'cc';
import type {AreaDef} from '../../../core/Contracts';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import {getMapArt} from '../data/MapArt';

type AssetType<T extends Asset>={new(...args:any[]):T};
type Region={assets:Set<Asset>;loaded:Map<string,Asset>;pending:Map<string,Promise<Asset>>;prefetched:Set<string>;allowed:Set<string>|null};
const createRegion=(allowed:Set<string>|null=null):Region=>({assets:new Set(),loaded:new Map(),pending:new Map(),prefetched:new Set(),allowed});
const surfacePaths=(area:AreaDef)=>area.id==='S01-T1'?['flat2d/maps/inn-readable-v4/texture']:
 Array.from(new Set(Object.values(getMapArt(area)).filter((value):value is {resource:string}=>!!value&&typeof value==='object'&&'resource'in value).map(surface=>surface.resource+'/texture')));
const keyPath=(key:string)=>key.slice(key.indexOf(':')+1);

/** Own decoded map resources only in the current one-hop exit neighborhood.
 * Adjacent maps warm their surface textures through Cocos, without constructing
 * hidden scenes/physics/AI. All warmed assets have explicit owners, so even
 * assets never entered can be released when their map leaves the neighborhood.
 */
export class MapResources {
 private regions=new Map<string,Region>();private current='';private revision=0;private disposed=false;
 private prefetching:Promise<void>=Promise.resolve();
 trimNeighbors(){
  this.revision++;
  for(const [id,region]of this.regions)if(id!==this.current){
   const empty=createRegion(region.allowed);this.regions.set(id,empty);
   for(const asset of region.assets)asset.decRef();region.assets.clear();region.loaded.clear();region.pending.clear();
  }
 }
 select(area:AreaDef,lookup:(id:string)=>AreaDef|undefined){
  if(this.disposed)return;
  this.current=area.id;this.revision++;
  const ids=new Set([area.id,...area.exits.map(exit=>exit.to).filter(id=>!!lookup(id))]);
  for(const [id,region]of this.regions)if(!ids.has(id)){this.regions.delete(id);for(const asset of region.assets)asset.decRef();region.assets.clear();region.loaded.clear();region.pending.clear();}
  for(const id of ids){
   if(!this.regions.has(id))this.regions.set(id,createRegion());const scope=this.regions.get(id)!;
   scope.allowed=id===this.current?null:new Set(surfacePaths(lookup(id)!));
   if(!scope.allowed)continue;
   // Leaving a map retires its cast/props atlases immediately. Only neighboring
   // surface warm-up survives; entering it rebuilds its actual actor resources.
   for(const key of scope.pending.keys())if(!scope.allowed.has(keyPath(key)))scope.pending.delete(key);
   for(const key of scope.loaded.keys())if(!scope.allowed.has(keyPath(key)))scope.loaded.delete(key);
   const retained=new Set(scope.loaded.values());for(const asset of scope.assets)if(!retained.has(asset)){scope.assets.delete(asset);asset.decRef();}
  }
 }
 load<T extends Asset>(area:string,path:string,type:AssetType<T>,complete:(error:Error|null,asset:T)=>void){
  const region=this.regions.get(area);
  if(this.disposed||!region||region.allowed&&!region.allowed.has(path)){complete(new Error('Map resource scope is closed: '+area+'/'+path),null);return;}
  const key=type.name+':'+path;let pending=region.pending.get(key) as Promise<T>|undefined;
  if(!pending){
   pending=new Promise<T>((resolve,reject)=>resources.load(path,type,(error,asset)=>{
    if(error){reject(error);return;}
    if(!this.disposed&&this.regions.get(area)===region&&region.pending.get(key)===pending&&(!region.allowed||region.allowed.has(path))){if(!region.assets.has(asset)){asset.addRef();region.assets.add(asset);}region.loaded.set(key,asset);}
    else {asset.addRef();asset.decRef();}
    resolve(asset);
   }));region.pending.set(key,pending);pending.catch(()=>{if(region.pending.get(key)===pending)region.pending.delete(key);});
  }
  void pending.then(asset=>complete(null,asset),error=>complete(error,null));
 }
 /** Begin after the current map has become playable; never block its input. */
 prefetch(lookup:(id:string)=>AreaDef|undefined){
  const revision=this.revision;
  // A single chain bounds platform file work even across rapid map changes.
  this.prefetching=this.prefetching.catch(()=>{}).then(async()=>{
   for(const [id,region]of this.regions){
    if(this.disposed||revision!==this.revision)return;
    if(id===this.current)continue;const area=lookup(id);if(!area)continue;
    const paths=surfacePaths(area);
    for(const path of paths){
     if(this.disposed||revision!==this.revision||this.regions.get(id)!==region)return;
     if(region.prefetched.has(path))continue;
     await new Promise<void>(resolve=>this.load(id,path,Texture2D,(error)=>{if(!error)region.prefetched.add(path);else console.warn('[MapResources] Adjacent surface load failed',id,path,error.message);resolve();}));
    }
   }
  });
 }
 inspect(){return {current:this.current,retainedAreas:Array.from(this.regions.keys()),areas:Array.from(this.regions,([id,region])=>({id,residentAssets:region.assets.size,textureBytes:Array.from(region.assets).reduce((n,a)=>n+(a instanceof Texture2D?a.getGFXTexture()?.size??0:0),0),prefetchedFiles:region.prefetched.size})),neighborPolicy:'direct outgoing exits, one hop; neighboring surfaces warm without scene instances'};}
 destroy(){this.disposed=true;this.revision++;for(const region of this.regions.values())for(const asset of region.assets)asset.decRef();this.regions.clear();}
}
