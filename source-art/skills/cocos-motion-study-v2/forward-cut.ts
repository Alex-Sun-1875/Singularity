/** A narrow forehand, backhand or descending cut drawn against the sampled weapon hand. */
export function drawMeleeSweep(host:MeleeVfxHost,key:string,p:Point,angle:number,radius:number,span:number,stage:number,t:number,alpha:number){
  if(!(radius>0&&span>0&&alpha>0)||t>=1||key.startsWith('echo:'))return;
  const heavy=stage===3,reverse=stage===2;
  const snap=1-Math.pow(1-Math.min(1,t/.47),2);
  const cutAngle=angle+(reverse?-1:1)*span*(-.26+.34*snap);
  const travel=radius*(.65+.35*snap);
  const ground={x:p.x+Math.sin(cutAngle)*travel,z:p.z+Math.cos(cutAngle)*travel};
  const tip=host.at(ground,heavy?1.54-.94*snap:reverse?1.36-.59*snap:.72+.56*snap);
  const grip=host.playerHand?.()??host.at(p,1.06);
  const recoil=Math.max(0,(t-.6)/.4),fade=1-recoil*recoil;
  const heel=Vec3.lerp(new Vec3(),grip,tip,.01+.54*recoil*recoil);
  const width=(heavy?.72:reverse?.51:.55)*(.81+.19*snap)*(.82+.18*fade);
  const strength=Math.round(alpha*fade);
  host.slash?.(key,heel,tip,width,strength,t);
  const shoulder=Vec3.lerp(new Vec3(),heel,tip,.39);
  shoulder.y+=heavy?.17:reverse?-.14:.12;
  const nib=Vec3.lerp(new Vec3(),heel,tip,.88);
  nib.y+=heavy?.06:reverse?-.03:.045;
  // A warm dark bevel keeps the steel readable over the pale in-game terrain.
  host.line([heel,shoulder,nib,tip],'#9d6639',heavy?.064:.044,Math.round(strength*.78),true,'ink');
  shoulder.y+=.047;nib.y+=.018;
  host.line([heel,shoulder,nib,tip],'#ffe3ac',heavy?.037:.023,Math.round(strength*.95),true,'core');
  if((reverse||heavy)&&t<.72){
    const a=Vec3.lerp(new Vec3(),heel,tip,.18), b=Vec3.lerp(new Vec3(),heel,tip,.79);
    a.y+=heavy?.22:-.18;b.y+=heavy?.11:-.055;
    host.slash?.(key+':filing',a,b,width*.28,Math.round(strength*.55),t);
  }
}
