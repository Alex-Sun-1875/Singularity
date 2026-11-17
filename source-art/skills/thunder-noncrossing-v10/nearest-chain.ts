 /** Design preview only: one nearest-neighbour path, degree <= 2, no crossings.
  * Keep the existing victims, radius, LOS, hit rolls and authored damage beats.
  * A failed contact is not promoted to a relay. No decorative closure edges. */
 private lightningNetwork(c:CombatCast,enemies:EnemyState[],segment:number,fraction:number,primaryId?:string,followFraction=fraction){
  const project=(p:Point):Point=>(globalThis as any).reviewLightningProject?.(p)??p;
  const nodes=enemies.filter(e=>e.hp>0).map(enemy=>({enemy,id:enemy.id,p:at(enemy),v:project(enemy)}));
  const remaining=new Set(nodes.map(node=>node.id));
  const edges:{a:Point;b:Point}[]=[];
  const hop=c.rank.connectionRadiusMetres??c.rank.geometry?.radiusMetres??0;
  const entry=c.skillId==='THU_02'||c.rank.geometry?.origin==='caster'?c.from:c.to;
  const cross=(a:Point,b:Point,p:Point)=>(b.x-a.x)*(p.z-a.z)-(b.z-a.z)*(p.x-a.x);
  const interior=(p:Point,a:Point,b:Point)=>{
   const length=Math.hypot(b.x-a.x,b.z-a.z);if(length<1e-6)return false;
   const t=((p.x-a.x)*(b.x-a.x)+(p.z-a.z)*(b.z-a.z))/(length*length);
   return t>1e-5&&t<1-1e-5&&Math.abs(cross(a,b,p))/length<1e-4;
  };
  const intersects=(a:Point,b:Point,u:Point,v:Point)=>{
   if(interior(a,u,v)||interior(b,u,v)||interior(u,a,b)||interior(v,a,b))return true;
   return cross(a,b,u)*cross(a,b,v)<-1e-7&&cross(u,v,a)*cross(u,v,b)<-1e-7;
  };
  let tail:typeof nodes[number]|undefined;
  while(remaining.size){
   const from=tail?.p??entry,visualFrom=tail?.v??project(c.from);
   const candidates=nodes.filter(node=>remaining.has(node.id)&&(!tail||distance(from,node.p)<=hop+.001)&&this.host.visible(from,node.p)&&!edges.some(edge=>intersects(visualFrom,node.v,edge.a,edge.b)));
   candidates.sort((a,b)=>(!tail&&primaryId?Number(b.id===primaryId)-Number(a.id===primaryId):0)||distance(from,a.p)-distance(from,b.p)||a.id.localeCompare(b.id));
   const next=candidates[0];if(!next)break;
   remaining.delete(next.id);
   this.hit(c,next.enemy,next.id===primaryId?fraction:followFraction,segment,from,tail?'network':'connection',tail?.id);
   ((globalThis as any).reviewLightningChoices??=[]).push({castId:c.id,skillId:c.skillId,segment,sourceId:tail?.id,from:{...from},targetId:next.id,targetedEntry:!tail&&!!primaryId,candidates:candidates.map(node=>({id:node.id,distance:distance(from,node.p)})),hit:c.hits.includes(`${segment}:${next.id}`)});
   if(!c.hits.includes(`${segment}:${next.id}`))continue;
   edges.push({a:visualFrom,b:next.v});tail=next;
  }
 }
