// Isolated v27 proposal: upright tapered hook silhouette, current native clips and air shader.
window.installUltimatePreview = function () {
  const {app,cc}=motionStudy,{Vec3,Quat,utils}=cc,pool=app.effects.warrior,native=pool.ultimateWave;
  const clamp=x=>Math.max(0,Math.min(1,x)),smooth=x=>{const q=clamp(x);return q*q*(3-2*q);};
  const study=window.ultimatePreview={enabled:false,phase:null};
  const actors=app.actors.player??app.actors,nativeContactPose=actors.contactPose;
  actors.contactPose=function(actor,time){if(study.enabled&&motionStudy.state.action?.skillId==='WAR_05'){this.heldPose=undefined;return;}return nativeContactPose.call(this,actor,time);};

  const bezier=(a,b,c,d,t)=>{const s=1-t;return a.map((v,i)=>s*s*s*v+3*s*s*t*b[i]+3*s*t*t*c[i]+t*t*t*d[i]);};
  const profile=(g,inner=false)=>{
    const tip=[4.80,3.90],outerHeel=[.04,.05],innerHeel=[.62,.35],hookTip=[.38,1.55];
    if(g<=.76){const t=g/.76;return inner?bezier(tip,[4.0,3.45],[1.2,1.20],innerHeel,t):bezier(tip,[3.6,2.90],[.70,.50],outerHeel,t);}
    const t=(g-.76)/.24;return inner?bezier(innerHeel,[.38,.75],[.40,1.33],hookTip,t):bezier(outerHeel,[-.08,.60],[.12,1.30],hookTip,t);
  };
  const headAt=age=>.045+.955*smooth(age/.16);
  function strokeMesh(age){
    const index=Math.round(clamp(age/.575)*35),key='proposal-upright-hook:'+index;
    let mesh=pool.meshes.get(key);if(mesh)return mesh;
    const sampled=index/35*.575,head=headAt(sampled),start=.19*smooth((sampled-.28)/.30);
    const positions=[],normals=[],uvs=[],colors=[],indices=[],nx=48,nv=10;
    for(let i=0;i<=nx;i++)for(let j=0;j<=nv;j++){
      const u=i/nx,v=j/nv,g=start+(head-start)*u;
      // One long tapered arm flows into a broad belly and a short returning hook.
      // Two separately authored cubic contours replace the circular moon outline.
      const outer=profile(g),inner=profile(g,true),soft=v*v;
      const height=outer[0]+(inner[0]-outer[0])*v+.045*Math.sin(g*27+v*8)*soft;
      const depth=outer[1]+(inner[1]-outer[1])*v+.040*Math.sin(g*31-v*6)*soft;
      positions.push(Math.max(.02,height),.045*Math.sin(g*18-v*5)*v,depth);
      const airDepth=v<.20?v*.60:v<.65?.12+(v-.20)*.12:.174+(v-.65)/.35*.826;
      normals.push(0,1,0);uvs.push(u,airDepth);colors.push(1,1,1,1);
    }
    for(let i=0;i<nx;i++)for(let j=0;j<nv;j++){const a=i*(nv+1)+j,b=a+nv+1;indices.push(a,b,a+1,b,b+1,a+1);}
    mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(0,-.10,0),maxPos:new Vec3(4.95,.10,4.05),boundingRadius:6.5});pool.meshes.set(key,mesh);return mesh;
  }
  function pressureFanMesh(){
    const key='proposal-irregular-ground-fan';let mesh=pool.meshes.get(key);if(mesh)return mesh;
    const positions=[],normals=[],uvs=[],indices=[],nx=32,nv=8;
    for(let i=0;i<=nx;i++)for(let j=0;j<=nv;j++){const u=i/nx,v=j/nv,taper=Math.pow(Math.max(0,Math.sin(Math.PI*u)),.65);positions.push((u-.5)*1.6,.02*Math.sin(u*15-v*6)*taper,((.16+.48*taper)*(1-v)+.065*Math.sin(u*23)*(1-v)*(1-v)));normals.push(0,1,0);uvs.push(u,v);}
    for(let i=0;i<nx;i++)for(let j=0;j<nv;j++){const a=i*(nv+1)+j,b=a+nv+1;indices.push(a,b,a+1,b,b+1,a+1);}
    mesh=utils.createMesh({positions,normals,uvs,indices,minPos:new Vec3(-.85,-.05,-.08),maxPos:new Vec3(.85,.05,.75),boundingRadius:1.2});pool.meshes.set(key,mesh);return mesh;
  }
  function drawStroke(key,position,forward,age,alpha,dissolve){
    if(age<=0||alpha<.02)return;
    const layer=pool.acquire(key,'pressure-flow');if(!layer)return;
    const mesh=strokeMesh(age);if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;
    const mat=pool.flowMaterial(layer,alpha,dissolve);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
    const up=Vec3.UNIT_Y,normal=Vec3.cross(new Vec3(),forward,up).normalize();
    layer.node.setWorldPosition(position);layer.node.setWorldRotation(Quat.fromAxes(new Quat(),up,normal,forward));layer.node.setWorldScale(1,1,1);layer.node.active=true;layer.touched=true;layer.phase='tapered-hook-downstroke';
  }
  pool.ultimateWave=function(key,center,angle,reach,alpha,t,stage){
    if(!study.enabled||stage<3)return native.call(this,key,center,angle,reach,alpha,t,stage);
    const age=t*.62,power=clamp(alpha/245),forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
    const travel=clamp(age/.32),growth=.82+.18*smooth(travel/.35),tip=reach*(.50+.48*smooth(travel/.62));
    const radius=reach*.61*growth,at=center.clone().add(forward.clone().multiplyScalar(tip-radius)).add(new Vec3(0,.38,0));
    const crossStrength=1-.28*smooth((age-.045)/.10);
    this.crescent(key+':ultimate-cross:horizontal',at,side,Vec3.UNIT_Y,forward,radius,power*smooth(age/.035)*crossStrength,2.85,.30,smooth((t-.38)/.62));
    const axis=this.crossingAxis(forward,side),normal=Vec3.cross(new Vec3(),forward,axis).normalize();
    this.crescent(key+':ultimate-cross:vertical',at,axis,normal,forward,radius,power*smooth((age-.020)/.045)*.96*crossStrength,2.85,.28,smooth((t-.46)/.54),.54);
    const player=motionStudy.state.player,floor=this.ground(player.x,player.z,center.y-1.02),dropAge=age-.045;
    // The heel belongs at the hero's feet; the long arm reaches forward and up.
    const position=new Vec3(player.x,floor,player.z);
    const dissolve=smooth((age-.27)/.35);
    drawStroke(key+':ultimate-downcut',position,forward,dropAge,power*1.10*smooth(dropAge/.035),dissolve);
    if(!this.reducedMotion){const tail=position.clone().subtract(forward.clone().multiplyScalar(.04)).add(new Vec3(0,.04,0));drawStroke(key+':ultimate-downcut-tail',tail,forward,dropAge-.035,power*.16*smooth((dropAge-.035)/.035),dissolve);}
    if(dropAge>0){const head=headAt(Math.round(clamp(dropAge/.575)*35)/35*.575),p=profile(head);study.phase={age,dropAge,progress:clamp(dropAge/.16),profileProgress:head,headHeight:p[0],headDepth:p[1],anchor:[position.x,position.y,position.z],playerFoot:[player.x,floor,player.z],longTip:[4.8,3.9],worldUp:[0,1,0],shape:'foot-anchored long tapered hook: long tip, broad curved belly, short return'};}
    const impactAge=dropAge-.108;
    if(impactAge>=0&&impactAge<.20){
      const contact=position.clone().add(forward.clone().multiplyScalar(.18));contact.y=floor+.07;
      // A feathered irregular fan gives the contact volume; no extra asterisk rays.
      const spread=smooth(impactAge/.20),layer=this.acquire(key+':ground-pressure','pressure-flow');
      if(layer){const mesh=pressureFanMesh();if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;const mat=this.flowMaterial(layer,.62*(1-spread),spread);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);contact.y=floor+.07;contact.add(forward.clone().multiplyScalar(spread*.30));layer.node.setWorldPosition(contact);layer.node.setWorldRotation(Quat.fromAxes(new Quat(),side,Vec3.UNIT_Y,forward));layer.node.setWorldScale(.78+.32*spread,1,1);layer.node.active=true;layer.touched=true;layer.phase='irregular-contact-fan';}
    }
  };
  for(let i=0;i<36;i++)strokeMesh(i/35*.575);pressureFanMesh();
};
