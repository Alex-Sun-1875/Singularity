// Apply bounded edits to the current renderer modules in a disposable review response.
const fs=require('node:fs');
const path=require('node:path');

function change(source,before,after){
  if(source.split(before).length!==2)throw Error('Current implementation changed near '+before.slice(0,90));
  return source.replace(before,()=>after);
}
function section(source,from,until,replacement){
  const begin=source.indexOf(from),end=source.indexOf(until,begin+from.length);
  if(begin<0||end<0)throw Error('Missing current implementation section '+from);
  return source.slice(0,begin)+replacement+'\n'+source.slice(end);
}

function lightning(source){
  const edits=[
    ["${event.targetId??''}:${pulse}","${event.targetId??''}"],
    ['Math.ceil(length/.16),12,94','Math.ceil(length/.20),16,80'],
    ['const phase=Math.floor(time*28),motion=time*28-phase,','const phase=Math.floor(time*18),motion=time*18-phase,'],
    ['tremble=noise(seed+phase)*.055','tremble=noise(seed+phase)*.030'],
    ['noise(seed+phase+1)*.055','noise(seed+phase+1)*.030'],
    ['field(seed+172,t*length*3.6)*.095+noise(seed+i*43+7)*.038','field(seed+172,t*length*2.2)*.075+noise(seed+i*43+7)*.022'],
    ['field(seed,t*length*1.1)*spread','(field(seed,t*length*.72)*.72+field(seed+11,t*length*2.0)*.28)*spread'],
    ['(network?.064:.082)+rank*.0034','(network?.126:.172)+rank*.0046'],
    ['.024+rank*.0018','.036+rank*.0026'],
    ['.43+rank*.025,brightness*.62','.47+rank*.025,brightness*.53'],
    ['const filaments=network?1:2','const filaments=0'],
    ['const forks=network?(length>3.3&&rank>=3?2:1):Math.min(4,2+Math.floor(rank/2))','const forks=network?(length>1.5?1:0):2'],
    ['rays=6+Math.floor(rank/2)','rays=3'],
    ['.014+rank*.001','.023+rank*.0018'],
    ['.012+rank*.0007','.021+rank*.0014'],
  ];
  for(const [before,after]of edits)source=change(source,before,after);
  source=section(source,' host.line(points,BLUE,',' // A long launch is a bundle',[
    ' if(host.thunderBeam){',
    "  host.thunderBeam(event.castId+':'+event.segment,points,(network?.32:.40)+rank*.012,brightness);",
    ' }else{',
    "  host.line(points,'#b8ceff',(network?.126:.172)+rank*.0046,Math.round(brightness*.72),true,'glow');",
    "  host.line(points,CORE,.078+rank*.003,Math.round(brightness*.96),true,'core');",
    ' }'
  ].join('\n'));
  source=change(source,"  detail(host,branch,CORE,.021+rank*.0014,brightness*(network?.65:.82),'core');\n  detail(host,branch,HALO,.12,brightness*.30,'glow');",[
    "  if(host.thunderBeam)host.thunderBeam(event.castId+':'+event.segment,branch,network?.13:.17,brightness*.72);",
    "  else detail(host,branch,CORE,.021+rank*.0014,brightness*(network?.65:.82),'core');"
  ].join('\n'));
  return source;
}

function skillVfx(source){
  source=change(source,'export interface SkillVfxHost {','export interface SkillVfxHost {\n thunderBeam?(key:string,points:readonly Vec3[],width:number,alpha:number):void;');
  source=section(source,'   let pulse=-1,alpha=0;','   if(pulse>=0&&alpha>0){',[
    '   let pulse=-1,alpha=0;',
    '   if(age>=0&&age<.46){',
    '    pulse=age<.18?0:age<.40?1:2;',
    '    const attack=Math.min(1,(age+.008)/.020);',
    '    const fade=Math.min(1,(.46-age)/.16);',
    '    alpha=Math.round(250*attack*fade*(.93+.07*Math.sin(age*39)));',
    '   }',
  ].join('\n'));
  source=change(source,"if(pattern.skillId!=='THU_01'&&pattern.ground.size)","if(pattern.skillId==='THU_05'&&pattern.ground.size)");
  source=change(source,'map(hit=>hit.p),pattern.rank,alpha,pulse);','map(hit=>hit.p),pattern.rank,Math.round(alpha*.22),pulse);');
  source=change(source,"if(network&&pulse>0&&e.phase!=='network')continue;","if(network&&age>.34&&e.phase!=='network')continue;");
  source=change(source,'if(network&&pulse>0&&(distance(visual.from',"if(network&&pulse>0&&e.phase==='network'&&(distance(visual.from");
  // The same emitter follows the real projectile, with less disconnected tail debris.
  source=change(source,"'fireRoll',p,height,.48+.025*r","'fireRoll',p,height,.28+.020*r");
  return source;
}

