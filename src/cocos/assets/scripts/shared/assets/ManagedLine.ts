import {_decorator,director,Line} from 'cc';

const {ccclass}=_decorator;

/** Creator 3.8.8 Line/LineModel omit destruction of their owned model/mesh.
 * Keep native Line rendering; release only this component's allocations.
 * Shared VfxAssets materials remain owned by their asset cache.
 */
@ccclass('ManagedLine')
export class ManagedLine extends Line {
 onDestroy():void {
  const models=this._models.splice(0);
  const meshes=new Set(models.flatMap(model=>model.subModels.map(sub=>sub.subMesh)).filter(Boolean));
  for(const model of models){if(director.root)director.root.destroyModel(model);else model.destroy();}
  for(const mesh of meshes)mesh.destroy();
  // Renderer.setSharedMaterial destroys the old per-component instance.
  // Line's 3.8.8 base classes have no onDestroy hook to do this for us.
  this.setSharedMaterial(null,0);
 }
}
