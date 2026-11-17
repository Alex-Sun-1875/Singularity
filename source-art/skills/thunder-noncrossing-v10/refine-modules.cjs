// Apply bounded edits to the current renderer modules in a disposable review response.
const fs=require('node:fs');
const path=require('node:path');
const reference=JSON.parse(fs.readFileSync(path.join(__dirname,'reference-profile.json'),'utf8'));

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
  source=change(source,'const HEIGHT=1.05;',[
    'const REFERENCE_SPINE='+JSON.stringify(reference.spine)+' as const;',
    'const REFERENCE_BRANCHES='+JSON.stringify(reference.branches)+' as const;',
    'function referenceSide(t:number){const f=Math.max(0,Math.min(1,t))*(REFERENCE_SPINE.length-1),i=Math.floor(f),j=Math.min(REFERENCE_SPINE.length-1,i+1);return REFERENCE_SPINE[i][1]+(REFERENCE_SPINE[j][1]-REFERENCE_SPINE[i][1])*(f-i);}',
    'const HEIGHT=1.05;'
  ].join('\n'));
  const edits=[
    ["${event.targetId??''}:${pulse}","${event.targetId??''}"],
    ['Math.ceil(length/.16),12,94','Math.ceil(length/.11),16,88'],
    ['const phase=Math.floor(time*28),motion=time*28-phase,','const phase=Math.floor(time*18),motion=time*18-phase,'],
    ['tremble=noise(seed+phase)*.055','tremble=noise(seed+phase)*.045'],
    ['noise(seed+phase+1)*.055','noise(seed+phase+1)*.045'],
    ['spread=clamp(.11+length*.032,.18,.48)','spread=clamp(.18+length*.06,.30,.65)'],
    ['field(seed+172,t*length*3.6)*.095+noise(seed+i*43+7)*.038','field(seed+172,t*length*3.6+time*.85)*.10+noise(seed+i*43+7)*.045'],
    ['field(seed,t*length*1.1)*spread','(field(seed,t*length*1.25)*.80+field(seed+11,t*length*2.6)*.20)*spread'],
    ['(network?.064:.082)+rank*.0034','(network?.126:.172)+rank*.0046'],
    ['.024+rank*.0018','.036+rank*.0026'],
    ['.43+rank*.025,brightness*.62','.47+rank*.025,brightness*.53'],
    ['const forks=network?(length>3.3&&rank>=3?2:1):Math.min(4,2+Math.floor(rank/2))','const forks=network?(length>1.8?1:0):1'],
    ['reach=Math.min(network?.26+rank*.042:.42+rank*.07,length*.24)','reach=Math.min(network?.52+rank*.05:.84+rank*.07,length*.31)'],
    ['for(let j=1;j<=6;j++){','for(let j=1;j<=11;j++){'],
    ['const t=j/6,jitter=noise(seed+i*101+j*17)*.065','const t=j/11,jitter=noise(seed+i*101+j*17)*.09'],
    ['rays=6+Math.floor(rank/2)','rays=6'],
    ['.014+rank*.001','.023+rank*.0018'],
    ['.012+rank*.0007','.021+rank*.0014'],
  ];
  for(const [before,after]of edits)source=change(source,before,after);
  source=section(source,'  const side=envelope*(','  const p=bound(',[
    '  const side=!network&&length>3?-referenceSide(t)*length+envelope*(field(seed+172,t*length*3.6+time*.85)*.025+tremble*.18):',
    '   envelope*((field(seed,t*length*1.25)*.80+field(seed+11,t*length*2.6)*.20)*spread+field(seed+172,t*length*3.6+time*.85)*.07+noise(seed+i*43+7)*.025+tremble*.3);'
  ].join('\n'));
  source=change(source,'noise(seed+i*11)*.095*envelope','noise(seed+i*11)*.035*envelope');
  source=section(source,' host.line(points,BLUE,',' // A long launch is a bundle',[
    ' if(host.thunderBeam){',
    "  host.thunderBeam(event.castId+':'+event.segment,points,(network?.29:.50)+rank*.010,brightness,network?'chain':'launch');",
    ' }else{',
    "  host.line(points,'#b8ceff',(network?.126:.172)+rank*.0046,Math.round(brightness*.72),true,'glow');",
    "  host.line(points,CORE,.078+rank*.003,Math.round(brightness*.96),true,'core');",
    ' }'
  ].join('\n'));
  source=section(source,' // A long launch is a bundle',' const forks=',[
    ' // Reuse the current filament paths with asymmetric split/rejoin lengths.',
    ' const filaments=0;',
    ' for(let strand=0;strand<filaments;strand++){',
    '  const begin=strand===0?0:Math.floor(count*.23),end=strand===0?count:Math.floor(count*.77);',
    '  const sign=strand%2?-1:1,path=points.slice(begin,end+1).map((p,j)=>{',
    '   const i=begin+j,t=j/(end-begin),envelope=Math.pow(Math.max(0,Math.sin(Math.PI*t)),.5);',
    '   const chord=mix(from,to,i/count),drift=(chord.x-worldPoints[i].x)*perpendicular.x+(chord.z-worldPoints[i].z)*perpendicular.z;',
    '   const offset=envelope*(drift*.6+sign*(network?.17:.30+strand*.08)*(.35+Math.abs(field(seed+331+strand*17,i/count*length*1.7))*.95)+field(seed+521+strand*29,i/count*length*3.3)*.05);',
    '   return p.clone().add(host.at(bound({x:worldPoints[i].x+perpendicular.x*offset,z:worldPoints[i].z+perpendicular.z*offset}),HEIGHT).subtract(host.at(worldPoints[i],HEIGHT)));',
    '  });',
    "  if(host.thunderBeam)host.thunderBeam(event.castId+':'+event.segment,path,network?.16:.21,brightness*(network?.58:.72),network?'chainDetail':'launchDetail');",
    "  else detail(host,path,CORE,.013+rank*.001,brightness*.72,'core');",
    ' }',
    ' if(!network&&length>3)for(const profile of REFERENCE_BRANCHES){',
    '  const path=profile.map(([t,s])=>{',
    '   const base=mix(from,to,t),p=bound({x:base.x-perpendicular.x*s*length,z:base.z-perpendicular.z*s*length});',
    '   const q=host.at(p,HEIGHT);if(sourceOffset)q.add(sourceOffset.clone().multiplyScalar(1-t));return q;',
    '  });',
    "  host.thunderBeam?.(event.castId+':'+event.segment,path,.16,brightness*.70,'launchDetail');",
    ' }',
  ].join('\n'));
  source=change(source,"  detail(host,branch,CORE,.021+rank*.0014,brightness*(network?.65:.82),'core');\n  detail(host,branch,HALO,.12,brightness*.30,'glow');",[
    "  if(host.thunderBeam)host.thunderBeam(event.castId+':'+event.segment,branch,network?.20:.25,brightness*.76,network?'chainDetail':'launchDetail');",
    "  else detail(host,branch,CORE,.021+rank*.0014,brightness*(network?.65:.82),'core');"
  ].join('\n'));
  return source;
}

