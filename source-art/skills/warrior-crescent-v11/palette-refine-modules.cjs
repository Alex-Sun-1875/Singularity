const fs=require('node:fs'),path=require('node:path');
function change(source,before,after){if(source.split(before).length!==2)throw Error('Snapshot changed near '+before.slice(0,65));return source.replace(before,()=>after);}
function section(source,from,until,replacement){const a=source.indexOf(from),b=source.indexOf(until,a+from.length);if(a<0||b<0)throw Error('Missing source section '+from);return source.slice(0,a)+replacement+'\n'+source.slice(b);}
exports.replaceModules=function(bundle,cocos,variant,sources){
 const ts=require(path.join(cocos,'node_modules/typescript')),root=sources||path.join(cocos,'assets/scripts/features');
 const edits=[
  ['actors/runtime/MeleeBladeSurfaces',()=>fs.readFileSync(path.join(__dirname,'PaletteStudy.ts'),'utf8')],
  ['combat/runtime/MeleeSkillEffects',source=>{
   source=section(source,'/** All blade vertices','/** Small local contact',`export function drawMeleeSweep(host:MeleeVfxHost,key:string,p:Point,angle:number,radius:number,span:number,stage:number,t:number,alpha:number){host.blade?.(key+':stage:'+stage,p,1.02,angle,radius,span,.2,alpha,t);}`);
   return source.slice(0,source.indexOf('/** Small local contact'))+'export function drawMeleeContact(...args:any[]){}\n';
  }],
  ['combat/runtime/Effects',source=>{
   source=change(source,"async prepareShaders(point:Point,game?:GameSession){await VfxAssets.prepareShaders(this.world.root,this.at(point,.9),this.world.mesh('cylinder'));if(game)await this.prepareEquipment(game);}","async prepareShaders(point:Point,game?:GameSession){if(game)await this.prepareEquipment(game);}");
   source=change(source,'Math.min(1,age/.18),alpha','Math.min(1,age/.28),alpha');
   source=change(source,'this.blades.draw(key,this.playerAt(p,height),angle,radius,span,width,alpha,progress,normal)','this.blades.drawFromHand(this.playerSource?.()?.hand,key,this.playerAt(p,height),angle,radius,span,width,alpha,progress,normal)');
   return change(source,'const host={',`const host={
    warriorCross:(key:string,p:Point,a:number,length:number,t:number,alpha:number)=>this.blades.cross(key,this.at(p,1.02),a,length,t,alpha),
    warriorCleave:(key:string,p:Point,a:number,radius:number,t:number,alpha:number)=>this.blades.cleave(key,this.at(p,0),a,radius,t,alpha),
    warriorGuard:(key:string,p:Point,a:number,age:number,alpha:number,hit=false)=>this.blades.guard(key,this.at(p,1.02),a,age,alpha,hit),
    warriorPulse:(key:string,p:Point,a:number,t:number,alpha:number,iron=false)=>this.blades.pulse(key,this.at(p,1.02),a,t,alpha,iron,this.playerSource?.()?.hand),
    warriorRush:(key:string,from:Point,to:Point,a:number,t:number)=>this.blades.rush(key,this.at(from,.18),this.at(to,.18),a,t),`);
  }],
  ['combat/runtime/NativeSkillVfx',source=>{
   source=change(source,'export interface SkillVfxHost {',`export interface SkillVfxHost {
    warriorCross?(key:string,p:Point,a:number,length:number,t:number,alpha:number):void;
    warriorCleave?(key:string,p:Point,a:number,radius:number,t:number,alpha:number):void;
    warriorGuard?(key:string,p:Point,a:number,age:number,alpha:number,hit?:boolean):void;
    warriorPulse?(key:string,p:Point,a:number,t:number,alpha:number,iron?:boolean):void;
    warriorRush?(key:string,from:Point,to:Point,a:number,t:number):void;`);
   source=change(source,"kind:'cross'|","kind:'warriorMastery'|'warriorIron'|'warriorRush'|'cross'|");
   source=change(source,"this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.28:.22)","this.add(e,'meleeSweep',id==='WAR_05'&&e.segment===2?.38:.32)");
   source=change(source,"this.add(e,'cross',.22)","this.add(e,'cross',.34)");
   source=change(source,"this.add(e,'cleave',.28)","this.add(e,'cleave',.40)");
   source=change(source,'const alpha=Math.round(225*Math.pow(1-t,1.7));',"const alpha=['meleeSweep','cross','cleave'].includes(c.kind)?Math.round(245*(t<.65?1:Math.pow((1-t)/.35,1.1))):Math.round(225*Math.pow(1-t,1.7));");
   source=section(source,"  if(family==='WAR'){","  }else if(family==='BOW'){","  if(family==='WAR'){this.add(e,'metal',.18);");
   source=change(source,"else if(id==='WAR_P1'||id==='WAR_P2'||id==='THU_P1')this.add(e,'metal',.22);","else if(id==='WAR_P1'||id==='WAR_P2')this.add(e,id==='WAR_P1'?'warriorMastery':'warriorIron',.42);else if(id==='THU_P1')this.add(e,'metal',.22);");
   source=change(source,"if(e.type==='skill_release'){","if(e.type==='skill_release'){\n   if(id==='WAR_02'&&e.phase==='rush')this.add(e,'warriorRush',e.duration??.18);");
   source=change(source,"   if(c.kind==='trap'){",`   if(c.kind==='warriorMastery'||c.kind==='warriorIron'){
    this.host.warriorPulse?.('passive:'+e.skillId+':'+e.castId,e.from,a,t,alpha,c.kind==='warriorIron');continue;
   }
   if(c.kind==='warriorRush'){this.host.warriorRush?.('rush-trail:'+e.castId,e.from,player,a,t);continue;}
   if(c.kind==='trap'){`);
   source=change(source,"   if(c.kind==='shield'){",`   if(c.kind==='shield'){
    if(e.skillId==='WAR_03'){if(player.shield>0)this.host.warriorGuard?.('guard:'+e.castId,player,player.angle,age,alpha);continue;}`);
   source=change(source,"   if(c.kind==='guardHit'){this.shield(e,p,player.angle,alpha);continue;}","   if(c.kind==='guardHit'){if(e.skillId==='WAR_03')this.host.warriorGuard?.('guard-hit:'+e.castId,p,player.angle,age,alpha,true);else this.shield(e,p,player.angle,alpha);continue;}");
   source=section(source,"   if(c.kind==='metal'){","   if(c.kind==='heal'){","   if(c.kind==='metal')continue;");
   source=section(source,"   if(c.kind==='cross'){","   if(c.kind==='cleave'){",`   if(c.kind==='cross'){
    const g=skillVfxGeometry(e),stamp=c as typeof c&{warriorImpact?:Point};
    if(!stamp.warriorImpact){const hit=this.cues.find(q=>q.kind==='metal'&&q.event.castId===e.castId&&q.event.targetId);stamp.warriorImpact={...(hit?this.point(hit.event):p)};}
    this.host.warriorCross?.('cross:'+e.castId,stamp.warriorImpact,a,g.lengthMetres??1.6,t,alpha);continue;
   }`);
   source=section(source,"   if(c.kind==='cleave'){","  for(const [id,path]of this.trails){",`   if(c.kind==='cleave'){
    this.host.warriorCleave?.('cleave:'+e.castId,p,a,skillVfxGeometry(e).radiusMetres??1.8,t,alpha);continue;
   }
  }`);
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
 return change(bundle,'this.preparationResources.prepare(this.session)','Promise.resolve()');
};
