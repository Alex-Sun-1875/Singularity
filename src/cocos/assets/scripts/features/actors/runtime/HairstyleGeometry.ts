import {Asset,Material,Mesh,Node,SkeletalAnimation,SkinnedMeshRenderer} from 'cc';
import {loadBundleWithDependencies} from '../../../shared/assets/AssetBundles';

/** A hairstyle owns one imported mesh and its source material. The existing hero
 * skeleton drives it; no duplicate prefab, skeleton nodes or animation clips. */
export class HairstyleGeometry {
 private assets=new Set<Asset>();private renderers:SkinnedMeshRenderer[]=[];private disposed=false;
 async mount(resource:string,root:Node,animation:SkeletalAnimation,current:()=>boolean){
  const bundle=await loadBundleWithDependencies('actor-raphael');
  const load=<T extends Asset>(type:{new(...args:any[]):T})=>new Promise<T>((resolve,reject)=>{
   const entries=bundle.getDirWithPath(resource,type);if(entries.length!==1){reject(new Error('Expected one hairstyle '+type.name+': '+resource));return;}
   bundle.load(entries[0].path,type,(error,asset)=>{if(error){reject(error);return;}asset.addRef();if(this.disposed){asset.decRef();reject(new Error('Hairstyle geometry was disposed'));return;}this.assets.add(asset);resolve(asset);});
  });
  const [mesh,material]=await Promise.all([load(Mesh),load(Material)]);
  if(this.disposed||!current())return;
  const skeleton=animation.node.getComponentsInChildren(SkinnedMeshRenderer).find(renderer=>renderer.skeleton)?.skeleton;
  if(!skeleton)throw new Error('Hero skeleton is unavailable for hairstyle');
  const renderer=root.addComponent(SkinnedMeshRenderer);renderer.enabled=false;this.renderers.push(renderer);
  renderer.mesh=mesh;renderer.skeleton=skeleton;renderer.skinningRoot=animation.node;renderer.setSharedMaterial(material,0);renderer.shadowCastingMode=1;renderer.receiveShadow=1;
 }
 show(){for(const renderer of this.renderers)renderer.enabled=true;}
 // Native teardown disposes skin and material bindings together.
 destroy(){if(this.disposed)return;this.disposed=true;for(const renderer of this.renderers){if(!renderer.isValid)continue;renderer.enabled=false;renderer.destroy();}this.renderers=[];for(const asset of this.assets)asset.decRef();this.assets.clear();}
}
