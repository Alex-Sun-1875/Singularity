export function drawArrowWake(host:SkillVfxHost,points:readonly Point[],color:string,split:boolean,rank:number,visualPoints?:readonly Vec3[],opacity=1):void{
  if(points.length<2||opacity<=0)return;
  const world=points.map((p,i)=>visualPoints?.[i]?.clone()??host.at(p,1.05));
  const wake=[world[0]];
  let remaining=split?1.05:1.75+rank*.055;
  for(let i=1;i<world.length && remaining>.001;i++){
    const last=wake[wake.length-1],distance=Vec3.distance(last,world[i]);
    if(distance<.001)continue;
    wake.push(distance<=remaining?world[i]:Vec3.lerp(new Vec3(),last,world[i],remaining/distance));
    remaining-=distance;
  }
  if(wake.length<2)return;
  // Follow only the physical arrow's travelled trail, including its real redirected leg.
  const alpha=Math.min(1,opacity),weight=split?.82:1;
  host.line(wake,'#7bb58a',.19*weight,Math.round(74*alpha),true,'glow');
  host.line(wake,'#91bd8a',.11*weight,Math.round(235*alpha),true,'ink');
  host.line(wake,'#e3e3b8',.027*weight,Math.round(236*alpha),true,'core');
}
