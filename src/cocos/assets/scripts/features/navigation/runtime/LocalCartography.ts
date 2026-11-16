import {Color,Graphics} from 'cc';
import {platformStorage} from '../../../platform/PlatformStorage';
import type {AreaDef,Obstacle,Point} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import {AREAS} from '../../world/data/WorldData';
import {INN_OPENING} from '../../world/data/SceneDressing';
import {getTerrain} from '../../world/runtime/Terrain';
import {Navigation} from './Navigation';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';

type Memory={cells:Map<string,Set<string>>;lastArea:string;last:Point;lastWrite:number;dirty:boolean};
const CELL=3;
const hex=(value:string)=>new Color().fromHEX(value);
// Natural terrain stays distinct from the UI: green canopy, warm earth and neutral grey masonry.
const COLORS={floor:hex('#7c858e'),forest:hex('#3e6852'),earth:hex('#786e65'),wood:hex('#746a63'),stone:hex('#78858c'),wall:hex('#b0bec6'),roof:hex('#4b5964'),line:hex('#263440'),water:hex('#2c6174'),bridge:hex('#a0a7ab'),fog:new Color(C.dark.r,C.dark.g,C.dark.b,250)};
const FOG_SUBDIVISIONS=4;
// The centre is unrevealed, leaving at most 255 nonempty neighbour patterns.
// Cache unrounded coverage so every opacity keeps the original alpha rounding.
const fogFeathers=new Map<number,Float64Array>();
const fogFeather=(mask:number):Float64Array=>{
 let values=fogFeathers.get(mask);if(values)return values;
 values=new Float64Array(FOG_SUBDIVISIONS**2);
 for(let sx=0;sx<FOG_SUBDIVISIONS;sx++)for(let sz=0;sz<FOG_SUBDIVISIONS;sz++){
  const px=(sx+.5)/FOG_SUBDIVISIONS,pz=(sz+.5)/FOG_SUBDIVISIONS;let distance=Infinity,bit=1;
  for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++,bit<<=1)if(mask&bit)distance=Math.min(distance,Math.hypot(Math.max(0,Math.abs(px-dx-.5)-.5),Math.max(0,Math.abs(pz-dz-.5)-.5)));
  values[sx*FOG_SUBDIVISIONS+sz]=Math.min(250,distance*330);
 }
 fogFeathers.set(mask,values);return values;
};

/** Cartography is derived from the same metre coordinates as the walk surface.
 * Exploration is cosmetic, keyed by the journey seed; it never writes game rules. */
