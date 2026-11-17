import {Texture2D,Camera,Color,Material,Mesh,MeshRenderer,Node,Vec3,gfx,utils} from 'cc';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import type {Point} from '../../../core/Contracts';

const REFERENCE_WIDTHS=[0.54676,0.92337,0.88163,0.84195,1.05211,1.11289,1.03535,1.10922,1.28738,1.38448,1.37584,1.2494,1.2067,1.21707,1.28649,1.32346,1.24583,1.26919,1.27579,1.14731,0.99582,0.95044,0.89116,0.65449,0.56587,0.6553,0.79035,0.90352,0.9228,0.89244,0.87184,0.92656,0.99025,1.02286,1.0761,1.03973,1.05235,1.12736,1.19206,1.25107,1.20869,1.16581,1.04969,0.95076,0.91916,0.96121,0.98295,1.00033,1.05146,0.97546,0.94096,1.00152,1.07789,1.00714,0.89503,0.80555,0.73806,0.79419,0.83759,0.83722,0.76733,0.69634,0.79012,1.08847,1.29166] as const;
type Geometry={positions:number[];colors:number[];uvs?:number[];indices:number[];minPos:Vec3;maxPos:Vec3;boundingRadius:number};
type Field={key:string;root:Node;renderer:MeshRenderer;material:Material;mesh?:Mesh;positions?:Float32Array;colors?:Float32Array;uvs?:Float32Array;indices?:Uint16Array|Uint32Array;stamp:string;touched:boolean;width:number;depth:number;paths:number;vertices:number;pulse:number;alpha:number};
type Beam={points:readonly Vec3[];width:number;alpha:number;role:'launch'|'chain'|'launchDetail'|'chainDetail'|'accent'};
const LIMIT=8,TAU=Math.PI*2;
const bands=[-1,-.55,-.15,-.055,0,.055,.15,.55,1];
const hash=(key:string)=>{let n=2166136261;for(let i=0;i<key.length;i++)n=Math.imul(n^key.charCodeAt(i),16777619);return n>>>0;};
const noise=(n:number)=>{const v=Math.sin(n*127.1+91.7)*43758.5453;return v-Math.floor(v);};

/** A spread-out discharge sheet, independent of the actor-to-actor skeleton.
 * Dozens of free-ended fractures and forks share one native coloured mesh.
 * This adapter only observes resolved impact positions and never submits hits. */
