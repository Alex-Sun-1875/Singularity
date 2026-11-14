// Render the actual UiChrome paths with lightweight Graphics capture, using the
// existing TypeScript transpiler + Resvg. No game/runtime behavior is changed.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=__dirname,project=path.resolve(root,'../../..');
const ts=require(path.join(project,'src/cocos/node_modules/typescript'));
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
class Color{constructor(r=0,g=0,b=0,a=255){Object.assign(this,{r,g,b,a});}}
class Graphics{
 constructor(){this.xml=[];this.d='';this.lineWidth=1;this.strokeColor=new Color();}
 moveTo(x,y){this.d+=`M${x} ${y}`;}lineTo(x,y){this.d+=`L${x} ${y}`;}
 bezierCurveTo(a,b,c,d,e,f){this.d+=`C${a} ${b} ${c} ${d} ${e} ${f}`;}
 close(){this.d+='Z';}
 circle(x,y,r){this.d+=`M${x-r} ${y}a${r} ${r} 0 1 0 ${r*2} 0a${r} ${r} 0 1 0 ${-r*2} 0`;}
 stroke(){const c=this.strokeColor;this.xml.push(`<path d="${this.d}" stroke="rgb(${c.r},${c.g},${c.b})" stroke-opacity="${c.a/255}" stroke-width="${this.lineWidth}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`);this.d='';}
}
class Node{addComponent(Type){return new Type();}}
const exportsObject={},moduleObject={exports:exportsObject};
const source=fs.readFileSync(path.join(project,'src/cocos/assets/scripts/shared/ui/UiChrome.ts'),'utf8');
const js=ts.transpileModule(source,{compilerOptions:{target:ts.ScriptTarget.ES2020,module:ts.ModuleKind.CommonJS}}).outputText;
vm.runInNewContext(js,{exports:exportsObject,module:moduleObject,require:name=>name==='cc'?{Color,Graphics,Node}:require(name)});
const {UiChrome}=moduleObject.exports;
const png=id=>'data:image/png;base64,'+fs.readFileSync(path.join(project,'src/cocos/assets/resources/ui/quiet-bronze',id+'.png')).toString('base64');
const image=(id,x,y,w,h=w)=>`<image href="${png(id)}" x="${x}" y="${y}" width="${w}" height="${h}"/>`;
const native=(g,x,y)=>`<g transform="translate(${x} ${y}) scale(1 -1)">${g.xml.join('')}</g>`;
const circle=(id,x,y,d)=>image(id,x-d/2,y-d/2,d)+native(UiChrome.circleOrnament(new Node(),d/2),x,y);
let body='<rect width="1024" height="560" fill="#16110D"/><g fill="#D2B985" font-family="sans-serif" font-size="18"><text x="24" y="27">Shared subdued gold: panels, map, supplies and skills</text><text x="24" y="258">Native corner curls and centered border vines</text><text x="386" y="335">Eight map motifs</text><text x="708" y="335">Four small rim curls</text></g>';
body+=image('unified-gold-panel-v13',24,60,280,140)+native(UiChrome.frame(new Node(),280,140),164,130);
body+=image('unified-gold-panel-v13',24,290,280,140)+native(UiChrome.frame(new Node(),280,140),164,360);
body+=circle('unified-gold-ring-v13',510,170,240);
body+=circle('unified-gold-medallion-v13',740,100,60)+circle('unified-gold-skill-v13',860,100,86);
for(let i=0;i<3;i++)body+=circle('unified-gold-medallion-v13',85+i*80,365,60);
for(let i=0;i<3;i++)body+=circle('unified-gold-skill-v13',724+i*105,390,i===2?86:64);
const svg=`<svg xmlns="http://www.w3.org/2000/svg" width="1024" height="560" viewBox="0 0 1024 560">${body}</svg>`;
fs.writeFileSync(path.join(root,'isolated-preview-v13.svg'),svg);
fs.writeFileSync(path.join(root,'isolated-preview-v13.png'),new Resvg(svg).render().asPng());
console.log('Rendered actual UiChrome v13 engraving paths with the exported SVG family.');
