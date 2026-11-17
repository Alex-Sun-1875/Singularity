 private readonly beamBatches=new Map<string,{points:readonly Vec3[];width:number;alpha:number}[]>();
 camera?:Camera;

 private acquire(key:string,pulse:number,alpha:number):Field|undefined {
  const beam=key.startsWith('beam:');
  let item=this.items.find(item=>item.key===key);
  if(!item)item=this.items.find(item=>!item.touched&&!item.root.active&&item.key.startsWith('beam:')===beam);
  if(!item&&this.items.length>=LIMIT){item=this.items.find(item=>!item.touched&&item.key.startsWith('beam:')===beam);if(!item)return;}
  if(!item){
   const root=new Node('ThunderArcSheet');root.layer=this.root.layer;root.active=false;this.root.addChild(root);
   const material=new Material();material.name='ProjectProcedural:ThunderArcSheet';
   material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_VERTEX_COLOR:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:beam?gfx.BlendFactor.ONE:gfx.BlendFactor.SRC_ALPHA,blendDst:beam?gfx.BlendFactor.ONE_MINUS_SRC_COLOR:gfx.BlendFactor.ONE,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
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
  const crossSection=[-1,-.52,-.25,-.10,0,.10,.25,.52,1];
  for(const [key,beams]of this.beamBatches){
   const item=this.acquire('beam:'+key,0,255);
   if(!item)continue;
   const origin=new Vec3();let count=0;
   for(const beam of beams)for(const p of beam.points){origin.add(p);count++;}
   origin.multiplyScalar(1/count);
   const positions:number[]=[],colors:number[]=[],indices:number[]=[];
   const minPos=new Vec3(Infinity,Infinity,Infinity),maxPos=new Vec3(-Infinity,-Infinity,-Infinity);
   let radius=0;
   for(const beam of beams){
    const first=positions.length/3;
    for(let i=0;i<beam.points.length;i++){
     const point=beam.points[i],before=beam.points[Math.max(0,i-1)],after=beam.points[Math.min(beam.points.length-1,i+1)];
     const tangent=after.clone().subtract(before).normalize();
     const side=Vec3.cross(new Vec3(),tangent,view);
     if(side.lengthSqr()<.00001)Vec3.cross(side,tangent,Vec3.UNIT_Y);
     side.normalize();
     const t=i/(beam.points.length-1),tip=Math.min(1,(t+.045)*9,(1.045-t)*9);
     const irregular=.88+.12*Math.sin(i*1.79+beam.points[0].x*3.1);
     const halfWidth=beam.width*.5*tip*irregular;
     for(const band of crossSection){
      const edge=Math.abs(band),core=edge<=.10;
      const p=point.clone().add(side.clone().multiplyScalar(band*halfWidth)).subtract(origin);
      positions.push(p.x,p.y,p.z);
      const opacity=(edge>=1?0:core?1:edge<=.25?.80:.32)*beam.alpha/255;
      // Premultiplied screen light preserves the blue corona over bright terrain.
      colors.push((core?1:edge<=.25?.59:.27)*opacity,(core?1:edge<=.25?.76:.35)*opacity,opacity,opacity);
      minPos.x=Math.min(minPos.x,p.x);minPos.y=Math.min(minPos.y,p.y);minPos.z=Math.min(minPos.z,p.z);
      maxPos.x=Math.max(maxPos.x,p.x);maxPos.y=Math.max(maxPos.y,p.y);maxPos.z=Math.max(maxPos.z,p.z);radius=Math.max(radius,p.length());
     }
    }
    for(let i=0;i<beam.points.length-1;i++)for(let j=0;j<crossSection.length-1;j++){
     const a=first+i*crossSection.length+j,b=a+1,c=a+crossSection.length;
     indices.push(a,c,b,b,c,c+1);
    }
   }
   this.upload(item,{positions,colors,indices,minPos,maxPos,boundingRadius:radius});
   item.key='beam:'+key;item.touched=true;item.stamp='';item.paths=beams.length;item.vertices=positions.length/3;
   item.root.setWorldPosition(origin);this.color.set(255,255,255,255);item.material.setProperty('mainColor',this.color);
   item.root.active=true;
  }
 }