export class ThunderArcField {
 private readonly root:Node;
 private readonly items:Field[]=[];
 private disposed=false;
 private readonly color=new Color(255,255,255,255);
 constructor(parent:Node,private readonly at:(point:Point,height:number)=>Vec3){this.root=new Node('ThunderArcFields');this.root.layer=parent.layer;parent.addChild(this.root);}
 begin(){this.renderedBeams.length=0;this.beamBatches.clear();for(const item of this.items)item.touched=false;}
 private geometry(center:Point,width:number,depth:number,rank:number,seeds:readonly Point[],seed:number):{data:Geometry;paths:number}{
  const count=seeds.length;
  const positions:number[]=[],colors:number[]=[],indices:number[]=[],origin=this.at(center,0);
  const minPos=new Vec3(Infinity,Infinity,Infinity),maxPos=new Vec3(-Infinity,-Infinity,-Infinity);let paths=0,radius=0;
  const bounded=(p:Point):Point=>{const r=Math.pow(Math.pow(Math.abs(p.x)/(width*.5),4)+Math.pow(Math.abs(p.z)/(depth*.5),4),.25);return r>.97?{x:p.x*.97/r,z:p.z*.97/r}:p;};
  const random=(n:number):Point=>{const a=noise(seed+n*31)*TAU,r=Math.sqrt(noise(seed+n*47+9))*.91;return{x:Math.cos(a)*width*.5*r,z:Math.sin(a)*depth*.5*r};};
  const path=(a:Point,b:Point,key:number,height:number,fork=false)=>{
   const dx=b.x-a.x,dz=b.z-a.z,length=Math.hypot(dx,dz),steps=Math.max(5,Math.min(80,Math.ceil(length/.14))),points:Point[]=[];
   const px=-dz/Math.max(.001,length),pz=dx/Math.max(.001,length),start=positions.length/3,widthScale=fork?.13:.21+.006*rank;
   for(let i=0;i<=steps;i++){
    const t=i===0?0:i===steps?1:(i+(noise(key+i*53)-.5)*.35)/steps,envelope=Math.pow(Math.max(0,Math.sin(Math.PI*t)),.4),frequency=t*length*1.35,coarse=Math.floor(frequency),blend=frequency-coarse,drift=(noise(key+coarse*29)*2-1)*(1-blend)+(noise(key+(coarse+1)*29)*2-1)*blend,bend=(drift*.22+(noise(key+i*43)*2-1)*.035)*envelope;
    const p=bounded({x:a.x+dx*t+px*bend,z:a.z+dz*t+pz*bend});points.push(p);
    const taper=Math.min(1,t*9,(1-t)*9),brightness=(fork?.57:.84)*( .68+.32*noise(key+i*11));
    for(const band of bands){
     const q={x:center.x+p.x+px*band*widthScale*taper,z:center.z+p.z+pz*band*widthScale*taper},h=height+(noise(key+i*7)*2-1)*.09*envelope,v=this.at(q,h).subtract(origin),edge=Math.abs(band),core=edge<=.055;
     positions.push(v.x,v.y,v.z);
     const alpha=(edge>=1?0:core?.94:edge<=.15?.40:edge<=.55?.20:.025)*brightness*taper;
     colors.push(core?.48:.13,core?.61:.23,1,alpha);
     minPos.x=Math.min(minPos.x,v.x);minPos.y=Math.min(minPos.y,v.y);minPos.z=Math.min(minPos.z,v.z);maxPos.x=Math.max(maxPos.x,v.x);maxPos.y=Math.max(maxPos.y,v.y);maxPos.z=Math.max(maxPos.z,v.z);radius=Math.max(radius,v.length());
    }
   }
   for(let i=0;i<steps;i++)for(let j=0;j<bands.length-1;j++){const a=start+i*bands.length+j,b=a+1,c=a+bands.length,d=c+1;indices.push(a,c,b,b,c,d);}
   paths++;return points;
  };
  const trunks=4+Math.ceil(count*.8);
  for(let i=0;i<trunks;i++){
   const anchor=count>1&&i<count?seeds[i]:undefined,a=anchor?bounded({x:anchor.x-center.x+(noise(seed+i*17)-.5)*1.1,z:anchor.z-center.z+(noise(seed+i*23)-.5)*1.1}):random(i*2+1);let b=random(i*2+2);if(Math.hypot(a.x-b.x,a.z-b.z)<Math.min(width,depth)*.3)b={x:-a.x,z:-a.z};
   // Several heights create a loose electric volume, rather than a flat grid
   // stamped on the floor or a set of lines ending only at people's chests.
   const height=.52+(i%3)*.28,points=path(a,b,seed+i*101,height),forks=1+(i%3===0?1:0);
   for(let j=0;j<forks;j++){
    const at=points[Math.max(1,Math.min(points.length-2,Math.round(points.length*(.22+j*.24))))],angle=noise(seed+i*71+j*13)*TAU,reach=.38+noise(seed+i*97+j*23)*Math.min(1.4,Math.max(width,depth)*.19),end=bounded({x:at.x+Math.cos(angle)*reach,z:at.z+Math.sin(angle)*reach});
    path(at,end,seed+i*211+j*37,height+.06,true);
   }
  }
  return{data:{positions,colors,indices,minPos,maxPos,boundingRadius:radius},paths};
 }
 private readonly beamBatches=new Map<string,Beam[]>();
 private readonly renderedBeams:Beam[]=[];
 private readonly beamMaterials=new WeakMap<Material,boolean>();
 private static referenceTexture?:Texture2D;
 private static referenceLoad?:Promise<void>;
 private static referenceRevision=0;
 camera?:Camera;

