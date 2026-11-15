/** Export the code-native one-colour bottle glyph with the existing SVG renderer. */
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'../..'),project=path.join(root,'src/cocos');
const {Resvg}=require(require.resolve('@resvg/resvg-js',{paths:[project]}));
const source=path.join(root,'source-art/ui/supply-hud-icons-v1'),resources=path.join(project,'assets/resources');
const input=path.join(source,'health-bottle-solid.svg'),output=path.join(resources,'ui/icons/supplies-bottle.png');
fs.writeFileSync(output,new Resvg(fs.readFileSync(input),{fitTo:{mode:'width',value:128}}).render().asPng());
if(!fs.existsSync(output+'.meta')){
 const template=fs.readFileSync(path.join(resources,'ui/icons/potion-health.png.meta'),'utf8'),id=JSON.parse(template).uuid;
 fs.writeFileSync(output+'.meta',template.replaceAll(id,crypto.randomUUID()).replaceAll('potion-health','supplies-bottle').replaceAll('"repeat"','"clamp-to-edge"'));
}
const hash=file=>crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const relative=file=>path.relative(root,file).split(path.sep).join('/');
fs.writeFileSync(path.join(source,'provenance.json'),JSON.stringify({date:'2026-11-15',method:'Original SVG glyph matching the approved round health bottle; exported with the existing @resvg/resvg-js dependency.',reference:'src/cocos/assets/resources/equipment/supplies-v2/health-bottle.png',source:relative(input),sourceSha256:hash(input),output:relative(output),sha256:hash(output),size:[128,128],palette:'White RGB with transparent background; MapTools applies the existing UI_COLORS.ink tint and a -45-degree node rotation (cork towards the upper right).',hud:'Potion shortcuts reuse each SUPPLIES.groundArt directly, with a 45-degree node rotation and neutral white tint. No duplicate colour artwork.',review:'Source glyph reviewed; see README for Cocos icon checks and the full-export limitation. TapTap native acceptance pending.'},null,2)+'\n');
console.log(relative(output));
