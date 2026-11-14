import type {Point} from '../../../core/Contracts';
import type {NavigationSearchBackend,NavigationSearchMap} from './NavigationSearchBackend';

interface NavigationKernel {
 memory:WebAssembly.Memory;
 api_version():number;
 create_context(slot:number,width:number,depth:number,count:number):void;
 obstacles_pointer(slot:number):number;
 prepare_context(slot:number):void;
 route_pointer(slot:number):number;
 search_context(slot:number,start:number,end:number):number;
 clear_context(slot:number):void;
 input_pointer(slot:number,count:number):number;
 points_pointer(slot:number):number;
 visible_context(slot:number,ax:number,az:number,bx:number,bz:number,radius:number):number;
 visibility_context(slot:number,x:number,z:number,count:number,radius:number):void;
 visibility_pointer(slot:number):number;
 connector_context(slot:number,x:number,z:number):number;
 simplify_context(slot:number,count:number):number;
}
type Context={slot:number;columns:number;rows:number;count:number;used:number};
const CONTEXT_LIMIT=4,MAX_CELLS=65536,MAX_OBSTACLES=4096;

/** One synchronous call per grid search. At most four immutable maps stay in
 * linear memory. No graph uploads/downloads occur on an existing context. */
export class NavigationWasmBackend implements NavigationSearchBackend {
 private readonly kernel:NavigationKernel;
 private contexts=new Map<NavigationSearchMap,Context>();
 private clock=0;private busy=false;private failed=false;
 private uploads=0;private uploadedBytes=0;private searches=0;
 private visibilityQueries=0;private batchTargets=0;private connectors=0;private simplifications=0;
 constructor(exports:WebAssembly.Exports,private readonly failedOnce:(error:unknown)=>void=()=>{}){
  const kernel=exports as unknown as NavigationKernel;
  for(const name of ['api_version','create_context','obstacles_pointer','prepare_context','route_pointer','search_context','clear_context','input_pointer','points_pointer','visible_context','visibility_context','visibility_pointer','connector_context','simplify_context']as const)if(typeof kernel[name]!=='function')throw new Error('Navigation WASM export missing: '+name);
  if(!kernel.memory?.buffer||kernel.api_version()!==3)throw new Error('Navigation WASM ABI mismatch');
  this.kernel=kernel;
 }
 private context(map:NavigationSearchMap):Context|null {
  const existing=this.contexts.get(map);
  if(existing?.count===map.obstacles.length){existing.used=++this.clock;return existing;}
  if(existing)this.release(map);
  if(!Number.isFinite(map.width+map.depth)||map.width<=0||map.depth<=0||map.width>1024||map.depth>1024||map.obstacles.length>MAX_OBSTACLES)return null;
  const columns=Math.floor(map.width/2)*2+1,rows=Math.floor(map.depth/2)*2+1;
  if(columns*rows>MAX_CELLS)return null;
  for(let i=0;i<map.obstacles.length;i++){
   const o=map.obstacles[i];
   if(!Number.isFinite(o.x+o.z+o.width+o.depth)||o.width<0||o.depth<0||Math.max(Math.abs(o.x),Math.abs(o.z),o.width,o.depth)>1e6)return null;
  }
  let slot=0;
  if(this.contexts.size===CONTEXT_LIMIT){
   let oldest:NavigationSearchMap|undefined,age=Infinity;
   for(const [key,value]of this.contexts)if(value.used<age){oldest=key;age=value.used;slot=value.slot;}
   this.release(oldest!);
  }else{
   const used=new Set(Array.from(this.contexts.values(),entry=>entry.slot));while(used.has(slot))slot++;
  }
  const k=this.kernel;
  k.create_context(slot,map.width,map.depth,map.obstacles.length);
  const input=new Float64Array(k.memory.buffer,k.obstacles_pointer(slot),map.obstacles.length*4);
  for(let i=0;i<map.obstacles.length;i++){const o=map.obstacles[i],at=i*4;input[at]=o.x;input[at+1]=o.z;input[at+2]=o.width;input[at+3]=o.depth;}
  k.prepare_context(slot);
  const context={slot,columns,rows,count:map.obstacles.length,used:++this.clock};
  this.contexts.set(map,context);this.uploads++;this.uploadedBytes+=map.obstacles.length*32;return context;
 }
 private run<T>(map:NavigationSearchMap,operation:(context:Context)=>T):T|null {
  if(this.failed||this.busy)return null;this.busy=true;
  try{const context=this.context(map);return context?operation(context):null;}
  catch(error){this.failed=true;this.reset();try{this.failedOnce(error);}catch{/* Diagnostics cannot interrupt rules. */}return null;}
  finally{this.busy=false;}
 }
 private valid(x:number,z:number,radius=0){return Number.isFinite(x+z+radius)&&Math.max(Math.abs(x),Math.abs(z))<=1e6&&radius>=0&&radius<=1024;}
 private input(slot:number,points:readonly Point[]){
  const pointer=this.kernel.input_pointer(slot,points.length),values=new Float64Array(this.kernel.memory.buffer,pointer,points.length*2);
  for(let i=0;i<points.length;i++){values[i*2]=points[i].x;values[i*2+1]=points[i].z;}
 }
 private points(slot:number,count:number):Point[]{
  if(count<0||count>MAX_CELLS+2)throw new Error('Navigation WASM returned invalid points');
  const values=new Float64Array(this.kernel.memory.buffer,this.kernel.points_pointer(slot),count*2),points:Point[]=[];
  for(let i=0;i<count;i++){const x=values[i*2],z=values[i*2+1];if(!this.valid(x,z))throw new Error('Navigation WASM returned invalid coordinates');points.push({x,z});}return points;
 }
 visible(map:NavigationSearchMap,start:Point,end:Point,radius:number):boolean|null {
  if(!this.valid(start.x,start.z,radius)||!this.valid(end.x,end.z,radius))return null;
  return this.run(map,({slot})=>{this.visibilityQueries++;return !!this.kernel.visible_context(slot,start.x,start.z,end.x,end.z,radius);});
 }
 visibleMany(map:NavigationSearchMap,start:Point,targets:readonly Point[],radius:number):Uint8Array|null {
  if(targets.length>4096||!this.valid(start.x,start.z,radius)||targets.some(p=>!this.valid(p.x,p.z,radius)))return null;
  return this.run(map,({slot})=>{
   this.input(slot,targets);this.kernel.visibility_context(slot,start.x,start.z,targets.length,radius);this.batchTargets+=targets.length;
   return new Uint8Array(this.kernel.memory.buffer,this.kernel.visibility_pointer(slot),targets.length).slice();
  });
 }
 connector(map:NavigationSearchMap,point:Point):Point[]|null {
  if(!this.valid(point.x,point.z))return null;
  return this.run(map,({slot})=>{this.connectors++;return this.points(slot,this.kernel.connector_context(slot,point.x,point.z));});
 }
 simplify(map:NavigationSearchMap,route:readonly Point[]):Point[]|null {
  if(route.length>MAX_CELLS+2||route.some(p=>!this.valid(p.x,p.z)))return null;
  return this.run(map,({slot})=>{
   this.input(slot,route);this.simplifications++;const count=this.kernel.simplify_context(slot,route.length);
   if(count>route.length)throw new Error('Navigation WASM returned invalid simplified length');
   const indices=new Int32Array(this.kernel.memory.buffer,this.kernel.route_pointer(slot),count),result:Point[]=[];
   for(const index of indices){if(index<0||index>=route.length)throw new Error('Navigation WASM returned invalid simplified index');result.push(route[index]);}return result;
  });
 }
 search(map:NavigationSearchMap,start:Point,end:Point):Point[]|null {
  return this.run(map,({columns,rows,slot})=>{
   const halfWidth=(columns-1)/2,halfDepth=(rows-1)/2;
   if(!Number.isInteger(start.x)||!Number.isInteger(start.z)||!Number.isInteger(end.x)||!Number.isInteger(end.z)||Math.max(Math.abs(start.x),Math.abs(end.x))>halfWidth||Math.max(Math.abs(start.z),Math.abs(end.z))>halfDepth)return null;
   const first=(start.z+halfDepth)*columns+start.x+halfWidth,last=(end.z+halfDepth)*columns+end.x+halfWidth;
   const count=this.kernel.search_context(slot,first,last);this.searches++;
   if(!count)return [];
   if(count>columns*rows)throw new Error('Navigation WASM returned an invalid route size');
   const cells=new Int32Array(this.kernel.memory.buffer,this.kernel.route_pointer(slot),count),route:Point[]=[{...start}];
   if(cells[0]!==first||cells[count-1]!==last)throw new Error('Navigation WASM returned invalid endpoints');
   for(let i=1;i<count;i++){const cell=cells[i];if(cell<0||cell>=columns*rows)throw new Error('Navigation WASM returned an invalid cell');route.push({x:cell%columns-halfWidth,z:Math.floor(cell/columns)-halfDepth});}
   return route;
  });
 }
 release(map:NavigationSearchMap):void {
  const entry=this.contexts.get(map);if(!entry)return;
  this.contexts.delete(map);try{this.kernel.clear_context(entry.slot);}catch{this.failed=true;}
 }
 reset():void {
  this.contexts.clear();for(let slot=0;slot<CONTEXT_LIMIT;slot++)try{this.kernel.clear_context(slot);}catch{this.failed=true;}
 }
 inspect(){return{ready:!this.failed,contexts:this.contexts.size,uploads:this.uploads,uploadedBytes:this.uploadedBytes,searches:this.searches,visibilityQueries:this.visibilityQueries,batchTargets:this.batchTargets,connectors:this.connectors,simplifications:this.simplifications,memoryBytes:this.kernel.memory.buffer.byteLength};}
}
