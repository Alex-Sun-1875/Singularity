// Disposable review response only. Does not write any Cocos production module.
const fs=require('node:fs');
const path=require('node:path');
function change(source,before,after){
  if(source.split(before).length!==2)throw Error('Current implementation changed near '+before.slice(0,100));
  return source.replace(before,()=>after);
}
function section(source,from,until,replacement){
  const begin=source.indexOf(from),end=source.indexOf(until,begin+from.length);
  if(begin<0||end<0)throw Error('Missing section '+from);
  return source.slice(0,begin)+replacement+'\n'+source.slice(end);
}
function nativeFire(source){
  source=change(source,'duration:number;sourceAnchor?:Vec3;kind:', 'duration:number;coolingAt?:number;sourceAnchor?:Vec3;kind:');
  source=change(source,'alpha:number,origin?:Point):void;', 'alpha:number,origin?:Point,cooling?:number):void;');
  source=change(source,"if(e.type==='skill_end'){this.cues=this.cues.filter(c=>c.event.castId!==e.castId);if(e.phase==='triggered')this.add(e,'snare',.4);return true;}",[
    "if(e.type==='skill_end'){",
    " this.cues=this.cues.filter(c=>{",
    "  if(c.event.castId!==e.castId)return true;",
    "  if(c.kind==='blast'&&c.event.skillId.startsWith('FIR'))return true;",
    "  if((c.kind==='wall'||c.kind==='field')&&c.event.skillId.startsWith('FIR')){",
    "   if(c.coolingAt===undefined){c.coolingAt=this.now;c.duration=this.now-c.start+1.8;}return true;",
    "  }return false;",
    " });if(e.phase==='triggered')this.add(e,'snare',.4);return true;",
    "}"
  ].join('\n'));
  source=change(source,"this.add(e,'blast',e.skillId==='FIR_02'?.64:.34);","this.add(e,'blast',e.skillId==='FIR_02'?3.25:1.85);");
  source=change(source,'  this.cues=this.cues.filter(c=>this.now-c.start<c.duration);',[
    '  for(const c of this.cues){',
    "   if((c.kind==='wall'||c.kind==='field')&&c.event.skillId.startsWith('FIR')&&c.coolingAt===undefined&&this.now>=c.start+c.duration){",
    '    c.coolingAt=c.start+c.duration;c.duration+=1.8;',
    '   }',
    '  }',
    '  this.cues=this.cues.filter(c=>this.now-c.start<c.duration);'
  ].join('\n'));
  source=section(source,"   if(c.kind==='blast'){","   if(c.kind==='wall'||",[
    "   if(c.kind==='blast'){",
    "    const radius=skillVfxGeometry(e).radiusMetres??0,peak=e.skillId==='FIR_02'?.55:.30;",
    "    const progress=age<peak?.68*age/peak:.68+.32*Math.min(1,(age-peak)/(c.duration-peak));",
    "    this.host.fireVolume?.(`impact:${e.castId}:${e.segment}`,p,radius,rank,progress,.96*(e.skillId==='FIR_02'&&e.segment>0?.65:1));",
    "    continue;",
    "   }"
  ].join('\n'));
  source=change(source,"  const steps=Math.min(7,Math.max(3,Math.ceil(width/1.6))),front=wave?(progress*depth-depth/2):0;",[
    '  if(c.coolingAt!==undefined){',
    '   const cooling=Math.min(1,Math.max(0,(this.now-c.coolingAt)/1.8));',
    '   const fade=Math.pow(1-cooling,1.12);',
    '   this.host.fireRibbon?.(`cooling:${e.castId}`,p,width,depth,a,this.now,(field?.60:.86)*fade,p,cooling);return;',
    '  }',
    '  const steps=Math.min(7,Math.max(3,Math.ceil(width/1.6))),front=wave?(progress*depth-depth/2):0;'
  ].join('\n'));
  source=change(source,'const fade=Math.min(1,(1-progress)*6),opacity=(after?.74:.60)*fade;','const fade=field?1:Math.min(1,(1-progress)*6),opacity=(after?.74:.60)*fade;');
  source=change(source,'const opacity=(wave?.92:.86)*Math.min(1,(1-progress)*8);','const opacity=(wave?.92:.86)*(wave?Math.min(1,(1-progress)*8):1);');
  source=change(source,"this.host.meteor?.('meteor:'+e.castId,p,rank,t,this.now);","if(age>=.30)this.host.meteor?.('meteor:'+e.castId,p,rank,Math.max(0,(age-.30)/Math.max(.1,c.duration-.30)),this.now);");
  source=change(source,"'fireRoll',p,height,.48+.025*r","'fireRoll',p,height,.28+.020*r");
  return source;
}
function fireSprites(source){
  for(const [before,after] of [
    ['x=foot.x-radius*tx*.12,z=foot.z-radius*tz*.12','x=foot.x-radius*tx*.22,z=foot.z-radius*tz*.22'],
    ['(rx*side*.35+tx*.28),z=foot.z+radius*spread*(rz*side*.35+tz*.28)','(rx*side*.27+tx*.16),z=foot.z+radius*spread*(rz*side*.27+tz*.16)'],
    ['radius*.85*spread,rx,rz','radius*1.02*spread,rx,rz'],
    ['if(radius<.8||t<.12||this.reducedMotion)','if(radius<.8||t<.08||this.reducedMotion)'],
    ['alpha*.68*fade*smooth((t-.12)/.10)','alpha*.72*fade*smooth((t-.08)/.14)'],
    ['width*(comet?.375:.52)','width*(comet?.375:1.0)'],
    ['size*1.75,frame,alpha','size*1.35,frame,alpha'],
    ['size*.24,frame,alpha','size*.19,frame,alpha'],
    ['Math.min(2.1,width/cols*1.70,sideLimit,depthLimit)','Math.min(2.6,width/cols*2.0,sideLimit,depthLimit)'],
    ['origin:Point=foot){','origin:Point=foot,cooling=-1){'],
    ['const beat=(time*5+col*.71+row*1.3)%10,clock=4+(beat<5?beat:10-beat);','const beat=time*4+col*.37+row*.72,clock=cooling>=0?(depth<=1.5?8+7*clamp(cooling):10+5*clamp(cooling)):(depth<=1.5?5.5+1.2*Math.sin(beat):7.5+1.1*Math.sin(beat));'],
    ['alpha*(row===0?1:.90),(col+row)%2?1:2','alpha*(row===0?1:.96),depth<=1.5?0:(col+row)%2?1:2'],
  ])source=change(source,before,after);
  source=change(source,'  const base=this.groundHeight?.(foot),lift=base===undefined?0:foot.y-base;',[
    '  const base=this.groundHeight?.(foot),lift=base===undefined?0:foot.y-base;',
    '  if(t>=.60){',
    '   const settling=smooth((t-.60)/.13);',
    '   const patches=[[-.43,-.12,.70,.2],[.29,-.34,.72,0],[-.20,.40,.67,.7],[.48,.29,.59,.4],[.01,.03,.78,0]];',
    '   for(let i=0;i<patches.length;i++){',
    '    const [side,depth,scale,lag]=patches[i],x=foot.x+radius*(rx*side+tx*depth),z=foot.z+radius*(rz*side+tz*depth);',
    '    this.point.set(x,this.groundHeight?this.groundHeight({x,z})+lift:foot.y,z);',
    '    const width=this.visibleWidth(foot,{x,z},radius*scale,rx,rz,key+":residual:"+i);',
    '    this.phase(key+":residual:"+i,this.point,width,Math.max(10,clock-lag),alpha*fade*.88*settling);',
    '   }if(t>=.73)return;alpha*=1-settling;',
    '  }'
  ].join('\n'));
  return source;
}
function effects(source){
  return change(source,'alpha:number,origin?:Point)=>this.fireSprites.drawRibbon(key,this.at(p,.03),width,depth,angle,time,Math.round(alpha*255),origin)',
    'alpha:number,origin?:Point,cooling?:number)=>this.fireSprites.drawRibbon(key,this.at(p,.03),width,depth,angle,time,Math.round(alpha*255),origin,cooling)');
}
exports.replaceModules=function(bundle,cocos){
  const ts=require(path.join(cocos,'node_modules/typescript'));
  const registrations=[];
  for(const [name,edit] of [['NativeSkillVfx',nativeFire],['SkillFireSprites',fireSprites],['Effects',effects]]){
    const file=path.join(cocos,'assets/scripts/features/combat/runtime',name+'.ts');
    const source=edit(fs.readFileSync(file,'utf8').replace(/\r\n/g,'\n'));
    const compiled=ts.transpileModule(source,{compilerOptions:{module:ts.ModuleKind.System,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
    if(compiled.diagnostics?.length)throw Error(ts.flattenDiagnosticMessageText(compiled.diagnostics[0].messageText,'\n'));
    const virtual='chunks:///_virtual/'+name+'.ts';
    const registration=compiled.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,imports)=>'System.register('+JSON.stringify(virtual)+','+JSON.stringify(JSON.parse(imports).map(x=>x==='cc'?'cc':'./'+x.split('/').pop()+'.ts')));
    bundle=change(bundle,'System.register('+JSON.stringify(virtual)+',','System.register('+JSON.stringify(virtual+'.fire-v5-original')+',');
    registrations.push(registration);
  }
  return bundle+'\n'+registrations.join('\n');
};
