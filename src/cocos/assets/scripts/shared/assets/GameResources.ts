import {Asset,AssetManager,assetManager,resources as localResources} from 'cc';
import {MINIGAME} from 'cc/env';
import {loadBundleWithDependencies} from './AssetBundles';
import {RESOURCE_PACKS} from './ResourcePacks';

/** The browser release preview exercises the same resource graph as TapTap. */
export const isTapRelease=MINIGAME||(globalThis as any).__TAP_RELEASE__===true;
type AssetType<T extends Asset>={new(...args:any[]):T};
function loadAsset<T extends Asset>(bundle:AssetManager.Bundle,path:string,type:AssetType<T>,complete:(error:Error|null,asset:T)=>void):void {
 const cached=bundle.get(path,type);
 if(!cached?.isValid){bundle.load(path,type,complete);return;}
 // Keep callbacks asynchronous, without re-entering Cocos' frame-throttled
 // loading pipeline for assets already resident in its own cache.
 void Promise.resolve().then(()=>{if(cached.isValid)complete(null,cached);else bundle.load(path,type,complete);});
}

/** Keep authored resource paths intact, using Cocos' own lazy bundle loader.
 * Ordinary editor/Web previews continue to use their existing resources bundle. */
export const gameResources={
 get<T extends Asset>(path:string,type:AssetType<T>):T|null {
  const route=isTapRelease&&RESOURCE_PACKS.find(pack=>path.startsWith(pack.prefix));
  const asset=route?assetManager.getBundle(route.bundle)?.get(path.slice(route.prefix.length),type):localResources.get(path,type);
  return asset?.isValid?asset:null;
 },
 load<T extends Asset>(path:string,type:AssetType<T>,complete:(error:Error|null,asset:T)=>void):void {
  if(!isTapRelease){loadAsset(localResources,path,type,complete);return;}
  const route=RESOURCE_PACKS.find(pack=>path.startsWith(pack.prefix));
  if(!route){loadAsset(localResources,path,type,complete);return;}
  void loadBundleWithDependencies(route.bundle).then(bundle=>{
   loadAsset(bundle,path.slice(route.prefix.length),type,complete);
  },error=>complete(error instanceof Error?error:new Error(String(error)),null));
 },
 release(path:string,type?:AssetType<Asset>):void {
  const route=isTapRelease&&RESOURCE_PACKS.find(pack=>path.startsWith(pack.prefix));
  if(route)assetManager.getBundle(route.bundle)?.release(path.slice(route.prefix.length),type);
  else localResources.release(path,type);
 },
};
