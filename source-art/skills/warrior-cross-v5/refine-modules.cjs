// Review the current steel surfaces in the existing Cocos battle scene.
const fs=require('node:fs');
const path=require('node:path');

function change(source,before,after){
  if(source.split(before).length!==2)throw Error('Current source changed near '+before.slice(0,80));
  return source.replace(before,()=>after);
}
function section(source,from,until,replacement){
  const begin=source.indexOf(from),end=source.indexOf(until,begin+from.length);
  if(begin<0||end<0)throw Error('Missing current source section '+from);
  return source.slice(0,begin)+replacement+'\n'+source.slice(end);
}

function previousBlade(source){
  source=change(source,'bodySpan=span*.64','bodySpan=span*.54');
  return change(source,'Math.max(width*4.7,radius*.21)','Math.max(width*5.5,radius*.54)');
}

function crossedBlade(source){
  source=previousBlade(source);
  source=change(source,'Math.max(width*5.5,radius*.54)','Math.max(width*4.8,radius*.34)');
  // Keep the production steel image, with a warm metal body visible on pale stone.
  source=change(source,'core?1.32:1.08,core?1.21:1.08,core?.96:1.06,level/16','core?1.40:1.02,core?1.24:.94,core?.89:.76,level/16*(core?1:.90)');
  source=change(source,'+.030*taper*(.5-inset)','+.050*taper*(.5-inset)');
  // The existing sector turns in its cutting plane. An upright plane needs a pitch component.
  source=change(source,'this.forward.normalize();Vec3.cross(this.side,this.normal,this.forward).normalize();',[
    'this.forward.normalize();',
    '  if(Math.abs(this.normal.y)<.35){',
    '   Vec3.cross(this.side,this.forward,this.normal).normalize();',
    '   const pitch=(sweep-.5)*(span-bodySpan);',
    '   this.forward.multiplyScalar(Math.cos(pitch)).add(this.side.multiplyScalar(Math.sin(pitch))).normalize();',
    '  }',
    '  Vec3.cross(this.side,this.normal,this.forward).normalize();',
  ].join('\n'));
  source=change(source,'slot.node.setWorldPosition(center);slot.node.setWorldRotation(this.rotation);',[
    'slot.node.setWorldPosition(center);',
    // Bias only the on-victim cross along the camera depth axis. Its projected
    // contact stays fixed while the body no longer hides both cutting planes.
    "  if(key.startsWith('cross:')&&this.camera?.node.isValid){this.midpoint.set(this.camera.node.forward).multiplyScalar(-.50).add(center);slot.node.setWorldPosition(this.midpoint);}",
    '  slot.node.setWorldRotation(this.rotation);',
  ].join('\n'));
  return source;
}

function crossedSweep(source){
  const authored=fs.readFileSync(path.join(__dirname,'crossed-sweep.ts'),'utf8');
  return section(source,'/** All blade vertices','/** Small local contact',authored);
}

function lingeringTrail(source){
  source=change(source,'this.basicTrails=this.basicTrails.filter(q=>this.now-q.start<.42);','this.basicTrails=this.basicTrails.filter(q=>this.now-q.start<.50);');
  return change(source,'smooth((age-.20)/.22)','smooth((age-.20)/.30)');
}

function crossedSkills(source){
  source=change(source,"this.add(e,'cross',.22)","this.add(e,'cross',.32)");
  source=change(source,"this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.28:.22)","this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.34:.28)");
  source=change(source,"this.add(e,'cleave',.28)","this.add(e,'cleave',.34)");
  source=change(source,'const alpha=Math.round(225*Math.pow(1-t,1.7));',[
    "const warriorCut=['meleeSweep','cross','cleave'].includes(c.kind);",
    '   const alpha=warriorCut?Math.round(245*(t<.42?1:Math.pow((1-t)/.58,1.25))):Math.round(225*Math.pow(1-t,1.7));',
  ].join('\n'));
  source=section(source,"   if(c.kind==='cross'){","   if(c.kind==='cleave'){",[
    "   if(c.kind==='cross'){",
    '    const g=skillVfxGeometry(e),length=g.lengthMetres??0;',
    "    const impact=this.cues.find(q=>q.kind==='metal'&&q.event.castId===e.castId&&q.event.targetId);",
    '    const victim=impact?game.state.enemies.find(n=>n.id===impact.event.targetId):undefined;',
    '    const anchor=offset(victim??p,a,0,-length*.82);',
    "    drawMeleeSweep(this.host,`cross:${e.castId}`,anchor,a,length*1.10,Math.PI*.68,3,t,alpha);",
    '    continue;',
    '   }',
  ].join('\n'));
  const drop='    const radius=skillVfxGeometry(e).radiusMetres??0;\n    for(let k=0;k<4;k++){';
  source=change(source,drop,[
    '    const radius=skillVfxGeometry(e).radiusMetres??0;',
    '    if(e.segment===0&&t<.68){',
    '     const across=radius*.68*Math.min(1,t*7);',
    '     const left=this.host.at(offset(p,a,-across,0),.52),right=this.host.at(offset(p,a,across,0),.52);',
    '     this.host.slash?.(`cleave:crossbar:${e.castId}`,left,right,.26+rank*.02,Math.round(alpha*.85),t);',
    "     this.host.line([left,right],'#ffe4ae',.034,Math.round(alpha*.75),true,'core');",
    '    }',
    '    for(let k=0;k<4;k++){',
  ].join('\n'));
  return source;
}

exports.replaceModules=function replaceModules(bundle,cocos,variant,sources){
  if(!['previous','design'].includes(variant))throw Error('Unknown warrior review variant '+variant);
  const ts=require(path.join(cocos,'node_modules/typescript'));
  const root=sources||path.join(cocos,'assets/scripts/features');
  const edits=variant==='previous'
    ? [['actors/runtime/MeleeBladeSurfaces',previousBlade]]
    : [['actors/runtime/MeleeBladeSurfaces',crossedBlade],['combat/runtime/MeleeSkillEffects',crossedSweep],['combat/runtime/Effects',lingeringTrail],['combat/runtime/NativeSkillVfx',crossedSkills]];
  const registrations=[];
  for(const [relative,edit]of edits){
    const source=fs.readFileSync(path.join(root,relative+'.ts'),'utf8').replace(/\r\n/g,'\n');
    const compiled=ts.transpileModule(edit(source),{compilerOptions:{module:ts.ModuleKind.System,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
    if(compiled.diagnostics?.length)throw Error(ts.flattenDiagnosticMessageText(compiled.diagnostics[0].messageText,'\n'));
    const name='chunks:///_virtual/'+path.basename(relative)+'.ts';
    const registration=compiled.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,imports)=>{
      const dependencies=JSON.parse(imports).map(imported=>imported==='cc'?'cc':'./'+imported.split('/').pop()+'.ts');
      return 'System.register('+JSON.stringify(name)+','+JSON.stringify(dependencies);
    });
    if(!registration.includes('System.register('+JSON.stringify(name)))throw Error('No compiled registration '+name);
    bundle=change(bundle,'System.register('+JSON.stringify(name)+',','System.register('+JSON.stringify(name+'.original')+',');
    registrations.push(registration);
  }
  return bundle+'\n'+registrations.join('\n');
};
