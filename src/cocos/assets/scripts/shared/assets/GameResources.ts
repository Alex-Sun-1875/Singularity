import {Asset,AssetManager,assetManager,resources as localResources} from 'cc';
import {isTapMinigame} from '../../platform/RuntimePlatform';
import {htmlBundlePreview} from '../../platform/HtmlPreview';
import {loadBundleWithDependencies} from './AssetBundles';
import {RESOURCE_PACKS,RESOURCE_ASSET_PACKS} from './ResourcePacks';

/** Explicit HTML bundle preview shares the resource graph, never platform identity. */
export const usesAssetBundles=isTapMinigame||htmlBundlePreview();
type AssetType<T extends Asset>={new(...args:any[]):T};
function loadAsset<T extends Asset>(bundle:AssetManager.Bundle,path:string,type:AssetType<T>,complete:(error:Error|null,asset:T)=>void,priority?:number):void {
 const load=()=>priority===undefined?bundle.load(path,type,complete):assetManager.loadAny({path,type,bundle:bundle.name},{priority},complete);
 const cached=bundle.get(path,type);
 if(!cached?.isValid){load();return;}
 // Keep callbacks asynchronous, without re-entering Cocos' frame-throttled
 // loading pipeline for assets already resident in its own cache.
 void Promise.resolve().then(()=>{if(cached.isValid)complete(null,cached);else load();});
}

/** Keep authored resource paths intact, using Cocos' own lazy bundle loader.
 * Ordinary editor/Web previews continue to use their existing resources bundle. */
export const gameResources={
 get<T extends Asset>(path:string,type:AssetType<T>):T|null {
  const exact=usesAssetBundles&&RESOURCE_ASSET_PACKS[path];
  if(exact){const asset=assetManager.assets.get(exact.uuid);return asset?.isValid&&asset instanceof type?asset:null;}
  const route=usesAssetBundles&&RESOURCE_PACKS.find(pack=>path.startsWith(pack.prefix));
  const asset=route?assetManager.getBundle(route.bundle)?.get(path.slice(route.prefix.length),type):localResources.get(path,type);
  return asset?.isValid?asset:null;
 },
 load<T extends Asset>(path:string,type:AssetType<T>,complete:(error:Error|null,asset:T)=>void,priority?:number):void {
  if(!usesAssetBundles){loadAsset(localResources,path,type,complete,priority);return;}
  const exact=RESOURCE_ASSET_PACKS[path];
  if(exact){
   void loadBundleWithDependencies(exact.bundle).then(()=>{
    const cached=gameResources.get(path,type);
    if(cached)void Promise.resolve().then(()=>{if(cached.isValid)complete(null,cached);else assetManager.loadAny({uuid:exact.uuid,bundle:exact.bundle},{priority:priority??0},complete);});
    else assetManager.loadAny({uuid:exact.uuid,bundle:exact.bundle},{priority:priority??0},complete);
   },error=>complete(error instanceof Error?error:new Error(String(error)),null));return;
  }
  const route=RESOURCE_PACKS.find(pack=>path.startsWith(pack.prefix));
  if(!route){loadAsset(localResources,path,type,complete,priority);return;}
  void loadBundleWithDependencies(route.bundle).then(bundle=>{
   loadAsset(bundle,path.slice(route.prefix.length),type,complete,priority);
  },error=>complete(error instanceof Error?error:new Error(String(error)),null));
 },
 release(path:string,type?:AssetType<Asset>):void {
  const exact=usesAssetBundles&&RESOURCE_ASSET_PACKS[path];
  if(exact){const asset=assetManager.assets.get(exact.uuid);if(asset&&(!type||asset instanceof type))assetManager.releaseAsset(asset);return;}
  const route=usesAssetBundles&&RESOURCE_PACKS.find(pack=>path.startsWith(pack.prefix));
  if(route)assetManager.getBundle(route.bundle)?.release(path.slice(route.prefix.length),type);
  else localResources.release(path,type);
 },
};
