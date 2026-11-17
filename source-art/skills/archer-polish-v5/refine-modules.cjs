// Review-only changes to the current renderer. No combat or animation module is replaced.
const fs=require('node:fs');
const path=require('node:path');
function change(s,a,b){if(s.split(a).length!==2)throw Error('Source changed near '+a.slice(0,90));return s.replace(a,()=>b);}
function section(s,a,b,replacement){const start=s.indexOf(a),end=s.indexOf(b,start+a.length);if(start<0||end<0)throw Error('Missing '+a);return s.slice(0,start)+replacement+'\n'+s.slice(end);}

function energy(s){
 s=change(s,"import type {Vec3} from 'cc';","import {Vec3} from 'cc';");
 s=section(s,'export function drawArrowWake(','/** One small physical puncture',`export function drawArrowWake(host:SkillVfxHost,points:readonly Point[],color:string,split:boolean,rank:number,visualPoints?:readonly Vec3[],opacity=1,chaining=false):void {
 if(points.length<2||opacity<=0)return;
 const flown=points.map((p,i)=>visualPoints?.[i]?.clone()??host.at(p,1.05));
 if(split){host.line(flown,'#c6ddb0',.026,Math.round(115*opacity),true,'solid');detail(host,flown,'#d3eab0',.14,48*opacity,'glow');}
 const limit=chaining?2.35:split?1.25:.88,native:Vec3[]=[flown[0]];let travelled=0;
 for(let i=1;i<flown.length;i++){
  const previous=flown[i-1],next=flown[i],length=Vec3.distance(previous,next);
  if(length<.00001)continue;
  if(travelled+length>=limit){native.push(Vec3.lerp(new Vec3(),previous,next,(limit-travelled)/length));break;}
  native.push(next);travelled+=length;
 }
 if(native.length<2)return;
 const alpha=(chaining?215:split?225:190)*opacity;
 if(chaining)host.line(native,'#89c9ac',.13,Math.round(42*opacity),true,'glow');
 host.line(native,chaining?'#a9d7ad':split?'#d8efb4':color,chaining?.052:split?.044:.037,Math.round(alpha),true,'core');
 host.line(native,split?'#f5f8de':'#f1efdf',chaining?.017:split?.018:.014,Math.round(alpha*.82),true,'core');
}
`);
 s=change(s,'point:Point,angle:number,rank:number):void {\n const tier=rankOf(rank);','point:Point,angle:number,rank:number,chaining=false):void {\n const tier=rankOf(rank);');
 s=change(s,"3+Math.floor(tier/2),.34+tier*.018,'#e5d8ab'","3+Math.floor(tier/2)+(chaining?1:0),(.34+tier*.018)*(chaining?1.12:1),chaining?'#b8dfb7':'#e5d8ab'");
 return change(s,"1,.34+tier*.017,'#e8f0cc'","1,(.34+tier*.017)*(chaining?1.25:1),'#e8f0cc'");
}

