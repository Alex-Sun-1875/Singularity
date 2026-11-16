/** Two ground rings with a legible interior at phone size. Every call uses the accepted cast centre and radius. */
function castSeal(host:SkillVfxHost,e:SkillEvent,progress:number){
  const g=skillVfxGeometry(e),r=g.radiusMetres??0,center=e.to??e.at;
  if(!center||r<=0)return;
  const opacity=Math.min(1,progress/.13)*(1-.23*Math.max(0,(progress-.84)/.16));
  const family=e.skillId.slice(0,3),ink=family==='FIR'?'#e97928':family==='BOW'?'#7ba783':family==='THU'?'#8d91ed':'#ceb68f';
  const hot=family==='FIR'?'#f4a04f':ink, umber=family==='FIR'?'#743716':family==='THU'?'#464576':family==='BOW'?'#395e49':'#6b553d';
  function pos(turn:number,side:number,horizon:number){
    const x=(Math.cos(turn)*side+Math.sin(turn)*horizon)*r;
    const z=(-Math.sin(turn)*side+Math.cos(turn)*horizon)*r;
    return host.at({x:center.x+x,z:center.z+z},.038);
  }
  const stroke=(pts:Vec3[],color:string,width:number,a:number)=>host.line(pts,color,width,Math.round(a*opacity),false,'ink');
  function ring(radius:number,color:string,width:number,a:number){
    const pts=[];for(let i=0;i<=64;i++)pts.push(pos(i*TAU/64,0,radius));
    stroke(pts,color,width,a);
  }
  ring(.989,umber,.086,195);ring(.989,hot,.045,250);ring(.869,ink,.061,231);
  const diamond=(phi:number)=>[pos(phi,0,.874),pos(phi,-.032,.928),pos(phi,0,.976),pos(phi,.032,.928),pos(phi,0,.874)];
  for(let k=0;k<4;k++){
    const phi=Math.PI*k/2+.15;
    if(family==='FIR'){
      stroke(diamond(phi),hot,.036,235);
      // An open flame lobe widens at the root and bends back to the next spoke.
      const curve=[];
      for(let j=0;j<=14;j++){const t=j/14;curve.push(pos(phi,.19*Math.sin(Math.PI*t*1.8)*Math.sin(Math.PI*t),.18+.65*t));}
      for(let j=13;j>=0;j--){const t=j/14;curve.push(pos(phi,-.17*Math.pow(Math.sin(Math.PI*t),1.7),.18+.65*t));}
      stroke(curve,ink,.058,235);
      const wing=phi+Math.PI/4;
      stroke([pos(wing,-.30,.76),pos(wing,-.13,.60),pos(wing,0,.31),pos(wing,.06,.64),pos(wing,.23,.81)],ink,.049,216);
      stroke([pos(phi,.20,.904),pos(phi,.30,.86),pos(phi,.43,.818)],hot,.045,220);
      stroke([pos(wing,-.16,.92),pos(wing,0,.89),pos(wing,.16,.92)],umber,.050,222);
    }else if(family==='THU'){
      stroke([pos(phi,-.12,.915),pos(phi,-.025,.96),pos(phi,-.01,.90),pos(phi,.12,.94)],ink,.047,212);
      stroke([pos(phi,0,.14),pos(phi,.16,.50),pos(phi,-.09,.45),pos(phi,.01,.83)],ink,.063,206);
    }else if(family==='BOW'){
      stroke([pos(phi,-.13,.91),pos(phi,0,.965),pos(phi,.11,.91)],ink,.058,235);
      stroke([pos(phi,.09,.914),pos(phi,.17,.944),pos(phi,.24,.912)],umber,.044,218);
    }else{
      stroke([pos(phi,-.18,.91),pos(phi,-.06,.956),pos(phi,.09,.935),pos(phi,.15,.90)],umber,.072,245);
      stroke([pos(phi,-.14,.922),pos(phi,-.05,.947),pos(phi,.07,.934)],hot,.038,220);
    }
  }
  function engraved(coords:number[][],width:number,angle=.38){
    const line=coords.map(([x,z])=>pos(angle,x,z));
    stroke(line,umber,width*1.66,235);stroke(line,ink,width,244);
  }
  if(family==='WAR'){
    for(const phi of [.44,.44+Math.PI]){
      engraved([[-.12,.15],[-.105,.58],[.015,.832],[.13,.49],[.10,.16]],.049,phi);
      stroke([pos(phi,.015,.81),pos(phi,.025,.36),pos(phi,-.055,.23)],umber,.038,216);
      engraved([[-.36,.12],[-.24,.23],[-.12,.17],[.10,.17],[.24,.23],[.36,.12]],.051,phi);
      stroke([pos(phi,-.70,.19),pos(phi,-.49,.11),pos(phi,-.39,-.03)],umber,.053,214);
    }
  }else if(family==='BOW'){
    engraved([[-.72,.14],[-.63,.35],[-.42,.30],[-.18,.13],[0,.10],[.18,.13],[.42,.30],[.63,.35],[.72,.14]],.061);
    stroke([pos(.38,-.72,.14),pos(.38,0,-.39),pos(.38,.72,.14)],umber,.043,243);
    engraved([[0,-.74],[0,.76],[-.13,.48],[0,.57],[.13,.48],[0,.76]],.053);
    for(const side of [-1,1])engraved([[0,-.56],[side*.14,-.69],[side*.12,-.48],[0,-.34]],.048);
  }
  const star=[];for(let j=0;j<=8;j++)star.push(pos(.15+j*Math.PI/4,0,j%2?.072:.16));
  stroke(star,hot,.048,215);
}
