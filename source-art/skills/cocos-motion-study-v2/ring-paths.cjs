// Read the same contours called by the Cocos cast event for the orthographic UI plate.
const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const ts=require(path.resolve(__dirname,'../../../src/cocos/node_modules/typescript'));
const js=ts.transpileModule(fs.readFileSync(path.join(__dirname,'cast-seal.ts'),'utf8'),{compilerOptions:{target:ts.ScriptTarget.ES2020}}).outputText;
const seal=vm.runInNewContext(js+'\ncastSeal',{TAU:Math.PI*2,Math,skillVfxGeometry:()=>({radiusMetres:2.6})});
const paths={};
for(const id of ['WAR_04','BOW_06','FIR_02','THU_05']){
  const lines=[];
  const host={at:p=>p,line:(points,colour,width,alpha)=>lines.push({points:points.map(p=>[p.x/2.6,p.z/2.6]),colour,width:width/2.6,alpha})};
  seal(host,{skillId:id,to:{x:0,z:0}},.62);
  if(lines.length<12)throw Error('Incomplete seal '+id);
  paths[id]=lines;
}
process.stdout.write(JSON.stringify(paths));
