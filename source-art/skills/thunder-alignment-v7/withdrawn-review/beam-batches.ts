 private readonly beamBatches=new Map<string,{points:readonly Vec3[];width:number;alpha:number}[]>();
 private readonly beamMaterials=new WeakMap<Material,boolean>();
 private static referenceTexture?:Texture2D;
 private static referenceLoad?:Promise<void>;
 camera?:Camera;

 prepareReference():Promise<void>{
  if(!ThunderArcField.referenceLoad)ThunderArcField.referenceLoad=new Promise<void>((resolve,reject)=>{
   assetManager.loadRemote<ImageAsset>('/__review/approved-thunder-strip.png',{ext:'.png'},(error,image)=>{
    if(error){reject(error);return;}
    const texture=new Texture2D();texture.name='Approved2DThunderLight';texture.image=image;
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    ThunderArcField.referenceTexture=texture;resolve();
   });
  });
  return ThunderArcField.referenceLoad;
 }

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

 addBeam(key:string,points:readonly Vec3[],width:number,alpha:number):void {
  if(this.disposed||points.length<2||alpha<=0)return;
  let batch=this.beamBatches.get(key);
  if(!batch){batch=[];this.beamBatches.set(key,batch);}
  batch.push({points,width,alpha});
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
   // Preserve the source drawing's signed bend in the oblique 3D camera.
   // Solve the camera projection on XZ so the air arcs retain their real height.
   const launch=beams.find(beam=>beam.width>.32);
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
   const presented=align?beams.map(beam=>({...beam,points:beam.points.map(align!)})):beams;
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
     const irregular=beam.width>.25?Math.min(1.20,REFERENCE_WIDTHS[a]+(REFERENCE_WIDTHS[b]-REFERENCE_WIDTHS[a])*(address-a)):.70+.30*(.5+.5*Math.sin(i*.71+beam.points[0].x*3.1));
     const halfWidth=beam.width*.5*tip*irregular;
     for(const band of crossSection){
      const p=point.clone().add(side.clone().multiplyScalar(band*halfWidth)).subtract(origin);
      positions.push(p.x,p.y,p.z);
      const strength=beam.alpha/255;
      colors.push(strength,strength,strength,strength);
      uvs.push(t,(band+1)*.25+(beam.width>.32?0:.5));
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
