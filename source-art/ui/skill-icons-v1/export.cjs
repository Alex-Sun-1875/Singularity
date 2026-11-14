// Reuse the installed SVG rasterizer and the established relief renderer.
const fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process');
const root=__dirname,project=path.resolve(root,'../../..');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const manifest=JSON.parse(fs.readFileSync(path.join(root,'sources.json'),'utf8'));
const pilot=process.argv.includes('--pilot'),ids=new Set(['WAR_01','WAR_03','FIR_01','THU_01']);
fs.mkdirSync(path.join(root,'masks'),{recursive:true});
for(const item of manifest.assets.filter(a=>!pilot||ids.has(a.id))){
 let svg=fs.readFileSync(path.join(project,item.source),'utf8').replace('<path d="M0 0h512v512H0z"/>','');
 svg=svg.replace(/<svg\b[^>]*>/,'<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 512 512"><g transform="translate(36 36) scale(.86)">').replace('</svg>','</g></svg>');
 fs.writeFileSync(path.join(root,'masks',item.id.toLowerCase()+'.png'),new Resvg(svg).render().asPng());
}
const run=cp.spawnSync('python',[path.join(root,'render.py'),...(pilot?['--pilot']:[])],{encoding:'utf8'});
if(run.status!==0)throw Error(run.stderr||run.stdout);process.stdout.write(run.stdout);