function skillVfx(source){
  source=change(source,'export interface SkillVfxHost {',"export interface SkillVfxHost {\n thunderBeam?(key:string,points:readonly Vec3[],width:number,alpha:number,role?:'launch'|'chain'|'launchDetail'|'chainDetail'):void;");
  source=section(source,'   let pulse=-1,alpha=0;','   if(pulse>=0&&alpha>0){',[
    '   let pulse=-1,alpha=0;',
    '   if(age>=0&&age<.46){',
    '    pulse=age<.18?0:age<.40?1:2;',
    '    const attack=Math.min(1,(age+.008)/.020);',
    '    const fade=Math.min(1,(.46-age)/.16);',
    '    alpha=Math.round(250*attack*fade*(.93+.07*Math.sin(age*39)));',
    '   }',
  ].join('\n'));
  source=change(source,'map(hit=>hit.p),pattern.rank,alpha,pulse);','map(hit=>hit.p),pattern.rank,Math.round(alpha*.44),pulse);');
  // Free, unrelated discharges look like extra links in a dense group. Keep
  // contacts and the approved path texture, with one authoritative chain.
  source=change(source,"if(pattern.skillId!=='THU_01'&&pattern.ground.size)this.host.thunderField?", "if(pattern.skillId!=='THU_01'&&!['THU_02','THU_05'].includes(pattern.skillId)&&pattern.ground.size)this.host.thunderField?");
  source=change(source,"if(network&&pulse>0&&e.phase!=='network')continue;","if(network&&age>.34&&e.phase!=='network')continue;");
  source=change(source,"const e=edge.event;if(network&&age>.34&&e.phase!=='network')continue;","let e=edge.event;if(network&&age>.34&&e.phase!=='network')continue;");
  source=change(source,"     if(cast&&distance(e.from,cast.from)<.01)edge.sourceAnchor=this.host.playerHand?.()?.clone();",[
    "     const firstEntry=Array.from(pattern.edges.values()).find(candidate=>candidate.event.phase==='connection');",
    "     if(cast&&pattern.skillId==='THU_05'&&edge===firstEntry&&e.to&&this.host.visible?.(cast.from,e.to)!==false){",
    "      e=edge.event={...e,from:{...cast.from}};",
    "     }",
    "     if(cast&&distance(e.from,cast.from)<.01)edge.sourceAnchor=this.host.playerHand?.()?.clone();"
  ].join('\n'));
  source=change(source,'if(network&&pulse>0&&(distance(visual.from',"if(network&&pulse>0&&e.phase==='network'&&(distance(visual.from");
  source=change(source,'     const visual=network&&pulse>0?',"     if(edge.sourceAnchor&&e.phase!=='network')edge.sourceAnchor=this.host.playerHand?.()?.clone()??edge.sourceAnchor;\n     const visual=network&&pulse>0?");
  // The same emitter follows the real projectile, with less disconnected tail debris.
  source=change(source,"'fireRoll',p,height,.48+.025*r","'fireRoll',p,height,.28+.020*r");
  return source;
}

