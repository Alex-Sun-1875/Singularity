// Shared clean-gold panel/circle family. Engraving is owned by UiChrome.ts.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,project=path.resolve(root,'../../..');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const output=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const palette={metal:'#B99456',light:'#D2B985',ornament:'#C29B5A',glint:'#D9CCA2',low:'#AB853B',mid:'#BE995A',shadow:'#1D170C'};
const gradients=`<linearGradient id="gold-metal" x1="0" y1="0" x2="1" y2="1">
 <stop stop-color="${palette.low}"/><stop offset=".16" stop-color="${palette.metal}"/>
 <stop offset=".29" stop-color="${palette.light}"/><stop offset=".44" stop-color="${palette.mid}"/>
 <stop offset=".62" stop-color="${palette.metal}"/><stop offset=".79" stop-color="${palette.light}"/><stop offset="1" stop-color="${palette.low}"/>
</linearGradient>
<linearGradient id="gold-highlight" x1="0" y1="0" x2="1" y2="1">
 <stop stop-color="${palette.glint}"/><stop offset=".26" stop-color="${palette.light}"/><stop offset=".58" stop-color="${palette.ornament}"/><stop offset=".86" stop-color="${palette.light}"/><stop offset="1" stop-color="${palette.mid}"/>
</linearGradient>
<linearGradient id="dark-inset" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#211910"/><stop offset=".4" stop-color="#19130E"/><stop offset="1" stop-color="#100D09"/></linearGradient>`;
function normalize(source){
 let svg=source;
 for(const id of ['gold-metal','gold-highlight','dark-inset'])svg=svg.replace(new RegExp(`<linearGradient id="${id}"[\\s\\S]*?<\\/linearGradient>`),'');
 return svg.replace('<defs>','<defs>'+gradients).replace(/<title>.*?<\/title>/,'<title>Unified subdued clean-gold surround; shared panel and circular palette</title>');
}
const panel=`<svg xmlns="http://www.w3.org/2000/svg" width="256" height="128" viewBox="0 0 256 128" fill="none"><title>Unified subdued gold panel; native engraving supplies the shared scrolls</title><defs>${gradients}</defs>
 <path d="M24 4H232C243 4 250 12 252 24V104C250 116 243 124 232 124H24C13 124 6 116 4 104V24C6 12 13 4 24 4Z" stroke="#070501" stroke-opacity=".94" stroke-width="5"/>
 <path d="M24 4H232C243 4 250 12 252 24V104C250 116 243 124 232 124H24C13 124 6 116 4 104V24C6 12 13 4 24 4Z" stroke="url(#gold-metal)" stroke-width="3.4"/>
 <path d="M24 8H232C240 8 246 14 248 24V104C246 114 240 120 232 120H24C16 120 10 114 8 104V24C10 14 16 8 24 8Z" stroke="#100C05" stroke-width="2.2"/>
 <path d="M24 11H232C239 11 243 16 245 25V103C243 112 239 117 232 117H24C17 117 13 112 11 103V25C13 16 17 11 24 11Z" stroke="${palette.ornament}" stroke-width="1.2"/>
 <path d="M25 5H231" stroke="url(#gold-highlight)" stroke-opacity=".72" stroke-width=".8"/>
 <path d="M25 119H231" stroke="#070501" stroke-opacity=".7" stroke-width="1.2"/>
</svg>`;
const definitions=[
 {id:'unified-gold-panel-v13',svg:panel,size:256,height:128},
 {id:'unified-gold-ring-v13',source:'clean-gold-ring-v12.svg',size:512},
 {id:'unified-gold-medallion-v13',source:'clean-gold-medallion-v12.svg',size:512},
 {id:'unified-gold-skill-v13',source:'clean-gold-skill-v12.svg',size:512},
 {id:'unified-gold-rail-v13',source:'clean-gold-rail-v12.svg',size:512},
];
const records=[];
for(const definition of definitions){
 const original=definition.svg??fs.readFileSync(path.join(root,definition.source),'utf8'),svg=definition.svg??normalize(original),svgPath=path.join(root,definition.id+'.svg');
 fs.writeFileSync(svgPath,svg);
 const png=new Resvg(svg,{fitTo:{mode:'width',value:definition.size}}).render().asPng();
 const target=path.join(output,definition.id+'.png');fs.writeFileSync(target,png);
 records.push({id:definition.id,source:path.relative(project,svgPath).replaceAll('\\','/'),sourceSHA256:sha(svg),derivedFrom:definition.source??'source-art/materials/chapter-one-v3/ui-kit/panel-frame.svg',asset:path.relative(project,target).replaceAll('\\','/'),pngSHA256:sha(png),size:[definition.size,definition.height??definition.size],bytes:png.length,nineSlice:definition.id.includes('panel')?[24,24,24,24]:[0,0,0,0]});
}
const provenance={version:'unified-gold-v13',date:'2026-11-08',userDirection:'Restore middle supplies and align rectangular/circular gold color and scroll decoration; add more motifs while keeping moderate brightness and thin clean-gold rims.',ownership:'Project-original SVG family derived from existing SupplyBelt panel and v12 circular designs. No external download or additional generation.',palette,gradient:'Identical normalized diagonal gradient and stops across panel, map, navigation and skill frames.',ornamentSource:'src/cocos/assets/scripts/shared/ui/UiChrome.ts',ornamentPolicy:'Metal PNGs contain no baked scrolls. Native shared frame()/circleOrnament() supply exactly one engraving layer: rectangular corner curls plus centered border vines, eight map motifs, four small-control rim curls.',exporter:'@resvg/resvg-js@2.6.2 (MPL-2.0), existing project dependency',assets:records,artReview:{source:'Shared palette/geometry verified; integrated review pending.',runtime:'Pending desktop/mobile screenshot review.',userAcceptance:'Not recorded.'}};
fs.writeFileSync(path.join(root,'provenance-v13.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify(records.map(({id,bytes,size})=>({id,bytes,size})),null,2));
