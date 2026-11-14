import {assetManager,AssetManager} from 'cc';
const pending=new Map<string,Promise<AssetManager.Bundle>>();
/** Cocos deduplicates equal materials into the highest-priority bundle. Resolve
 * only dependency manifests before loading a prefab, including resources deps. */
export function loadBundleWithDependencies(name:string,chain:string[]=[]):Promise<AssetManager.Bundle>{
 if(chain.includes(name))return Promise.reject(new Error('Cyclic asset bundles: '+[...chain,name].join(' → ')));
 const cached=pending.get(name);if(cached)return cached;
 const promise=(async()=>{
  const bundle=assetManager.getBundle(name)??await new Promise<AssetManager.Bundle>((resolve,reject)=>assetManager.loadBundle(name,(error,value)=>error?reject(error):resolve(value)));
  await Promise.all(bundle.deps.map(id=>loadBundleWithDependencies(id,[...chain,name])));return bundle;
 })();pending.set(name,promise);promise.catch(()=>pending.delete(name));return promise;
}