function playerEffects(source){
  source=change(source,'const host={meteor:','const host={thunderBeam:(key:string,points:readonly Vec3[],width:number,alpha:number)=>this.thunderField.addBeam(key,points,width,alpha),meteor:');
  source=change(source,"family==='FIR'?.24:charged?.85:.47,color","family==='FIR'?.24:family==='THU'?.21:charged?.85:.47,color");
  return change(source,"family==='WAR'?.25:.32,color","family==='WAR'?.25:family==='THU'?.20:.32,color");
}

function beamField(source){
  source=change(source,'import {Color,','import {Camera,Color,');
  source=change(source,' begin(){for(const item of this.items)item.touched=false;}',' begin(){this.beamBatches.clear();for(const item of this.items)item.touched=false;}');
  const drawStart=source.indexOf(' draw(key:string,points:readonly Point[]');
  const allocationStart=source.indexOf('  let item=this.items.find',drawStart);
  const allocationEnd=source.indexOf('  const xs=points.map',allocationStart);
  if(allocationStart<0||allocationEnd<0)throw Error('Current ThunderArcField allocation changed');
  source=source.slice(0,allocationStart)+'  const item=this.acquire(key,pulse,alpha);if(!item)return;\n'+source.slice(allocationEnd);
  const methods=fs.readFileSync(path.join(__dirname,'beam-batches.ts'),'utf8');
  source=change(source,' private upload(item:Field,data:Geometry){',methods+'\n private upload(item:Field,data:Geometry){');
  source=change(source,' clear(){for(const item of this.items)',' clear(){this.beamBatches.clear();for(const item of this.items)');
  return change(source,' end(){for(const item of this.items)',' end(){this.flushBeams();for(const item of this.items)');
}

function fireSprites(source){
  source=change(source,'x=foot.x-radius*tx*.12,z=foot.z-radius*tz*.12','x=foot.x-radius*tx*.22,z=foot.z-radius*tz*.22');
  source=change(source,'(rx*side*.35+tx*.28),z=foot.z+radius*spread*(rz*side*.35+tz*.28)','(rx*side*.24+tx*.38),z=foot.z+radius*spread*(rz*side*.24+tz*.38)');
  source=change(source,'radius*.85*spread,rx,rz','radius*1.02*spread,rx,rz');
  source=change(source,'if(radius<.8||t<.12||this.reducedMotion)','if(radius<.8||t<.08||this.reducedMotion)');
  source=change(source,'alpha*.68*fade*smooth((t-.12)/.10)','alpha*.72*fade*smooth((t-.08)/.14)');
  source=change(source,'width*(comet?.375:.52)','width*(comet?.375:1.0)');
  source=change(source,'size*1.75,frame,alpha','size*1.35,frame,alpha');
  source=change(source,'size*.24,frame,alpha','size*.19,frame,alpha');
  source=change(source,'Math.min(2.1,width/cols*1.70,sideLimit,depthLimit)','Math.min(2.6,width/cols*2.0,sideLimit,depthLimit)');
  source=change(source,'time*5+col*.71+row*1.3','time*5+col*.37+row*.72');
  source=change(source,'(row===0?1:.90)','(row===0?1:.96)');
  return source;
}

function bladeSurface(source){
  source=change(source,'bodySpan=span*.64','bodySpan=span*.54');
  return change(source,'Math.max(width*4.7,radius*.21)','Math.max(width*5.5,radius*.54)');
}

exports.replaceModules=function replaceModules(bundle,cocos){
  const ts=require(path.join(cocos,'node_modules/typescript'));
  const root=path.join(cocos,'assets/scripts/features');
  const edits=[
    ['combat/runtime/SkillEnergyStrokes',lightning],
    ['combat/runtime/NativeSkillVfx',skillVfx],
    ['combat/runtime/Effects',playerEffects],
    ['combat/runtime/SkillFireSprites',fireSprites],
    ['actors/runtime/MeleeBladeSurfaces',bladeSurface],
    ['combat/runtime/ThunderArcField',beamField],
  ];
  const registrations=[];
  for(const [relative,edit]of edits){
    const filename=path.join(root,relative+'.ts');
    const source=fs.readFileSync(filename,'utf8').replace(/\r\n/g,'\n');
    const authored=edit(source);
    const compiled=ts.transpileModule(authored,{compilerOptions:{module:ts.ModuleKind.System,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
    if(compiled.diagnostics?.length)throw Error(ts.flattenDiagnosticMessageText(compiled.diagnostics[0].messageText,'\n'));
    const name='chunks:///_virtual/'+path.basename(relative)+'.ts';
    const registration=compiled.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,imports)=>{
      const dependencies=JSON.parse(imports).map(imported=>imported==='cc'?'cc':'./'+imported.split('/').pop()+'.ts');
      return 'System.register('+JSON.stringify(name)+','+JSON.stringify(dependencies);
    });
    if(!registration.includes('System.register('+JSON.stringify(name)))throw Error('No replacement registration '+name);
    bundle=change(bundle,'System.register('+JSON.stringify(name)+',','System.register('+JSON.stringify(name+'.original')+',');
    registrations.push(registration);
  }
  return bundle+'\n'+registrations.join('\n');
};
