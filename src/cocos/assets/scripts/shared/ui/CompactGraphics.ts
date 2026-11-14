import {_decorator,Graphics,gfx,sys} from 'cc';

const {ccclass}=_decorator;
const capacity=(count:number,limit:number)=>Math.min(limit,2**Math.ceil(Math.log2(Math.max(256,count))));

/** Cocos 3.8.8 Web Graphics reserves 65535 vertices for every submodel, even
 * for a four-vertex rectangle. Keep its native tessellation, material, mask
 * integration and upload; size only the GFX buffers to the actual geometry.
 * Uses the documented protected upload hook, not a global engine patch.
 */
@ccclass('CompactGraphics')
export class CompactGraphics extends Graphics {
 private readonly fitted=new WeakSet<gfx.Buffer>();
 private fit(buffer:gfx.Buffer,count:number,limit:number){
  const required=count*buffer.stride;
  if(this.fitted.has(buffer)&&buffer.size>=required)return;
  const bytes=capacity(count,limit)*buffer.stride;
  if(buffer.size!==bytes)buffer.resize(bytes);
  this.fitted.add(buffer);
 }
 protected _uploadData():void {
  // Native UI uses its own proxy/upload path; this adapter targets the WebGL
  // backend used by TapTap mini-games and by the browser verification builds.
  if(!sys.isNative){
   const data=this.impl?.getRenderDataList(),models=this.model?.subModels;
   if(data&&models)for(let i=0;i<data.length;i++){
    const ia=models[i]?.inputAssembler;if(!ia)continue;
    const vertices=data[i].vertexStart,indices=data[i].indexStart;
    if(vertices>0&&ia.vertexBuffers[0])this.fit(ia.vertexBuffers[0],vertices,65535);
    if(indices>0&&ia.indexBuffer)this.fit(ia.indexBuffer,indices,131070);
   }
  }
  super._uploadData();
 }
}
