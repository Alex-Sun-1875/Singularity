import type {Obstacle,Point} from '../../../core/Contracts';
import type {NavigationSearchBackend} from '../common/NavigationSearchBackend';
interface SearchNode extends Point {key:number;cost:number;score:number;closed:boolean;index:number;order:number;previous?:SearchNode}
const NEIGHBOURS:readonly (readonly [number,number,number])[]=[[1,0,1],[-1,0,1],[0,1,1],[0,-1,1],[1,1,Math.SQRT2],[1,-1,Math.SQRT2],[-1,1,Math.SQRT2],[-1,-1,Math.SQRT2]];
// Indexed adaptation of TinyQueue's binary heap (Vladimir Agafonkin, ISC;
// see THIRD_PARTY_NOTICES.txt). Keep enqueue order on equal scores so routes
// match the former stable linear scan, including after a decrease-key.
class NavigationFrontier {
 readonly data:SearchNode[]=[];
 private before(a:SearchNode,b:SearchNode){return a.score<b.score||a.score===b.score&&a.order<b.order;}
 push(node:SearchNode){node.index=this.data.length;this.data.push(node);this.up(node.index);}
 update(node:SearchNode){this.up(node.index);}
 pop(){
  const data=this.data,top=data[0],bottom=data.pop()!;
  if(data.length){
   let pos=0;const half=data.length>>1;
   while(pos<half){
    let child=(pos<<1)+1;const right=child+1;
    if(right<data.length&&this.before(data[right],data[child]))child=right;
    if(!this.before(data[child],bottom))break;
    data[pos]=data[child];data[pos].index=pos;pos=child;
   }
   data[pos]=bottom;bottom.index=pos;
  }
  top.index=-1;return top;
 }
 private up(pos:number){
  const data=this.data,node=data[pos];
  while(pos>0){const parent=(pos-1)>>1,current=data[parent];if(!this.before(node,current))break;data[pos]=current;current.index=pos;pos=parent;}
  data[pos]=node;node.index=pos;
 }
}
/** Local routes are derived from the same immutable collider footprints as rendering. */
export class Navigation {
 private static backend:NavigationSearchBackend|undefined;
 static useSearchBackend(backend?:NavigationSearchBackend){if(this.backend===backend)return;this.backend?.reset();this.backend=backend;}
 static resetSearchBackend(){this.backend?.reset();}
 dispose(){Navigation.backend?.release(this);}
 private cache=new Map<string,Point[]>();
 private gridEdges?:Uint16Array;
 private obstacleIndex?:{count:number;columns:number;minX:number;minZ:number;buckets:Map<number,Obstacle[]>;large:Obstacle[]};
 constructor(readonly width:number,readonly depth:number,readonly obstacles:Obstacle[],private readonly indexCollisions=false){}
 blocked(p:Point,r=.42){return this.blockedAt(p.x,p.z,r);}
 blockedAt(x:number,z:number,r=.42){
  if(Math.abs(x)>this.width/2-r||Math.abs(z)>this.depth/2-r)return true;
  if(!this.indexCollisions||this.obstacles.length<8||!Number.isFinite(x+z+r+this.width+this.depth)||r<0){
   for(let i=0;i<this.obstacles.length;i++){const o=this.obstacles[i];if(Math.abs(x-o.x)<o.width/2+r&&Math.abs(z-o.z)<o.depth/2+r)return true;}
   return false;
  }
  const grid=this.obstacleIndex?.count===this.obstacles.length?this.obstacleIndex:(this.obstacleIndex=this.indexObstacles());
  // Broad phase only: the original strict rectangle/radius test still decides
  // collision, including at doors, corners and exact obstacle boundaries.
  for(let i=0;i<grid.large.length;i++){const o=grid.large[i];if(Math.abs(x-o.x)<o.width/2+r&&Math.abs(z-o.z)<o.depth/2+r)return true;}
  const minX=Math.floor((x-r)/4),maxX=Math.floor((x+r)/4),minZ=Math.floor((z-r)/4),maxZ=Math.floor((z+r)/4);
  for(let cz=minZ;cz<=maxZ;cz++)for(let cx=minX;cx<=maxX;cx++){
   const bucket=grid.buckets.get((cz-grid.minZ)*grid.columns+cx-grid.minX);if(!bucket)continue;
   for(let i=0;i<bucket.length;i++){const o=bucket[i];if(Math.abs(x-o.x)<o.width/2+r&&Math.abs(z-o.z)<o.depth/2+r)return true;}
  }
  return false;
 }
 private indexObstacles(){
  const minX=Math.floor(-this.width/8),maxX=Math.floor(this.width/8),minZ=Math.floor(-this.depth/8),maxZ=Math.floor(this.depth/8),columns=maxX-minX+1;
  const buckets=new Map<number,Obstacle[]>(),large:Obstacle[]=[];
  for(const o of this.obstacles){
   if(!Number.isFinite(o.x+o.z+o.width+o.depth)||o.width<0||o.depth<0){large.push(o);continue;}
   const left=Math.max(minX,Math.floor((o.x-o.width/2)/4)),right=Math.min(maxX,Math.floor((o.x+o.width/2)/4)),bottom=Math.max(minZ,Math.floor((o.z-o.depth/2)/4)),top=Math.min(maxZ,Math.floor((o.z+o.depth/2)/4));
   // Huge walls/water stay in one overflow list instead of filling the grid.
   if((right-left+1)*(top-bottom+1)>64){large.push(o);continue;}
   for(let z=bottom;z<=top;z++)for(let x=left;x<=right;x++){const key=(z-minZ)*columns+x-minX,bucket=buckets.get(key);if(bucket)bucket.push(o);else buckets.set(key,[o]);}
  }
  return {count:this.obstacles.length,columns,minX,minZ,buckets,large};
 }
 visible(a:Point,b:Point,r=0){const accelerated=Navigation.backend?.visible?.(this,a,b,r);if(accelerated!==undefined&&accelerated!==null)return accelerated;const steps=Math.max(1,Math.ceil(Math.hypot(b.x-a.x,b.z-a.z)/.18));for(let i=0;i<=steps;i++){const t=i/steps;if(this.blockedAt(a.x+(b.x-a.x)*t,a.z+(b.z-a.z)*t,r))return false;}return true;}
 visibleMany(a:Point,targets:readonly Point[],r=0):Uint8Array {
  if(!targets.length)return new Uint8Array(0);
  const accelerated=Navigation.backend?.visibleMany?.(this,a,targets,r);if(accelerated)return accelerated;
  return Uint8Array.from(targets,p=>Number(this.visible(a,p,r)));
 }
 path(a:Point,b:Point):Point[]{
  if(this.visible(a,b,.32))return [{...a},{...b}];
  const step=1;
  const connector=(p:Point):Point|undefined=>{const accelerated=Navigation.backend?.connector?.(this,p);if(accelerated!==undefined&&accelerated!==null)return accelerated[0];const candidates:Point[]=[];for(let x=-3;x<=3;x++)for(let z=-3;z<=3;z++)candidates.push({x:(Math.round(p.x/step)+x)*step,z:(Math.round(p.z/step)+z)*step});return candidates.sort((u,v)=>Math.hypot(u.x-p.x,u.z-p.z)-Math.hypot(v.x-p.x,v.z-p.z)).find(v=>!this.blocked(v)&&this.visible(p,v,.32));};
  const startPoint=connector(a),endPoint=connector(b);if(!startPoint||!endPoint)return [];
  // The public route cache keeps its original coordinate keys. Search nodes
  // use numeric cells instead of allocating a string for every grid edge.
  const cachekey=`${startPoint.x},${startPoint.z}>${endPoint.x},${endPoint.z}`;
  const cached=this.cache.get(cachekey);if(cached){if(!cached.length)return [];if(this.visible(a,cached[0],.42)&&this.visible(cached[cached.length-1],b,.42))return [{...a},...cached,{...b}];}
  const points=this.searchGrid(startPoint,endPoint);
  if(this.cache.size>=200)this.cache.delete(this.cache.keys().next().value!);
  if(!points.length){this.cache.set(cachekey,[]);return [];}
  const route:Point[]=[{...a},...points,{...b}];
  const simplified=Navigation.backend?.simplify?.(this,route)??this.simplify(route);
  this.cache.set(cachekey,route.slice(1,-1));return simplified;
 }
 private simplify(route:Point[]):Point[]{
  const simplified=[route[0]];let i=0;while(i<route.length-1){let next=i+1;for(let j=i+2;j<route.length;j++){if(!this.visible(route[i],route[j],.42))break;next=j;}simplified.push(route[next]);i=next;}return simplified;
 }
 private searchGrid(startPoint:Point,endPoint:Point):Point[]{
  const accelerated=Navigation.backend?.search(this,startPoint,endPoint);if(accelerated!==undefined&&accelerated!==null)return accelerated;
  const step=1,halfWidth=Math.floor(this.width/2),halfDepth=Math.floor(this.depth/2),columns=halfWidth*2+1;
  const key=(p:Point)=>(p.z+halfDepth)*columns+p.x+halfWidth,start=key(startPoint),end=key(endPoint);
  // Keep coordinates and f-scores on each frontier node. Decoding string keys
  // and recomputing hypot for every frontier comparison caused second-long
  // guidance updates on Android, even though the searched grid was unchanged.
  const first:SearchNode={...startPoint,key:start,cost:0,score:Math.hypot(startPoint.x-endPoint.x,startPoint.z-endPoint.z),closed:false,index:-1,order:0};
  const open=new NavigationFrontier(),nodes=new Map<number,SearchNode>([[start,first]]);open.push(first);let found:SearchNode|undefined;
  // Collider footprints are immutable for this scene. Cache the eight directed
  // grid edges lazily (known + passable bits), using only two bytes per cell.
  const edges=this.gridEdges??=new Uint16Array(columns*(halfDepth*2+1));
  // Scratch coordinates never escape: only newly discovered search nodes copy them.
  const next:Point={x:0,z:0};
  for(let iterations=0;open.data.length&&iterations<20000;iterations++){
   const current=open.pop();if(current.key===end){found=current;break;}current.closed=true;
   const cell=(current.z+halfDepth)*columns+current.x+halfWidth;
   for(let direction=0;direction<NEIGHBOURS.length;direction++){
    const [dx,dz,cost]=NEIGHBOURS[direction];
    next.x=current.x+dx*step;next.z=current.z+dz*step;const k=key(next);let node=nodes.get(k);
    if(node?.closed)continue;
    const known=1<<(direction+8),passable=1<<direction;let mask=edges[cell];
    if(!(mask&known)){if(!this.blocked(next)&&this.visible(current,next,.42))mask|=passable;mask|=known;edges[cell]=mask;}
    if(!(mask&passable))continue;
    const nextCost=current.cost+cost*step;if(nextCost>=(node?.cost??Infinity))continue;
    if(!node){node={...next,key:k,cost:nextCost,score:0,closed:false,index:-1,order:nodes.size};nodes.set(k,node);}
    node.cost=nextCost;node.score=nextCost+Math.hypot(next.x-endPoint.x,next.z-endPoint.z);node.previous=current;
    if(node.index<0)open.push(node);else open.update(node);
   }
  }
  if(!found)return [];
  const route:Point[]=[];let node=found;while(node!==first){route.push({x:node.x,z:node.z});node=node.previous!;}route.push({...startPoint});route.reverse();return route;
 }
}
