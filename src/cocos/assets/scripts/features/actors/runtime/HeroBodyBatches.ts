import {Asset,Material,Mesh,Node,SkinnedMeshRenderer} from 'cc';

type Piece={renderer:SkinnedMeshRenderer;slot:number;material:Material};
type Batch={node:Node;renderer:SkinnedMeshRenderer;mesh:Mesh};

/** Merge only opaque, identically shaded clothing driven by the same skeleton.
 * Native Mesh.merge copies the original attributes and offsets indices. No
 * texture atlas, simplification, shader replacement or animation change. */
export class HeroBodyBatches {
 private sources:SkinnedMeshRenderer[]=[];
 private batches:Batch[]=[];
 private disposed=false;
 private batched=false;
 private ids=new WeakMap<object,number>();private nextId=0;
 private id(value:object){let id=this.ids.get(value);if(id===undefined){id=++this.nextId;this.ids.set(value,id);}return id;}
 private value(value:any):any {
  if(value instanceof Asset)return {asset:this.id(value)};
  if(Array.isArray(value)||ArrayBuffer.isView(value))return Array.from(value as any,v=>this.value(v));
  if(value&&typeof value==='object')return Object.fromEntries(['x','y','z','w','r','g','b','a'].filter(k=>typeof value[k]==='number').map(k=>[k,value[k]]));
  return value;
 }
 private materialKey(material:Material){
  const effect=material.effectAsset;
  if(!effect||material.effectName!=='builtin-standard'||material.passes[0]?.blendState.targets.some(t=>t.blend))return;
  return JSON.stringify({effect:this.id(effect),technique:material.technique,passes:material.passes.map(pass=>pass.hash),
   properties:effect.techniques[material.technique].passes.map((pass,index)=>Object.fromEntries(Object.keys(pass.properties??{}).map(key=>[key,this.value(material.getProperty(key,index))])))});
 }
 prepare(model:Node):void {
  if(this.disposed||this.batches.length)return;
  const groups=new Map<string,Piece[]>();
  const candidates=model.getComponentsInChildren(SkinnedMeshRenderer).filter(r=>r.enabled&&r.node.activeInHierarchy&&r.skeleton&&r.skinningRoot&&r.mesh&&!r.mesh.struct.morph&&!r.mesh.struct.dynamic&&/^raphael_native_(arms|body|feet|legs|pauldrons)_/.test(r.node.name));
  for(const renderer of candidates){
   const mesh=renderer.mesh!,materials=mesh.struct.primitives.map((_,slot)=>renderer.getSharedMaterial(slot));
   const keys=materials.map(material=>material&&this.materialKey(material));if(keys.some(key=>!key))continue;
   const n=renderer.node,p=n.position,q=n.rotation,s=n.scale;
   for(let slot=0;slot<mesh.struct.primitives.length;slot++){
    const primitive=mesh.struct.primitives[slot],layout=primitive.vertexBundelIndices.map(i=>mesh.struct.vertexBundles[i].attributes);
    const key=JSON.stringify([keys[slot],layout,primitive.primitiveMode,this.id(renderer.skeleton!),this.id(renderer.skinningRoot!),this.id(n.parent!),n.layer,p.x,p.y,p.z,q.x,q.y,q.z,q.w,s.x,s.y,s.z,renderer.shadowCastingMode,renderer.receiveShadow]);
    const group=groups.get(key)??[];group.push({renderer,slot,material:materials[slot]!});groups.set(key,group);
   }
  }
  const affected=new Set(Array.from(groups.values()).filter(g=>g.length>1).flatMap(g=>g.map(p=>p.renderer)));
  if(!affected.size)return;
  try{
   for(const group of groups.values()){
    const pieces=group.filter(p=>affected.has(p.renderer));if(!pieces.length)continue;
    const source=pieces[0].renderer,mesh=new Mesh();mesh.name='HeroClothingBatch';mesh.addRef();
    const node=new Node('HeroClothingBatch');node.active=false;node.layer=source.node.layer;source.node.parent!.addChild(node);node.setRTS(source.node.rotation,source.node.position,source.node.scale);
    const renderer=node.addComponent(SkinnedMeshRenderer);this.batches.push({node,renderer,mesh});
    let first=true;
    for(const piece of pieces){
     const original=piece.renderer.mesh!,struct=JSON.parse(JSON.stringify(original.struct)) as Mesh.IStruct;
     struct.primitives=[struct.primitives[piece.slot]];
     struct.vertexBundles=struct.primitives[0].vertexBundelIndices.map(i=>struct.vertexBundles[i]);
     struct.primitives[0].vertexBundelIndices=struct.vertexBundles.map((_,i)=>i);
     const part=new Mesh();part.reset({struct,data:original.data});
     try{if(!mesh.merge(part,undefined,!first))throw new Error('Hero mesh layouts cannot be merged');}finally{part.destroy();}
     first=false;
    }
    renderer.mesh=mesh;renderer.skeleton=source.skeleton;renderer.skinningRoot=source.skinningRoot;
    renderer.setSharedMaterial(pieces[0].material,0);renderer.shadowCastingMode=source.shadowCastingMode;renderer.receiveShadow=source.receiveShadow;
   }
   this.sources=Array.from(affected);
   for(const source of this.sources)source.node.on(Node.EventType.ACTIVE_IN_HIERARCHY_CHANGED,this.sync,this);
   this.sync();
  }catch(error){this.destroy();console.warn('[HeroBodyBatches] Keeping separate clothing renderers',error);}
 }
 private sync(){
  if(this.disposed)return;
  const visible=this.sources.every(source=>source.isValid&&source.node.activeInHierarchy);
  if(visible===this.batched)return;this.batched=visible;
  for(const source of this.sources)if(source.isValid)source.enabled=!visible;
  for(const batch of this.batches)if(batch.node.isValid)batch.node.active=visible;
 }
 destroy(){
  if(this.disposed)return;this.disposed=true;
  for(const source of this.sources){if(!source.isValid)continue;source.node.off(Node.EventType.ACTIVE_IN_HIERARCHY_CHANGED,this.sync,this);source.enabled=true;}this.sources=[];
  for(const {node,renderer,mesh}of this.batches){if(node.isValid){node.active=false;renderer.mesh=null;renderer.skeleton=null;renderer.skinningRoot=null;node.destroy();}mesh.decRef(false);if(mesh.refCount===0)mesh.destroy();}this.batches=[];
 }
}
