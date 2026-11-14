// User revision: quieter clean gold, with a slightly wider skill-only surround.
// Preserve v11 sources and outputs for comparison; reuse installed resvg.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const root=__dirname,project=path.resolve(root,'../../..');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
const output=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
const sha=data=>crypto.createHash('sha256').update(data).digest('hex');
const metalColors=['#C99D45','#DAAE65','#F7DA9D','#E0B46A','#FFF0BF','#E4B66A'];
const dimColor=hex=>'#'+[1,3,5].map(i=>Math.round(parseInt(hex.slice(i,i+2),16)*.85).toString(16).padStart(2,'0')).join('').toUpperCase();
const palette=Object.fromEntries(metalColors.map(hex=>[hex,dimColor(hex)]));
function dim(source){
 return source.replace(/#[0-9A-Fa-f]{6}/g,hex=>palette[hex.toUpperCase()]??hex);
}
const definitions=[
 {id:'clean-gold-ring-v12',source:'clean-gold-ring-v11.svg'},
 {id:'clean-gold-medallion-v12',source:'clean-gold-medallion-v11.svg'},
 {id:'clean-gold-rail-v12',source:'clean-gold-rail-v11.svg'},
 {id:'clean-gold-skill-v12',source:'clean-gold-medallion-v11.svg',skill:true},
];
const records=[];
for(const definition of definitions){
 const sourcePath=path.join(root,definition.source),original=fs.readFileSync(sourcePath,'utf8');
 let svg=dim(original).replaceAll('polished gold','soft polished gold');
 if(definition.skill){
  // Outer bounds remain at253px including shadow. Widen the full visible rim
  // from18.725px to23.225px (24%) by moving the inner lip towards the center.
  svg=svg.replace('r="244.5" stroke="url(#gold-metal)" stroke-width="12"','r="242.25" stroke="url(#gold-metal)" stroke-width="16.5"')
    .replace('r="238.8"','r="234.3"').replace('r="236.3"','r="231.8"')
    .replace('r="234.9"','r="230.4"').replace('r="237" fill="url(#dark-inset)"','r="232.5" fill="url(#dark-inset)"')
    .replace('gold medallion','gold skill medallion');
 }
 const svgPath=path.join(root,definition.id+'.svg');fs.writeFileSync(svgPath,svg);
 const png=new Resvg(svg,{fitTo:{mode:'width',value:512}}).render().asPng();
 const target=path.join(output,definition.id+'.png');fs.writeFileSync(target,png);
 records.push({id:definition.id,source:path.relative(project,svgPath).replaceAll('\\','/'),sourceSHA256:sha(svg),derivedFrom:definition.source,derivedFromSHA256:sha(original),asset:path.relative(project,target).replaceAll('\\','/'),pngSHA256:sha(png),size:[512,512],bytes:png.length,outerRadiusIncludingShadow:253,totalRimWidth:definition.skill?23.225:18.725});
}
const provenance={
 version:'clean-gold-v12',date:'2026-11-08',
 userDirection:'Gold was too bright. Reduce brightness moderately, make skill borders slightly thicker, and leave navigation/map rim widths unchanged. Skill-name visibility is implemented separately in runtime.',
 ownership:'Original project-owned SVG family derived from SupplyBelt panel surround; no external art/download or new image generation.',
 designSource:'source-art/materials/chapter-one-v3/ui-kit/panel-frame.svg',
 changes:{metalRGBMultiplier:.85,normalRimWidth:18.725,skillRimWidth:23.225,skillWidthIncreasePercent:24.032,outerRadiusUnchanged:253,darkInsetUnchanged:true,mapAndRailWidthsUnchanged:true},
 palette,exporter:'@resvg/resvg-js@2.6.2 (MPL-2.0), existing dependency',assets:records,
 artReview:{source:'Source geometry and palette verified; v11 preserved.',runtime:'Pending integrated screenshot review.',userAcceptance:'Not recorded.'},
};
fs.writeFileSync(path.join(root,'provenance-v12.json'),JSON.stringify(provenance,null,2)+'\n');
console.log(JSON.stringify(records.map(({id,bytes,totalRimWidth})=>({id,bytes,totalRimWidth})),null,2));
