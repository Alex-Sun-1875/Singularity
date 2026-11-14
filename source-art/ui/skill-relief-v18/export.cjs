// Extend the project's licensed SVG icon family and original continuous gold frame.
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),cp=require('node:child_process');
const root=__dirname,project=path.resolve(root,'../../..'),source=path.join(root,'../game-icons');
const output=path.join(project,'src/cocos/assets/resources/ui/combat-relief');
const chrome=path.join(project,'src/cocos/assets/resources/ui/quiet-bronze');
const {Resvg}=require(path.join(project,'src/cocos/node_modules/@resvg/resvg-js'));
fs.mkdirSync(output,{recursive:true});fs.mkdirSync(path.join(root,'masks'),{recursive:true});
const sha=d=>crypto.createHash('sha256').update(d).digest('hex');
const manifest=JSON.parse(fs.readFileSync(path.join(source,'sources.json'),'utf8'));
const records=[];
for(const id of ['attack','bow','staff','dash','skill','spell0','spell1','checks']){
 const sourceId=id==='staff'?'spell0':id;
 let svg=fs.readFileSync(path.join(source,sourceId+'.svg'),'utf8').replace('<path d="M0 0h512v512H0z"/>','');
 if(id==='spell1')svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><title>Original forked lightning silhouette</title><path fill="#fff" d="M300 18 92 296h143l-37 198 222-296H271Z"/><path fill="#fff" d="m119 43 54 10-26 82-49-11 25-33-31-3Zm284 290 48 12-29 92-50-12 29-36-32-6Z"/></svg>';
 svg=svg.replace(/<svg\b[^>]*>/, '<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 512 512"><g transform="translate(36 36) scale(.86)">').replace('</svg>','</g></svg>');
 fs.writeFileSync(path.join(root,id+'.svg'),svg+'\n');
 fs.writeFileSync(path.join(root,'masks',id+'.png'),new Resvg(svg).render().asPng());
 const upstream=manifest.icons.find(i=>i.id===sourceId);
 records.push({id,source:id==='spell1'?'Project-original lightning silhouette':`source-art/ui/game-icons/${sourceId}.svg`,...(id==='spell1'?{license:'Project original'}:{author:upstream.author,license:manifest.license,repository:manifest.repository,commit:manifest.commit,upstreamSHA256:upstream.sha256}),svgSHA256:sha(svg)});
}
const old=fs.readFileSync(path.join(root,'../clean-gold-v11/unified-gold-skill-v16.svg'),'utf8');
const stem=old.match(/<path data-role="continuous-stem-with-integral-open-returns" d="([^"]+)"/)[1];
const frame=`<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512"><title>Heavy antique gold skill medallion with recessed steel face</title><defs>
<linearGradient id="side" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#B28A49"/><stop offset=".56" stop-color="#6A4425"/><stop offset="1" stop-color="#26160E"/></linearGradient>
<linearGradient id="gold" x1=".15" y1="0" x2=".85" y2="1"><stop stop-color="#FAE3A8"/><stop offset=".17" stop-color="#C39B56"/><stop offset=".29" stop-color="#EAD09A"/><stop offset=".43" stop-color="#87612E"/><stop offset=".58" stop-color="#AC8142"/><stop offset=".76" stop-color="#DDBA77"/><stop offset=".9" stop-color="#715027"/><stop offset="1" stop-color="#3F2918"/></linearGradient>
<linearGradient id="rim" x1="0" y1="0" x2=".7" y2="1"><stop stop-color="#544632"/><stop offset=".35" stop-color="#302A21"/><stop offset=".66" stop-color="#1C1915"/><stop offset="1" stop-color="#45331F"/></linearGradient>
<linearGradient id="lip" x1=".1" y1="0" x2=".7" y2="1"><stop stop-color="#FFF0BE"/><stop offset=".32" stop-color="#B18A48"/><stop offset=".55" stop-color="#60401E"/><stop offset=".8" stop-color="#C09A58"/><stop offset="1" stop-color="#E0BE7D"/></linearGradient>
<radialGradient id="face" cx=".34" cy=".24" r=".86"><stop stop-color="#3B3931"/><stop offset=".35" stop-color="#24251F"/><stop offset=".7" stop-color="#171A17"/><stop offset="1" stop-color="#0D100F"/></radialGradient>
<clipPath id="face-clip"><circle cx="256" cy="250" r="188"/></clipPath></defs>
<circle cx="256" cy="260" r="248" fill="#080604"/>
<circle cx="256" cy="257" r="247" fill="url(#side)"/>
<circle cx="256" cy="250" r="246" fill="url(#gold)" stroke="#140D07" stroke-width="3"/>
<circle cx="256" cy="250" r="241" fill="none" stroke="#FBE6B2" stroke-opacity=".65" stroke-width="2"/>
<circle cx="256" cy="250" r="235" fill="url(#rim)" stroke="#392719" stroke-width="3"/>
<g transform="translate(0 -6)" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="${stem}" transform="translate(1.2 2.6)" stroke="#100B07" stroke-width="8"/><path d="${stem}" stroke="url(#gold)" stroke-width="5.4"/><path d="${stem}" transform="translate(-.5 -.8)" stroke="#E8CEA0" stroke-opacity=".55" stroke-width="1.3"/></g>
<circle cx="256" cy="250" r="204" fill="#090C0A" stroke="#1B140D" stroke-width="5"/>
<circle cx="256" cy="250" r="199" fill="url(#lip)"/>
<circle cx="256" cy="250" r="191" fill="url(#face)" stroke="#070A08" stroke-width="3"/>
<g clip-path="url(#face-clip)" stroke="#D9D1A6" stroke-opacity=".018" stroke-width="1">${Array.from({length:32},(_,i)=>`<path d="M50 ${70+i*12}h412"/>`).join('')}</g>
<path d="M91 152A190 190 0 0 1 360 91" fill="none" stroke="#D7C7A4" stroke-opacity=".19" stroke-width="1.5"/>
</svg>\n`;
fs.writeFileSync(path.join(root,'unified-gold-skill-v18.svg'),frame);
fs.writeFileSync(path.join(chrome,'unified-gold-skill-v18.png'),new Resvg(frame).render().asPng());
fs.writeFileSync(path.join(root,'sources.json'),JSON.stringify({version:'skill-relief-v18',date:'2026-11-10',userDirection:'Remove shortcut badges; make skill icons more refined and substantial.',construction:'Existing Game-icons silhouettes rendered with deterministic beveled metal relief; original continuous v16 scrollwork retained in a deeper cast-gold rim. No generative model or new dependencies.',assets:records,frame:{source:'source-art/ui/skill-relief-v18/unified-gold-skill-v18.svg',derivedFrom:'source-art/ui/clean-gold-v11/unified-gold-skill-v16.svg',license:'Project original',svgSHA256:sha(frame)},artReview:{generation:'Deterministic SVG rasterization and alpha-mask embossing',isolated:'Pending',runtime:'Pending',userAcceptance:'Not recorded'}},null,2)+'\n');
const run=cp.spawnSync('python',[path.join(root,'emboss.py')],{encoding:'utf8'});if(run.status!==0)throw new Error(run.stderr||run.stdout);process.stdout.write(run.stdout);