function playerEffects(source){
  source=change(source,'const host={meteor:',"const host={thunderBeam:(key:string,points:readonly Vec3[],width:number,alpha:number,role?:'launch'|'chain'|'launchDetail'|'chainDetail')=>this.thunderField.addBeam(key,points,width,alpha,role),meteor:");
  source=change(source,"family==='FIR'?.24:charged?.85:.47,color","family==='FIR'?.24:family==='THU'?.21:charged?.85:.47,color");
  return change(source,"family==='WAR'?.25:.32,color","family==='WAR'?.25:family==='THU'?.20:.32,color");
}

function beamField(source){
  source=change(source,'import {Color,','import {assetManager,ImageAsset,Texture2D,Camera,Color,');
  source=change(source,'type Geometry={','const REFERENCE_WIDTHS='+JSON.stringify(reference.widths)+' as const;\ntype Geometry={');
  source=change(source,'colors:number[];indices:number[];','colors:number[];uvs?:number[];indices:number[];');
  source=change(source,'colors?:Float32Array;indices?:','colors?:Float32Array;uvs?:Float32Array;indices?:');
  source=change(source,'  item.positions!.set(data.positions);item.colors!.set(data.colors);item.indices!.set(data.indices);',[
    '  item.positions!.set(data.positions);item.colors!.set(data.colors);item.indices!.set(data.indices);',
    '  if(data.uvs){if(!item.uvs||item.uvs.length<item.positions!.length/3*2)item.uvs=new Float32Array(item.positions!.length/3*2);item.uvs.set(data.uvs);}'
  ].join('\n'));
  source=change(source,'const geometry={positions:item.positions!','const geometry={uvs:data.uvs?item.uvs!.subarray(0,data.uvs.length):undefined,positions:item.positions!');
  // A pooled inactive MeshRenderer keeps its old model on enable. Rebind a
  // grown mesh while enabled so the model cannot retain destroyed buffers.
  source=change(source,"item.mesh.name='ThunderFreeDischarges';item.renderer.mesh=item.mesh;previous?.destroy();", "item.mesh.name='ThunderFreeDischarges';item.root.active=true;item.renderer.mesh=item.mesh;previous?.destroy();");
  source=change(source,' begin(){for(const item of this.items)item.touched=false;}',' begin(){this.reviewStats.length=0;this.beamBatches.clear();for(const item of this.items)item.touched=false;}');
  source=change(source,'const trunks=7+rank+Math.ceil(count*.8)','const trunks=4+Math.ceil(count*.8)');
  source=change(source,'height=.18+(i%3)*.32','height=.52+(i%3)*.28');
  source=change(source,'forks=2+(i%3===0?1:0)','forks=1+(i%3===0?1:0)');
  source=change(source,'hash(key)%100003+pulse*991','hash(key)%100003');
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
    ['combat/common/PureCombat',source=>section(source,' private lightningNetwork(',' private anchorsHit(',fs.readFileSync(path.join(__dirname,'nearest-chain.ts'),'utf8'))],
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
    const prefix='System.register('+JSON.stringify(name)+',';
    const start=bundle.indexOf(prefix)+prefix.length,end=bundle.indexOf(']',start)+1;
    if(start<prefix.length||end<=start)throw Error('Missing original dependency table '+name);
    const originalDependencies=JSON.parse(bundle.slice(start,end));
    const registration=compiled.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,imports)=>{
      const dependencies=JSON.parse(imports).map(imported=>{
        if(imported==='cc')return 'cc';
        const basename=imported.split('/').pop(),flat='./'+basename+'.ts';
        if(originalDependencies.includes(flat))return flat;
        const aliases=originalDependencies.filter(value=>new RegExp('^\\./'+basename+'[0-9]+\\.ts$').test(value));
        if(aliases.length!==1)throw Error('Cannot resolve original module dependency '+relative+': '+imported);
        return aliases[0];
      });
      return 'System.register('+JSON.stringify(name)+','+JSON.stringify(dependencies);
    });
    if(!registration.includes('System.register('+JSON.stringify(name)))throw Error('No replacement registration '+name);
    bundle=change(bundle,'System.register('+JSON.stringify(name)+',','System.register('+JSON.stringify(name+'.original')+',');
    registrations.push(registration);
  }
  return bundle+'\n'+registrations.join('\n');
};