 static preload():Promise<void>{
  const revision=this.referenceRevision;
  if(!this.referenceLoad)this.referenceLoad=new Promise<void>((resolve,reject)=>{
   resources.load('vfx/production/thunder-reference-strip-v1/texture',Texture2D,(error,texture)=>{
    if(error){this.referenceLoad=undefined;reject(error);return;}
    if(revision!==this.referenceRevision){reject(new Error('Thunder light load cancelled after disposal'));return;}
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);
    texture.addRef();this.referenceTexture=texture;resolve();
   });
  });
  return this.referenceLoad;
 }
 static dispose(){this.referenceRevision++;this.referenceTexture?.decRef();this.referenceTexture=undefined;this.referenceLoad=undefined;}

 private acquire(key:string,pulse:number,alpha:number):Field|undefined {
  const beam=key.startsWith('beam:');
  let item=this.items.find(item=>item.key===key);
  if(!item)item=this.items.find(item=>!item.touched&&!item.root.active&&this.beamMaterials.get(item.material)===beam);
  if(!item&&this.items.length>=LIMIT){item=this.items.find(item=>!item.touched&&this.beamMaterials.get(item.material)===beam);if(!item)return;}
  if(!item){
   const root=new Node('ThunderArcSheet');root.layer=this.root.layer;root.active=false;this.root.addChild(root);
   const material=new Material();material.name='ProjectProcedural:ThunderArcSheet';
   material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_VERTEX_COLOR:true,USE_TEXTURE:beam},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:beam?gfx.BlendFactor.ONE:gfx.BlendFactor.SRC_ALPHA,blendDst:beam?gfx.BlendFactor.ONE_MINUS_SRC_ALPHA:gfx.BlendFactor.ONE,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
   if(beam){if(!ThunderArcField.referenceTexture)throw Error('Approved thunder light is not prepared');material.setProperty('mainTexture',ThunderArcField.referenceTexture);}
   this.beamMaterials.set(material,beam);
   const renderer=root.addComponent(MeshRenderer);renderer.setSharedMaterial(material,0);renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   item={key,root,renderer,material,stamp:'',touched:false,width:0,depth:0,paths:0,vertices:0,pulse,alpha};
   this.items.push(item);
  }
  return item;
 }

 addBeam(key:string,points:readonly Vec3[],width:number,alpha:number,role:'launch'|'chain'|'launchDetail'|'chainDetail'|'accent'='launchDetail'):void {
  if(this.disposed||points.length<2||alpha<=0)return;
  let batch=this.beamBatches.get(key);
  if(!batch){batch=[];this.beamBatches.set(key,batch);}
  batch.push({points,width,alpha,role});
 }

 private flushBeams():void {
  if(!this.camera?.node.isValid){
   this.camera=this.root.scene?.getComponentsInChildren(Camera).find(camera=>(camera.visibility&this.root.layer)!==0);
  }
  const view=this.camera?.node.forward??new Vec3(0,-1,0);
  const crossSection=[-1,-.74,-.48,-.30,-.17,0,.17,.30,.48,.74,1];
  for(const [key,beams]of this.beamBatches){
   const item=this.acquire('beam:'+key,0,255);
   if(!item)continue;
   // Preserve the cast's small lateral kinks in the oblique 3D camera.
   // Solve the camera projection on XZ so the air arcs retain their real height.
   const launch=beams.find(beam=>beam.role==='launch');
   let align:((point:Vec3)=>Vec3)|undefined;
   if(launch&&this.camera){
    const first=launch.points[0],last=launch.points[launch.points.length-1],delta=last.clone().subtract(first);
    const right=this.camera.node.right,up=this.camera.node.up;
    const sx=delta.x*right.x+delta.y*right.y+delta.z*right.z,sy=-(delta.x*up.x+delta.y*up.y+delta.z*up.z);
    const determinant=-right.x*up.z+right.z*up.x,lengthXZ=delta.x*delta.x+delta.z*delta.z;
    if(Math.abs(determinant)>.0001&&lengthXZ>.01){
     const nx=(sy*up.z-right.z*sx)/determinant,nz=(right.x*sx-sy*up.x)/determinant;
     align=point=>{const x=point.x-first.x,z=point.z-first.z,t=(x*delta.x+z*delta.z)/lengthXZ,s=(x*delta.z-z*delta.x)/lengthXZ;return new Vec3(first.x+delta.x*t-nx*s,point.y,first.z+delta.z*t-nz*s);};
    }
   }
   let presented=align?beams.map(beam=>(beam.role==='launch'||beam.role==='launchDetail')?{...beam,points:beam.points.map(align!)}:beam):beams;
   if(this.camera){
    // Keep the hand-anchored launch intact. Constrain chain bends to a separate
    // corridor so jagged curves cannot cross even when their chords do not.
    const camera=this.camera,cores=presented.filter(beam=>beam.role==='launch'||beam.role==='chain');
    const right=camera.node.right,up=camera.node.up;
    const project=(p:Vec3)=>camera.projection===Camera.ProjectionType.ORTHO?new Vec3(Vec3.dot(p,right),Vec3.dot(p,up),0):camera.worldToScreen(p);
    const projected=new Map(cores.map(beam=>[beam,beam.role==='launch'?beam.points.map(project):[project(beam.points[0]),project(beam.points[beam.points.length-1])]]));
    const separation=(p:Vec3,a:Vec3,b:Vec3)=>{
     const dx=b.x-a.x,dy=b.y-a.y,sq=dx*dx+dy*dy;
     const t=sq>1e-8?Math.max(0,Math.min(1,((p.x-a.x)*dx+(p.y-a.y)*dy)/sq)):0;
     return Math.hypot(p.x-a.x-dx*t,p.y-a.y-dy*t);
    };
    presented=presented.map(beam=>{
     if(beam.role!=='chain')return beam;
     const first=beam.points[0],last=beam.points[beam.points.length-1];
     return {...beam,points:beam.points.map((point,i)=>{
      const t=i/(beam.points.length-1),base=first.clone().add(last.clone().subtract(first).multiplyScalar(t)),s=project(base),p=project(point);
      let clearance=Infinity;
      for(const other of cores){
       if(other===beam)continue;
       const path=projected.get(other)!;
       if(other.role==='launch'){
        for(let j=1;j<path.length;j++)clearance=Math.min(clearance,separation(s,path[j-1],path[j]));
       }else clearance=Math.min(clearance,separation(s,path[0],path[1]));
      }
      const displacement=Math.hypot(p.x-s.x,p.y-s.y),factor=Math.min(1,clearance*.30/Math.max(1e-8,displacement));
      return base.add(point.clone().subtract(base).multiplyScalar(factor));
     })};
    });
   }
   this.renderedBeams.push(...presented);
   const origin=new Vec3();let count=0;
   for(const beam of presented)for(const p of beam.points){origin.add(p);count++;}
   origin.multiplyScalar(1/count);
   const positions:number[]=[],colors:number[]=[],uvs:number[]=[],indices:number[]=[];
   const minPos=new Vec3(Infinity,Infinity,Infinity),maxPos=new Vec3(-Infinity,-Infinity,-Infinity);
   let radius=0;
   for(const beam of presented){
    const first=positions.length/3;
    for(let i=0;i<beam.points.length;i++){
     const point=beam.points[i],before=beam.points[Math.max(0,i-1)],after=beam.points[Math.min(beam.points.length-1,i+1)];
     const tangent=after.clone().subtract(before).normalize();
     const side=Vec3.cross(new Vec3(),tangent,view);
     if(side.lengthSqr()<.00001)Vec3.cross(side,tangent,Vec3.UNIT_Y);
     side.normalize();
     const t=i/(beam.points.length-1),tip=Math.min(1,(t+.015)*10,(1.015-t)*10);
     const address=t*(REFERENCE_WIDTHS.length-1),a=Math.floor(address),b=Math.min(REFERENCE_WIDTHS.length-1,a+1);
     const irregular=beam.role==='launch'||beam.role==='chain'||beam.role==='accent'?Math.min(1.35,REFERENCE_WIDTHS[a]+(REFERENCE_WIDTHS[b]-REFERENCE_WIDTHS[a])*(address-a)):.70+.30*(.5+.5*Math.sin(i*.71+beam.points[0].x*3.1));
     const halfWidth=beam.width*.5*tip*irregular;
     for(const band of crossSection){
      const p=point.clone().add(side.clone().multiplyScalar(band*halfWidth)).subtract(origin);
      positions.push(p.x,p.y,p.z);
      const strength=beam.alpha/255;
      colors.push(strength,strength,strength,strength);
      uvs.push(t,(band+1)*.25+((beam.role==='launch'||beam.role==='chain'||beam.role==='accent')?0:.5));
      minPos.x=Math.min(minPos.x,p.x);minPos.y=Math.min(minPos.y,p.y);minPos.z=Math.min(minPos.z,p.z);
      maxPos.x=Math.max(maxPos.x,p.x);maxPos.y=Math.max(maxPos.y,p.y);maxPos.z=Math.max(maxPos.z,p.z);radius=Math.max(radius,p.length());
     }
    }
    for(let i=0;i<beam.points.length-1;i++)for(let j=0;j<crossSection.length-1;j++){
     const a=first+i*crossSection.length+j,b=a+1,c=a+crossSection.length;
     indices.push(a,c,b,b,c,c+1);
    }
   }
   this.upload(item,{positions,colors,uvs,indices,minPos,maxPos,boundingRadius:radius});
   item.key='beam:'+key;item.touched=true;item.stamp='';item.paths=beams.length;item.vertices=positions.length/3;
   item.root.setWorldPosition(origin);this.color.set(255,255,255,255);item.material.setProperty('mainColor',this.color);
   item.root.active=true;
  }
 }

 private upload(item:Field,data:Geometry){
  const vertices=data.positions.length/3,indices=data.indices.length;
  const grow=!item.mesh||vertices>item.positions!.length/3||indices>item.indices!.length;
  if(grow){
   const vertexCapacity=2**Math.ceil(Math.log2(Math.max(1,vertices,(item.positions?.length??0)/3))),indexCapacity=2**Math.ceil(Math.log2(Math.max(1,indices,item.indices?.length??0)));
   item.positions=new Float32Array(vertexCapacity*3);item.colors=new Float32Array(vertexCapacity*4);
   item.indices=vertexCapacity>65536?new Uint32Array(indexCapacity):new Uint16Array(indexCapacity);
  }
  item.positions!.set(data.positions);item.colors!.set(data.colors);item.indices!.set(data.indices);
  if(data.uvs){if(!item.uvs||item.uvs.length<item.positions!.length/3*2)item.uvs=new Float32Array(item.positions!.length/3*2);item.uvs.set(data.uvs);}
  // The bundled unlit vertex-color shader needs neither normals nor UVs.
  // Reuse native dynamic buffers between pulses, growing only when necessary.
  const geometry={uvs:data.uvs?item.uvs!.subarray(0,data.uvs.length):undefined,positions:item.positions!.subarray(0,data.positions.length),colors:item.colors!.subarray(0,data.colors.length),minPos:data.minPos,maxPos:data.maxPos,indices16:item.indices instanceof Uint16Array?item.indices.subarray(0,indices):undefined,indices32:item.indices instanceof Uint32Array?item.indices.subarray(0,indices):undefined};
  if(grow){
   const previous=item.mesh;
   item.mesh=utils.MeshUtils.createDynamicMesh(0,geometry,undefined,{maxSubMeshes:1,maxSubMeshVertices:item.positions!.length/3,maxSubMeshIndices:item.indices!.length});
   item.mesh.name='ThunderFreeDischarges';item.root.active=true;item.renderer.mesh=item.mesh;previous?.destroy();
  }else{item.mesh!.updateSubMesh(0,geometry);item.renderer.onGeometryChanged();}
 }
 draw(key:string,points:readonly Point[],rank:number,alpha:number,pulse:number){
  if(this.disposed||!points.length||alpha<=0)return;
  const item=this.acquire(key,pulse,alpha);if(!item)return;
  const xs=points.map(p=>p.x),zs=points.map(p=>p.z),minX=Math.min(...xs),maxX=Math.max(...xs),minZ=Math.min(...zs),maxZ=Math.max(...zs),center={x:(minX+maxX)/2,z:(minZ+maxZ)/2},pad=.9+.035*rank,width=Math.max(2.2,maxX-minX+pad*2),depth=Math.max(2.2,maxZ-minZ+pad*2);
  const stamp=`${key}:${pulse}:${rank}:${points.length}:${center.x.toFixed(3)}:${center.z.toFixed(3)}:${width.toFixed(3)}:${depth.toFixed(3)}`;
  if(item.stamp!==stamp){const result=this.geometry(center,width,depth,rank,points,hash(key)%100003);this.upload(item,result.data);item.stamp=stamp;item.paths=result.paths;item.vertices=result.data.positions.length/3;}
  item.key=key;item.touched=true;item.width=width;item.depth=depth;item.pulse=pulse;item.alpha=alpha;item.root.setWorldPosition(this.at(center,0));this.color.a=Math.round(Math.max(0,Math.min(255,alpha))*.82);item.material.setProperty('mainColor',this.color);item.root.active=true;
 }
 /** Hand-only batches can follow a late-sampled socket without rebuilding
  * their local mesh. Called before drawing, after native pose/socket updates. */
 followHand(key:string,hand:Vec3){
  const beams=this.beamBatches.get(key),item=this.items.find(i=>i.key==='beam:'+key&&i.root.active);
  if(!item||!beams?.length)return;
  const last=beams[0].points[beams[0].points.length-1],delta=hand.clone().subtract(last);
  if(delta.lengthSqr()<1e-10)return;
  item.root.setWorldPosition(item.root.worldPosition.clone().add(delta));
  for(const beam of beams)for(const point of beam.points)point.add(delta);
 }
 end(){this.flushBeams();for(const item of this.items)if(!item.touched)item.root.active=false;}
 clear(){this.renderedBeams.length=0;this.beamBatches.clear();for(const item of this.items){item.root.active=false;item.touched=false;item.key='';}}
 inspectBeams(){const triple=(p:Vec3)=>[p.x,p.y,p.z];return this.renderedBeams.map(beam=>({role:beam.role,width:beam.width,alpha:beam.alpha,textureBand:beam.role==='launch'||beam.role==='chain'||beam.role==='accent'?0:1,renderFrom:triple(beam.points[0]),renderTo:triple(beam.points[beam.points.length-1]),renderMid:triple(beam.points[Math.floor(beam.points.length/2)]),renderPath:beam.points.map(triple)}));}
 inspect(){return{capacity:LIMIT,allocated:this.items.length,active:this.items.filter(item=>item.root.active).map(item=>({key:item.key,pulse:item.pulse,width:item.width,depth:item.depth,freeDischarges:item.paths,vertices:item.vertices,alpha:item.alpha}))};}
 destroy(){if(this.disposed)return;this.disposed=true;this.clear();for(const item of this.items){item.mesh?.destroy();item.material.destroy();}this.items.length=0;this.root.destroy();}
}
