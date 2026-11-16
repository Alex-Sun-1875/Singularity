// Compile only the touched modules against the current working sources. Serve the
// replacement SystemJS registrations in memory; the exported game stays on disk.
const path=require('node:path');
const fs=require('node:fs');
const read=name=>fs.readFileSync(path.join(__dirname,name),'utf8');
function once(source,from,to){
  if(source.split(from).length!==2)throw Error('Upstream source changed near '+from.slice(0,80));
  return source.replace(from,()=>to);
}
function section(source,from,until,body){
  const start=source.indexOf(from),end=source.indexOf(until,start+from.length);
  if(start<0||end<0)throw Error('Upstream section missing: '+from);
  return source.slice(0,start)+body+'\n'+source.slice(end);
}
function melee(source){
  source=once(source,'export interface MeleeVfxHost {','export interface MeleeVfxHost {\n playerHand?():Vec3|undefined;\n slash?(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number):void;');
  source=section(source,'/** All blade vertices','/** Small local contact',read('forward-cut.ts'));
  source=once(source,'(.17+Math.min(2,strength)*.075)','(.29+Math.min(2,strength)*.135)');
  source=once(source,"const center=host.at(p,.68);","const center=host.at(p,.79);");
  source=once(source,"host.at(q,.68+Math.cos(i*2.1)*reach)","host.at(q,.79+Math.cos(i*2.1)*reach)");
  return once(source,"for(let i=0;i<(reduced?3:5);i++){","if(!reduced&&t<.38){\n  const lead=host.at(point(p,angle+.30,reach*.90),.84+reach*.62);\n  const trail=host.at(point(p,angle+Math.PI,reach*.55),.72-reach*.33);\n  host.line([trail,center,lead],'#c58941',.091,alpha,true,'ink');\n  host.line([trail,center,lead],'#ffe0a1',.037,alpha,true,'core');\n }\n for(let i=0;i<(reduced?3:5);i++){");
}
function energy(source){
  source=once(source,"import type {Vec3} from 'cc'","import {Vec3} from 'cc'");
  source=section(source,'export function drawArrowWake','/** One small physical',read('arrow-wake.ts'));
  const edits=[
    ['\u0024{event.targetId??\'\'}:\u0024{pulse}','\u0024{event.targetId??\'\'}'],
    ['Math.ceil(length/.16),12,94','Math.ceil(length/.64),4,25'],
    ['.11+length*.032,.18,.48','.16+length*.044,.22,.48'],
    ['field(seed,t*length*1.1)*spread','(field(seed,t*length*1.1)*.62+(i%2?1:-1)*(.65+.28*noise(seed+i*19)))*spread'],
    ['noise(seed+i*11)*.095*envelope','((i%3===1?.16:-.06)+noise(seed+i*11)*.16)*envelope'],
    ['field(seed+172,t*length*3.6)*.095+noise(seed+i*43+7)*.038','field(seed+172,t*length*1.9)*.060+noise(seed+i*43+7)*.024'],
    ['(network?.064:.082)+rank*.0034','(network?.14:.195)+rank*.0042'],
    ['.024+rank*.0018','.048+rank*.0032'],
    ['.43+rank*.025,brightness*.62','.46+rank*.018,brightness*.51'],
    ['const filaments=network?1:2','const filaments=0'],
    ['const forks=network?(length>3.3&&rank>=3?2:1):Math.min(4,2+Math.floor(rank/2))','const forks=length>4.0?1:0'],
    ['rays=6+Math.floor(rank/2)','rays=4'],
  ];
  for(const [a,b]of edits)source=once(source,a,b);
  return source;
}
function skills(source){
  source=once(source,"|'snare'|'storm'}","|'snare'|'storm'|'rangeSigil'}");
  source=once(source,'export class NativeSkillVfx {',read('cast-seal.ts')+'\nexport class NativeSkillVfx {');
  const castGate="if(e.type==='skill_cast'){";
  source=once(source,castGate,castGate+"\n   if(['WAR_04','BOW_06','FIR_02','THU_02','THU_05'].includes(id))this.add(e,'rangeSigil',e.duration??.25);");
  source=once(source,"if(c.kind==='drop'){","if(c.kind==='rangeSigil'){\n    if(game.state.action?.id===e.castId)castSeal(this.host,e,t);\n    continue;\n   }\n   if(c.kind==='drop'){");
  source=once(source,"this.host.meteor?.('meteor:'+e.castId,p,rank,t,this.now);","if(t>=.36)this.host.meteor?.('meteor:'+e.castId,p,rank,(t-.36)/.64,this.now);");
  source=once(source,"meta.skillId==='BOW_02'?1.15:.72","meta.skillId==='BOW_02'?2.25:2.05");
  const crossStart='const tip=mix(start,end,Math.min(1,t*8));';
  source=section(source,crossStart,'    }continue;',[
    'const back=degrees!==directions[0],beat=(t-(back?.24:0))/(back?.76:1);',
    '     if(beat<0)continue;',
    '     const tip=mix(start,end,Math.min(1,beat*4.8)), heel=this.host.at(start,back?1.44:.58), toe=this.host.at(tip,back?.60:1.34);',
    "     this.host.line([heel,toe],'#c18a51',.18,Math.round(alpha*.5),true,'ink');",
    "     this.host.slash?.('cross:'+e.castId+':'+degrees,heel,toe,Math.min(g.widthMetres??.42,.40+.03*rank),alpha,beat);",
    "     this.host.line([heel,toe],'#f8d492',.038,alpha,true,'core');",
    '     this.scratch(tip,angle,1,GOLD,alpha,.58);'
  ].join('\n'));
  const impact='if(this.host.fireVolume)this.host.fireVolume(`impact:';
  source=once(source,impact,"if(e.skillId==='FIR_02'&&e.segment===0&&t<.62){\n     const bloom=Math.sin(Math.PI*Math.min(1,(t+.04)/.66));\n     this.host.firePlume?.('meteor-crown:'+e.castId,p,.04,radius*.90,t*1.8,Math.round(211*bloom));\n     const reach=radius*(.18+.80*(1-Math.pow(1-Math.min(1,t/.45),2)));\n     for(let k=0;k<5;k++){const rim:Vec3[]=[];for(let j=0;j<=9;j++){const a=TAU*(k/5+j/9*.115)+.27;rim.push(this.host.at({x:p.x+Math.cos(a)*reach,z:p.z+Math.sin(a)*reach},.07));}\n       this.host.line(rim,'#db6b28',.091,Math.round(200*bloom),true,'ink');this.host.line(rim,'#ffb052',.041,Math.round(165*bloom),true,'core');}\n    }\n    "+impact);
  source=once(source,"this.host.fireProjectile?.('flame:'+p.id,p,height,a,1.28+.09*r,time);","this.host.fireProjectile?.('flame:'+p.id,p,height,a,1.51+.10*r,time);\n   if(trail.visual&&trail.visual.length>=2){\n    this.host.line(trail.visual,'#c95521',.105,198,true,'ink');\n    this.host.line(trail.visual,'#ffc777',.043,204,true,'core');\n   }");
  source=section(source,'   let pulse=-1,alpha=0;', '   if(pulse>=0&&alpha>0){',
    '   let pulse=-1,alpha=0;\n   if(age>=0&&age<.47){\n    pulse=age<.18?0:age<.33?1:2;\n    const attack=Math.min(1,(age+.012)/.026),tail=Math.min(1,(.47-age)/.12);\n    const flicker=.81+.19*Math.cos(age*41);\n    alpha=Math.round(247*attack*tail*flicker);\n   }');
  source=once(source,"if(pattern.skillId!=='THU_01'&&pattern.ground.size)","if(pattern.skillId==='THU_05'&&pattern.ground.size)");
  source=once(source,'map(hit=>hit.p),pattern.rank,alpha,pulse);','map(hit=>hit.p),pattern.rank,Math.round(alpha*.16),pulse);');
  source=once(source,"if(network&&pulse>0&&e.phase!=='network')continue;","if(network&&age>.35&&e.phase!=='network')continue;");
  source=once(source,"if(network&&pulse>0&&(distance(visual.from","if(network&&pulse>0&&e.phase==='network'&&(distance(visual.from");
  return source;
}
function meteor(source){
  source=once(source,'new Vec3(2.6,-8,-1.8)','new Vec3(3.3,-3.5,-2.3)');
  source=once(source,'fall=.4*t+.6*t*t,size=1.05+rank*.11','fall=.22*t+.78*t*t,size=(1.15+rank*.14)*(.72+.74*t)');
  return once(source,'target.x-2.6*(1-fall),this.groundHeight(target)+8*(1-fall)+size*.30,target.z+1.8*(1-fall)','target.x-3.3*(1-fall),this.groundHeight(target)+3.5*(1-fall)+size*.24,target.z+2.3*(1-fall)');
}
function blade(source){
  source=once(source,'bend=.04*Math.sin(Math.PI*t)','bend=.37*Math.sin(Math.PI*t)-.10*Math.sin(2*Math.PI*t)');
  return once(source,'core?1.32:1.08,core?1.21:1.08,core?.96:1.06','core?1.08:1.0,core?.92:.88,core?.63:.75');
}
function palette(source){
  source=once(source,"VfxLineStyle='core'|'glow'|'solid'","VfxLineStyle='core'|'glow'|'solid'|'ink'");
  return once(source,"static lineMaterial(style:VfxLineStyle,electric=false):Material {","static lineMaterial(style:VfxLineStyle,electric=false):Material {\n  if(style==='ink')return this.material('ribbon-white-v1','line',true,.89);");
}
function fire(source){
  return section(source,'    const right=this.camera.node.right,up=this.camera.node.up;', '   }\n  }\n  else if(this.camera',[
    '    const rotation=this.camera.node.worldRotation;',
    '    const normal=Vec3.transformQuat(new Vec3(),Vec3.UNIT_Z,rotation).normalize();',
    '    const along=direction.clone().subtract(normal.clone().multiplyScalar(Vec3.dot(direction,normal)));',
    '    if(along.lengthSqr()>.00001){along.normalize();const up=Vec3.cross(new Vec3(),normal,along).normalize();Quat.fromAxes(this.rotation,along,up,normal);}'
  ].join('\n'));
}
exports.replaceModules=function replaceModules(bundle,cocos){
  const ts=require(path.join(cocos,'node_modules/typescript'));
  const dependencies=(from)=>from==='cc'?'cc':'./'+from.split('/').pop()+'.ts';
  const root=path.join(cocos,'assets/scripts/features');
  const modules=[
    ['combat/runtime/MeleeSkillEffects',melee],['combat/runtime/SkillEnergyStrokes',energy],
    ['combat/runtime/NativeSkillVfx',skills],['combat/runtime/SkillMeteorBody',meteor],
    ['actors/runtime/MeleeBladeSurfaces',blade],['../shared/assets/VfxAssets',palette],['combat/runtime/SkillFireSprites',fire]
  ];
  const registrations=[];
  for(const [relative,edit]of modules){
    const name='chunks:///_virtual/'+path.basename(relative)+'.ts';
    const upstream=fs.readFileSync(path.join(root,relative+'.ts'),'utf8').replace(/\r\n/g,'\n');
    const authored=edit(upstream);
    const js=ts.transpileModule(authored,{compilerOptions:{module:ts.ModuleKind.System,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
    if(js.diagnostics?.length)throw Error(ts.flattenDiagnosticMessageText(js.diagnostics[0].messageText,'\n'));
    const registration=js.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,deps)=>'System.register('+JSON.stringify(name)+','+JSON.stringify(JSON.parse(deps).map(dependencies)));
    if(!registration.includes('System.register('+JSON.stringify(name)))throw Error('No compiled module named '+name);
    bundle=once(bundle,'System.register('+JSON.stringify(name)+',','System.register('+JSON.stringify(name+'.original')+',');
    registrations.push(registration);
  }
  return bundle+'\n'+registrations.join('\n');
};