function skills(s){
 s=change(s,'type Trail={points:Point[];','type Trail={castId?:string;points:Point[];');
 s=change(s,'bow?:{split:boolean;rank:number;color:string}','bow?:{split:boolean;rank:number;color:string;chaining:boolean}');
 s=change(s,' private trails=new Map<string,Trail>();',' private trails=new Map<string,Trail>();\n private arrowLegs:{points:Point[];visual?:Vec3[];time:number;rank:number;color:string}[]=[];');
 s=change(s,'drawArrowContact(this.host,p,a,r);',"drawArrowContact(this.host,p,a,r,e.skillId==='BOW_02');");
 s=change(s,'const path=e.projectileId?this.trails.get(e.projectileId):undefined;',"const path=e.projectileId?this.trails.get(e.projectileId):e.skillId==='BOW_02'?[...this.trails.values()].find(t=>t.castId===e.castId&&t.bow?.chaining):undefined;");
 s=change(s,"  if(e.type==='skill_segment'){",`  if(e.type==='skill_segment'){
   if(id==='BOW_02'&&e.phase==='redirect'&&e.projectileId){
    const path=this.trails.get(e.projectileId);
    if(path?.bow){
     const completed=path.points.map(p=>({...p})),visual=path.visual?.map(p=>p.clone())??completed.map(p=>this.host.at(p,1.05));
     // Replace a completed target-centre sample with the true redirect position.
     if(path.ended){completed.shift();visual.shift();}
     if(!completed.length||distance(completed[0],e.from)>.02){completed.unshift({...e.from});visual.unshift(this.host.at(e.from,1.05));}
     if(completed.length>1)this.arrowLegs.push({points:completed,visual,time:this.now,rank:path.bow.rank,color:path.bow.color});
     if(this.arrowLegs.length>8)this.arrowLegs.shift();
     path.points=[{...e.from}];path.visual=[this.host.at(e.from,1.05)];path.time=this.now;path.ended=false;
    }
   }`);
 s=change(s,"meta.skillId==='BOW_02'?1.15:.72","meta.skillId==='BOW_02'?2.8:1.05");
 s=change(s,'trail={points:[],time,visual:[]};','trail={points:[],time,visual:[],castId:p.castId};');
 s=change(s,'Math.min(split?56:14,trail.points.length)',"Math.min(split?56:meta.skillId==='BOW_02'?32:14,trail.points.length)");
 s=change(s,'trail.bow={split,rank:r,color};',"trail.bow={split,rank:r,color,chaining:meta.skillId==='BOW_02'};");
 s=change(s,'drawArrowWake(this.host,trail.points,color,split,r,trail.visual);','drawArrowWake(this.host,trail.points,color,split,r,trail.visual,1,trail.bow.chaining);');
 s=change(s,'const age=this.now-path.time;\n   if(path.bow',"const age=this.now-path.time,ttl=path.bow?.chaining?.38:.24;\n   if(path.bow");
 s=change(s,'&&age<.24){','&&age<ttl){');
 s=change(s,'Math.pow(1-age/.24,1.5));','Math.pow(1-age/ttl,1.5),path.bow.chaining);');
 s=change(s,'if(age>(path.bow?.24:.4))','if(age>(path.bow?ttl:.4))');
 s=change(s,'\n }\n clear(preserveCues=false){',`\n  this.arrowLegs=this.arrowLegs.filter(leg=>this.now-leg.time<.40);
  for(const leg of this.arrowLegs){const fade=.52*Math.pow(1-(this.now-leg.time)/.40,1.1);drawArrowWake(this.host,leg.points,leg.color,false,leg.rank,leg.visual,fade,true);}
 }
 clear(preserveCues=false){`);
 return change(s,'this.trails.clear();if(!preserveCues)','this.trails.clear();this.arrowLegs=[];if(!preserveCues)');
}

function effects(s){
 s=change(s,"p.owner==='player'&&p.skillId?.startsWith('BOW_')?1.35:1","p.owner==='player'?(p.skillId?.startsWith('BOW_')?1.42:1.06):1");
 s=change(s,'staff?.55:p.charged?1.2:1,color','staff?.55:p.charged?1.2:p.owner===\'player\'&&p.kind===\'arrow\'?.74:1,color');
 return change(s,'  this.line(path.points,color,spell?.065',`  if(p.owner==='player'&&p.kind==='arrow'){
   this.line(path.points,p.charged?'#e3d5a4':'#d6e0c5',p.charged?.038:.025,185,true,'core');
   this.line(path.points,'#f3efdb',.012,155,true,'core');return;
  }
  this.line(path.points,color,spell?.065`);
}

exports.replaceModules=function(bundle,cocos,refined,frozenSources){
 const ts=require(path.join(cocos,'node_modules/typescript')),registrations=[];
 for(const [name,edit]of [['SkillEnergyStrokes',energy],['NativeSkillVfx',skills],['Effects',effects]]){
  const source=fs.readFileSync(frozenSources?path.join(frozenSources,name+'.ts'):path.join(cocos,'assets/scripts/features/combat/runtime',name+'.ts'),'utf8').replace(/\r\n/g,'\n');
  const authored=refined?edit(source):source;
  const compiled=ts.transpileModule(authored,{compilerOptions:{module:ts.ModuleKind.System,target:ts.ScriptTarget.ES2020},reportDiagnostics:true});
  if(compiled.diagnostics?.length)throw Error(ts.flattenDiagnosticMessageText(compiled.diagnostics[0].messageText,'\n'));
  const id='chunks:///_virtual/'+name+'.ts';
  const registration=compiled.outputText.replace(/System\.register\((\[[^\]]*\])/,(_,imports)=>'System.register('+JSON.stringify(id)+','+JSON.stringify(JSON.parse(imports).map(x=>x==='cc'?'cc':'./'+x.split('/').pop()+'.ts')));
  bundle=change(bundle,'System.register('+JSON.stringify(id)+',','System.register('+JSON.stringify(id+'.original')+',');
  registrations.push(registration);
 }
 return bundle+'\n'+registrations.join('\n');
};