export class LocalCartography {
 static current:GameSession|null=null;
 private static memories=new WeakMap<GameSession,Memory>();
 private static vision=new WeakMap<AreaDef,Navigation>();
 private static layouts=new Map<string,Obstacle[]>();
 static setLayout(areaId:string,obstacles:readonly Obstacle[]):void{
  this.layouts.set(areaId,obstacles.map(o=>({...o})));const area=AREAS[areaId];if(area)this.vision.set(area,new Navigation(area.width,area.depth,this.obstacles(area).filter(o=>o.height>=1.5),true));
 }
 static obstacles(area:AreaDef):Obstacle[]{
  const extras=this.layouts.get(area.id)??(area.id==='S01-T1'?INN_OPENING.map(o=>({x:o.x,z:o.z,width:o.width,depth:o.depth,height:o.height,kind:o.key})):[]);
  return [...area.obstacles,...extras];
 }
 private static memory(game:GameSession):Memory{
  let memory=this.memories.get(game);if(memory)return memory;
  memory={cells:new Map(),lastArea:'',last:{x:Infinity,z:Infinity},lastWrite:0,dirty:false};
  try{const data=JSON.parse(platformStorage.getItem('sword-fire-chart:'+game.state.seed)||'{}');
   for(const [id,values]of Object.entries(data))if(AREAS[id]&&Array.isArray(values)&&values.length<=10000){
    if(values.every(v=>typeof v==='number'&&Number.isInteger(v))){const a=AREAS[id],x0=Math.floor(-a.width/2/CELL),z0=Math.floor(-a.depth/2/CELL),nx=Math.ceil(a.width/2/CELL)-x0,nz=Math.ceil(a.depth/2/CELL)-z0,cells=new Set<string>();if(values.length!==Math.ceil(nx*nz/32))continue;for(let i=0;i<nx*nz;i++)if((values[Math.floor(i/32)]>>>(i%32))&1)cells.add((x0+i%nx)+','+(z0+Math.floor(i/nx)));memory.cells.set(id,cells);}
    else memory.cells.set(id,new Set(values.filter(v=>typeof v==='string'&&/^-?\d+,-?\d+$/.test(v))));
   }
  }catch{/* A cosmetic chart cannot prevent a valid journey from loading. */}
  this.memories.set(game,memory);return memory;
 }
 static track(game:GameSession):boolean{
  this.current=game;const memory=this.memory(game),s=game.state,area=AREAS[s.area];if(!area)return false;
  if(memory.lastArea===area.id&&Math.hypot(s.player.x-memory.last.x,s.player.z-memory.last.z)<1.2)return false;
  memory.lastArea=area.id;memory.last={x:s.player.x,z:s.player.z};
  let visible=this.vision.get(area);if(!visible){visible=new Navigation(area.width,area.depth,this.obstacles(area).filter(o=>o.height>=1.5),true);this.vision.set(area,visible);}
  let cells=memory.cells.get(area.id);if(!cells){cells=new Set();memory.cells.set(area.id,cells);}
  const radius=area.kind==='interior'?13:17,cx=Math.floor(s.player.x/CELL),cz=Math.floor(s.player.z/CELL),r=Math.ceil(radius/CELL),candidates:Point[]=[],keys:string[]=[];let changed=false;
  for(let x=cx-r;x<=cx+r;x++)for(let z=cz-r;z<=cz+r;z++){
   const p={x:(x+.5)*CELL,z:(z+.5)*CELL},key=x+','+z;if(cells.has(key)||Math.abs(p.x)>area.width/2+CELL||Math.abs(p.z)>area.depth/2+CELL||Math.hypot(p.x-s.player.x,p.z-s.player.z)>radius)continue;
   candidates.push(p);keys.push(key);
  }
  const visibility=visible.visibleMany(s.player,candidates);for(let i=0;i<candidates.length;i++)if(visibility[i]){cells.add(keys[i]);changed=true;}
  memory.dirty ||= changed;if(memory.dirty&&Date.now()-memory.lastWrite>4500)this.flush(game);return changed;
 }
 static flush(game=this.current):void{
  if(!game)return;const memory=this.memory(game);if(!memory.dirty)return;
  try{
   const data:Record<string,number[]>={};for(const [id,cells]of memory.cells){const a=AREAS[id],x0=Math.floor(-a.width/2/CELL),z0=Math.floor(-a.depth/2/CELL),nx=Math.ceil(a.width/2/CELL)-x0,nz=Math.ceil(a.depth/2/CELL)-z0,words=new Array(Math.ceil(nx*nz/32)).fill(0);for(const key of cells){const[x,z]=key.split(',').map(Number),ix=x-x0,iz=z-z0;if(ix<0||ix>=nx||iz<0||iz>=nz)continue;const i=iz*nx+ix;words[Math.floor(i/32)]|=1<<(i%32);}data[id]=words;}
   const key='sword-fire-chart:'+game.state.seed,old=JSON.parse(platformStorage.getItem('sword-fire-chart-index')||'[]'),index=Array.isArray(old)?old.filter(k=>typeof k==='string'&&/^sword-fire-chart:\d+$/.test(k)&&k!==key):[];
   platformStorage.setItem(key,JSON.stringify(data));for(const stale of index.slice(0,-2))platformStorage.removeItem(stale);platformStorage.setItem('sword-fire-chart-index',JSON.stringify(index.slice(-2).concat(key)));memory.dirty=false;memory.lastWrite=Date.now();
  }catch{/* Keep the in-memory chart when browser storage is unavailable. */}
 }
 static revealed(area:string,p:Point,game=this.current):boolean{
  if(!game)return false;const cells=this.memory(game).cells.get(area);return !!cells?.has(Math.floor(p.x/CELL)+','+Math.floor(p.z/CELL));
 }
 static canSee(area:string,from:Point,to:Point):boolean{return this.vision.get(AREAS[area])?.visible(from,to)??false;}
 static drawTerrain(g:Graphics,area:AreaDef,scale:number,ox:number,oy:number):void{
  const terrain=getTerrain(area),step=area.kind==='interior'?2:6;
  const point=(p:Point)=>({x:ox+p.x*scale,y:oy+p.z*scale});
  const rect=(p:Point,w:number,d:number,fill:Color,stroke?:Color)=>{const q=point(p);g.fillColor=fill;g.rect(q.x-w*scale/2,q.y-d*scale/2,w*scale,d*scale);g.fill();if(stroke){g.strokeColor=stroke;g.lineWidth=Math.max(.7,scale*.08);g.stroke();}};
  const base=area.kind==='interior'?COLORS.wood:area.kind==='underground'?COLORS.stone:area.palette==='forest'?COLORS.forest:COLORS.earth;
  for(let x=-area.width/2;x<area.width/2;x+=step)for(let z=-area.depth/2;z<area.depth/2;z+=step){
   const w=Math.min(step,area.width/2-x),d=Math.min(step,area.depth/2-z),h=terrain.height({x,z}),grain=Math.sin(x*7.31+z*3.13)*3+Math.min(12,h*2),c=new Color(Math.max(0,base.r+grain),Math.max(0,base.g+grain),Math.max(0,base.b+grain),255);
   rect({x:x+w/2,z:z+d/2},w,d,c);if(area.kind==='interior'){g.strokeColor=new Color(C.dark.r,C.dark.g,C.dark.b,50);g.lineWidth=.6;g.stroke();}
  }
  for(const water of terrain.waters){rect(water,water.width,water.depth,COLORS.water);const p=point(water);g.strokeColor=new Color(C.route.r,C.route.g,C.route.b,70);g.lineWidth=.7;for(let n=-2;n<=2;n++){const y=p.y+n*water.depth*scale/6;g.moveTo(p.x-water.width*scale*.4,y);g.lineTo(p.x+water.width*scale*.4,y);g.stroke();}}
  for(const bridge of terrain.bridges)rect(bridge,bridge.width,bridge.depth,COLORS.bridge,COLORS.line);
  for(const obstacle of this.obstacles(area)){
   if(obstacle.kind==='building')continue;
   const wall=obstacle.kind==='wall'||obstacle.height>2.8,tree=/tree/i.test(obstacle.kind??''),rock=/rock|cliff|rubble/i.test(obstacle.kind??'');
   const p=point(obstacle);if(tree||rock){g.fillColor=tree?hex('#285340'):hex('#85929a');g.ellipse(p.x,p.y,Math.max(1.3,obstacle.width*scale*.55),Math.max(1.3,obstacle.depth*scale*.55));g.fill();g.strokeColor=COLORS.line;g.lineWidth=.6;g.stroke();}
   else if(/round-table|stool|barrel/.test(obstacle.kind??'')){g.fillColor=hex('#918279');g.ellipse(p.x,p.y,obstacle.width*scale/2,obstacle.depth*scale/2);g.fill();g.strokeColor=COLORS.line;g.lineWidth=.8;g.stroke();}
   else rect(obstacle,obstacle.width,obstacle.depth,wall?COLORS.wall:COLORS.roof,COLORS.line);
  }
  for(const b of area.buildings){
   const p=point(b),angle=(b.rotation??0)*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle),corners=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([x,z])=>({x:p.x+(x*b.width/2*c+z*b.depth/2*s)*scale,y:p.y+(-x*b.width/2*s+z*b.depth/2*c)*scale}));
   g.fillColor=COLORS.roof;g.strokeColor=COLORS.wall;g.lineWidth=Math.max(.8,scale*.15);g.moveTo(corners[0].x,corners[0].y);for(const q of corners.slice(1))g.lineTo(q.x,q.y);g.close();g.fill();g.stroke();
   g.strokeColor=new Color(C.muted.r,C.muted.g,C.muted.b,170);g.moveTo(p.x-b.width*scale*.35*c,p.y+b.width*scale*.35*s);g.lineTo(p.x+b.width*scale*.35*c,p.y-b.width*scale*.35*s);g.stroke();
  }
 }
 static drawFog(g:Graphics,area:AreaDef,scale:number,ox:number,oy:number,game=this.current,opacity=1):void{
  const alpha=Math.max(0,Math.min(1,opacity)),cells=game?this.memory(game).cells.get(area.id):undefined;
  const frontier:{x:number;z:number;mask:number}[]=[];
  const minX=Math.floor(-area.width/2/CELL),maxX=Math.ceil(area.width/2/CELL),minZ=Math.floor(-area.depth/2/CELL),maxZ=Math.ceil(area.depth/2/CELL);
  // Include the one-cell border: discovery just beyond the region still
  // feathers its edge. Query each original Set key once, rather than nine
  // times per hidden cell, without changing legacy key interpretation.
  const stride=maxX-minX+2,rows=maxZ-minZ+2,grid=new Uint8Array(stride*rows);
  if(cells?.size)for(let z=minZ-1;z<=maxZ;z++)for(let x=minX-1;x<=maxX;x++)grid[(z-minZ+1)*stride+x-minX+1]=Number(cells.has(x+','+z));
  g.fillColor=new Color(COLORS.fog.r,COLORS.fog.g,COLORS.fog.b,Math.round(COLORS.fog.a*alpha));let rectangles=0;
  // Merge opaque runs; Graphics retains much less geometry while walking reveals new cells.
  for(let z=minZ;z<maxZ;z++){
   let start:number|undefined;
   for(let x=minX;x<=maxX;x++){
    let opaque=false;
    const index=(z-minZ+1)*stride+x-minX+1;
    if(x<maxX&&!grid[index]){
     let mask=0,bit=1;for(let dx=-1;dx<=1;dx++)for(let dz=-1;dz<=1;dz++,bit<<=1)if(grid[index+dx+dz*stride])mask|=bit;
     opaque=!mask;if(mask)frontier.push({x,z,mask});
    }
    if(opaque){start??=x;continue;}
    if(start!==undefined){g.rect(ox+start*CELL*scale,oy+z*CELL*scale,(x-start)*CELL*scale+.5,CELL*scale+.5);rectangles++;start=undefined;}
   }
  }
  if(rectangles)g.fill();
  // Keep the approved feathered frontier; batch equal alpha instead of filling each tile.
  const shades=new Map<number,number[]>(),sub=FOG_SUBDIVISIONS;
  for(const {x,z,mask}of frontier){const feather=fogFeather(mask);for(let sx=0;sx<sub;sx++)for(let sz=0;sz<sub;sz++){
   const shade=Math.round(feather[sx*sub+sz]*alpha);let positions=shades.get(shade);if(!positions){positions=[];shades.set(shade,positions);}positions.push(x+sx/sub,z+sz/sub);
  }
  }
  for(const [shade,positions]of shades){g.fillColor=new Color(C.dark.r,C.dark.g,C.dark.b,shade);for(let i=0;i<positions.length;i+=2)g.rect(ox+positions[i]*CELL*scale,oy+positions[i+1]*CELL*scale,CELL/sub*scale+.5,CELL/sub*scale+.5);g.fill();}
 }
 static kind(object:{action:string;actor?:string;merchant?:string}):'quest'|'npc'|'merchant'|'checkpoint'|'place'{return object.merchant?'merchant':object.action==='checkpoint'?'checkpoint':['offer','recover','meeting','finish','captain_gate','campaign_event','growing_scene','growing_rematch','journey_board','journey_task'].includes(object.action)?'quest':object.actor?'npc':'place';}
}
