const fs=require('node:fs');const path=require('node:path');
function change(source,before,after){if(source.split(before).length!==2)throw Error('Snapshot changed near '+before.slice(0,60));return source.replace(before,()=>after);}
function section(source,from,until,replacement){const a=source.indexOf(from),b=source.indexOf(until,a+from.length);if(a<0||b<0)throw Error('Missing source section '+from);return source.slice(0,a)+replacement+'\n'+source.slice(b);}
exports.replaceModules=function(bundle,cocos,variant,sources){
 const ts=require(path.join(cocos,'node_modules/typescript'));
 const root=sources||path.join(cocos,'assets/scripts/features');
 const edits=[
  ['actors/runtime/MeleeBladeSurfaces',()=>fs.readFileSync(path.join(__dirname,'WarriorBladeStudy.ts'),'utf8')],
  ['combat/runtime/MeleeSkillEffects',source=>{
   source=section(source,'/** All blade vertices','/** Small local contact',`export function drawMeleeSweep(host:MeleeVfxHost,key:string,p:Point,angle:number,radius:number,span:number,stage:number,t:number,alpha:number){host.blade?.(key+':stage:'+stage,p,1.02,angle,radius,span,.2,alpha,t);}`);
   return source.slice(0,source.indexOf('/** Small local contact'))+'export function drawMeleeContact(...args:any[]){}\n';
  }],
  ['combat/runtime/Effects',source=>{
   source=change(source,"async prepareShaders(point:Point,game?:GameSession){await VfxAssets.prepareShaders(this.world.root,this.at(point,.9),this.world.mesh('cylinder'));if(game)await this.prepareEquipment(game);}","async prepareShaders(point:Point,game?:GameSession){if(game)await this.prepareEquipment(game);}");
   source=change(source,'Math.min(1,age/.18),alpha','Math.min(1,age/.28),alpha');
   return change(source,'this.blades.draw(key,this.playerAt(p,height),angle,radius,span,width,alpha,progress,normal)','this.blades.drawFromHand(this.playerSource?.()?.hand,key,this.playerAt(p,height),angle,radius,span,width,alpha,progress,normal)');
  }],
  ['combat/runtime/NativeSkillVfx',source=>{
   source=change(source,"this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.28:.22)","this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.38:.32)");
   source=change(source,'const alpha=Math.round(225*Math.pow(1-t,1.7));',"const alpha=c.kind==='meleeSweep'?Math.round(245*(t<.68?1:Math.pow((1-t)/.32,1.1))):Math.round(225*Math.pow(1-t,1.7));");
   source=section(source,"   if(c.kind==='metal'){","   if(c.kind==='heal'){","   if(c.kind==='metal')continue;");
   return source;
  }]
 ];
 for(const [relative,edit] of edits){
  const source=fs.readFileSync(path.join(root,relative+'.ts'),'utf8').replace(/\r\n/g,'\n');
  const result=ts.transpileModule(edit(source),{compilerOptions:{module:ts.ModuleKind.System,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
  if(result.diagnostics?.length)throw Error(ts.flattenDiagnosticMessageText(result.diagnostics[0].messageText,'\n'));
  const name='chunks:///_virtual/'+path.basename(relative)+'.ts';
  const registration=result.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,imports)=>'System.register('+JSON.stringify(name)+','+JSON.stringify(JSON.parse(imports).map(x=>x==='cc'?'cc':'./'+x.split('/').pop()+'.ts')));
  bundle=change(bundle,'System.register('+JSON.stringify(name)+',','System.register('+JSON.stringify(name+'.original')+',')+'\n'+registration;
 }
 // The review captures one real attack; inventory page prewarming is unrelated to it.
 bundle=change(bundle,'this.preparationResources.prepare(this.session)','Promise.resolve()');
 return bundle;
};
