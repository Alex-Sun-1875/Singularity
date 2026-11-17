// Disposable-browser proposal only. Reuse current game meshes, shader and native actor clips.
window.installUltimatePreview = function () {
  const {app,cc}=motionStudy, pool=app.effects.warrior, native=pool.ultimateWave;
  const clamp=x=>Math.max(0,Math.min(1,x)), smooth=x=>{const q=clamp(x);return q*q*(3-2*q);};
  const study=window.ultimatePreview={enabled:false,phase:null};
  const actors=app.actors.player??app.actors, nativeContactPose=actors.contactPose;
  actors.contactPose=function(actor,time){
    if(study.enabled&&motionStudy.state.action?.skillId==='WAR_05'){this.heldPose=undefined;return;}
    return nativeContactPose.call(this,actor,time);
  };
  pool.ultimateWave=function(key,center,angle,reach,alpha,t,stage){
    if(!study.enabled||stage<3)return native.call(this,key,center,angle,reach,alpha,t,stage);
    const {Vec3}=cc, age=t*.62, power=clamp(alpha/245), forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
    const travel=clamp(age/.32),growth=.82+.18*smooth(travel/.35),tip=reach*(.50+.48*smooth(travel/.62));
    const radius=reach*.61*growth,at=center.clone().add(forward.clone().multiplyScalar(tip-radius)).add(new Vec3(0,.38,0));
    const crossStrength=1-.28*smooth((age-.045)/.10);
    this.crescent(key+':ultimate-cross:horizontal',at,side,Vec3.UNIT_Y,forward,radius,power*smooth(age/.035)*crossStrength,2.85,.30,smooth((t-.38)/.62));
    const axis=this.crossingAxis(forward,side),normal=Vec3.cross(new Vec3(),forward,axis).normalize();
    this.crescent(key+':ultimate-cross:vertical',at,axis,normal,forward,radius,power*smooth((age-.020)/.045)*.96*crossStrength,2.85,.28,smooth((t-.46)/.54),.54);
    const floor=this.ground(center.x,center.z,center.y-1.02),dropAge=age-.045;
    const drop=(elapsed,suffix,strength)=>{
      if(elapsed<=0)return;
      const q=clamp(elapsed/.17),p=smooth(q),r=reach*.51,leading=reach*.96;
      // World-up stays fixed: the entire upright crescent falls straight down.
      // No pitched forward axis, sideways roll, or horizontal travel in this stage.
      const f=forward.clone(),a=Vec3.UNIT_Y.clone(),n=Vec3.cross(new Vec3(),f,a).normalize();
      const leadingY=2.72-1.28*p,position=center.clone().add(forward.clone().multiplyScalar(leading-r));
      position.y=floor+leadingY;
      this.crescent(key+':'+suffix,position,a,n,f,r,power*strength*smooth(elapsed/.035),2.60,.32,smooth((age-.27)/.35),.60);
      if(suffix==='ultimate-downcut')study.phase={age,dropAge:elapsed,progress:q,crestHeight:leadingY,crestReach:leading,position:[position.x,position.y,position.z],worldUp:[a.x,a.y,a.z]};
    };
    drop(dropAge,'ultimate-downcut',.98);
    if(!this.reducedMotion)drop(dropAge-.040,'ultimate-downcut-tail',.13);
    const impactAge=dropAge-.13;
    if(impactAge>=0&&impactAge<.20){
      const contact=center.clone().add(forward.clone().multiplyScalar(reach*.94));contact.y=floor+.40;
      this.contact(key+':preview-drop-impact',contact,angle,2,impactAge/.20);
      const mist=contact.clone();mist.y=floor+.095;
      this.spinArc(key+':ultimate-low-wake',mist,angle,.58+.60*smooth(impactAge/.20),1.95,.20,.32*(1-smooth(impactAge/.20)),0,smooth(impactAge/.20));
    }
  };
  // Warm only existing mesh/material constructors in this disposable context.
  pool.spinMesh(2.60,.32);pool.spinMesh(1.95,.20);
};
