/** Reuse the current steel sectors on horizontal and upright cutting planes. */
export function drawMeleeSweep(host:MeleeVfxHost,key:string,p:Point,angle:number,radius:number,span:number,stage:number,t:number,alpha:number){
 if(!(radius>0&&span>0&&alpha>0))return;
 const heavy=stage===3,reverse=stage===2,echo=key.startsWith('echo:');
 const progress=Math.max(0,Math.min(1,t));
 const horizontalTilt=heavy?.08:reverse?-.10:.13;
 const horizontalNormal=new Vec3(Math.cos(angle)*Math.sin(horizontalTilt),Math.cos(horizontalTilt),-Math.sin(angle)*Math.sin(horizontalTilt));
 const horizontalSpan=Math.min(span*.90,Math.PI*.50);
 host.blade?.(key+':horizontal',p,1.02,angle,radius*.98,horizontalSpan,
  Math.min(radius*.12,.12+stage*.025),Math.round(alpha*(heavy?.72:.94)),reverse?1-progress:progress,horizontalNormal);
 if(echo)return;
 const verticalProgress=Math.max(0,Math.min(1,(progress-.10)/.82));
 const reveal=Math.max(0,Math.min(1,(progress-.10)/.20));
 const tail=Math.max(0,Math.min(1,(progress-.72)/.28));
 const verticalAlpha=alpha*reveal*(1-tail*(heavy?.55:.82))*(heavy?1:.85);
 if(verticalAlpha<=1)return;
 const lean=reverse?-.11:heavy?.025:.09;
 const verticalNormal=new Vec3(Math.cos(angle)*Math.cos(lean),Math.sin(lean),-Math.sin(angle)*Math.cos(lean));
 const verticalSpan=Math.min(span*.96,Math.PI*.56);
 host.blade?.(key+':vertical',p,1.02,angle,radius*.98,verticalSpan,
  Math.min(radius*.11,.11+stage*.020),Math.round(verticalAlpha),1-verticalProgress,verticalNormal);
}
