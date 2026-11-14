// Vector rasterization uses resvg; original shapes and attribution stay intact.
const {Resvg}=require('@resvg/resvg-js');
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const source=path.resolve(__dirname,'../../../source-art/ui/game-icons');
const out=path.resolve(__dirname,'../assets/resources/ui/icons');fs.mkdirSync(out,{recursive:true});
const manifest=JSON.parse(fs.readFileSync(path.join(source,'sources.json'),'utf8'));
manifest.icons=manifest.icons.filter(item=>item.id!=='oil');
for(const item of manifest.icons){const svg=fs.readFileSync(path.join(source,item.id+'.svg'),'utf8').replace('<path d="M0 0h512v512H0z"/>','');const data=new Resvg(svg,{fitTo:{mode:'width',value:128}}).render().asPng();fs.writeFileSync(path.join(out,item.id+'.png'),data);item.exportSHA256=crypto.createHash('sha256').update(data).digest('hex');}
fs.copyFileSync(path.join(source,'CREDITS.txt'),path.join(out,'CREDITS.txt'));
fs.writeFileSync(path.join(out,'provenance.json'),JSON.stringify({...manifest,exporter:'@resvg/resvg-js@2.6.2',size:128,changes:'Removed full-canvas black background path; transparent PNG; runtime tinting.'},null,2));
console.log('Rendered '+manifest.icons.length+' original Game-icons vectors to 128px PNG.');
