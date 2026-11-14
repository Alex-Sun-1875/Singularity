import type {AreaDef,Obstacle,Point} from '../../../core/Contracts';
import {CAMPAIGN_TERRAIN} from '../data/CampaignTerrain';

/** All dimensions and elevations are metres in the area's local +X east/+Z north frame. */
export interface WaterDef extends Point {
  id:string; width:number; depth:number; y:number;
  kind:'river'|'harbor'|'canal'|'pool';
}
export interface BridgeDef extends Point {
  id:string; width:number; depth:number; axis:'x'|'z'; deckHeight:number;
  material:'stone'|'wood'; supports:Point[];
}
export interface BrokenBridgeDef extends BridgeDef {gapWidth:number}
/** Dry landform, never a water surface. y is the centre's bed elevation;
 * height(point) retains the surrounding analytic slope across the whole bed. */
export interface GorgeDef extends Point {
  id:string;width:number;depth:number;y:number;drop:number;bankWidth:number;
  kind:'gorge'|'dry-moat'|'quarry';walkable:boolean;
}
export interface RampDef {
  id:string; start:Point; end:Point; width:number; rise:number;
  startHeight:number; endHeight:number; material:'earth'|'stone'|'rock';
}
export interface TerrainDef {
  id:string;
  /** The actual walk surface AND ground mesh elevation, including intact decks.
   * Render bridge slab top at deckHeight; never add an invisible flat floor.
   * Water beds are below y and their blocked pieces leave intact bridge gaps. */
  height(point:Point):number;
  waters:WaterDef[]; bridges:BridgeDef[]; brokenBridges:BrokenBridgeDef[];
  gorges:GorgeDef[];
  ramps:RampDef[];
  /** Merge with area.obstacles for navigation and physical collision. Water is
   * owned here, so WorldData does not also include solid water boxes. */
  barriers:Obstacle[];
}

const smooth=(t:number)=>{t=Math.max(0,Math.min(1,t));return t*t*(3-2*t);};
const point=(x:number,z:number):Point=>({x,z});
type RampSpec=[string,number,number,number,number,number];
// These are broad landforms with a low plateau and a high plateau connected by
// a continuous dry ramp. Their gradients are analytic, not decorative noise.
const RAMP_SPECS:Record<string,RampSpec>={
  S03:['s03-cemetery-rise',0,-50,0,25,1.6],
  S04:['s04-bridge-bank',-12,0,32,0,3.4],
  S05:['s05-birch-ridge',-15,0,45,0,2.2],
  S06:['s06-dry-platform',0,-38,0,22,1],
  S07:['s07-mill-street',0,-40,0,30,1.2],
  S08:['s08-quarry-high-road',-18,0,42,0,4.2],
  S09:['s09-camp-terrace',0,-20,0,44,2.4],
  S10:['s10-north-wall-slope',0,18,0,58,2],
  S11:['s11-tower-ascent',0,0,0,40,5.2],
  S12:['s12-oath-court',0,-26,0,35,3.2],
  S13:['s13-quarry-ramp',-30,0,35,0,3.8],
  S14:['s14-manor-court',0,-35,0,38,1.4],
  S15:['s15-canal-dyke',-30,0,48,0,1.8],
  S16:['s16-highland-pass',-40,0,42,0,3.1],
  S17:['s17-cliff-platform',0,-30,0,40,4.4],
  S18:['s18-old-cart-slope',0,-30,0,34,1.1],
  S19:['s19-arrow-bank',-35,0,34,0,3],
  S20:['s20-iron-ridge',-35,0,32,0,4],
  'U1-01':['u101-loading-ramp',0,-20,0,34,1.4],
  'U1-02':['u102-dry-ramp',-25,-12,5,-12,5],
  'U1-03':['u103-extraction-ramp',-40,0,35,0,3],
  'U1-04':['u104-residential-terrace',0,-30,0,30,1.1],
  'U1-05':['u105-work-band',-30,0,40,0,1.6],
  'U2-01':['u201-dry-stair-approach',0,-30,0,25,1.2],
};
type WaterSpec=[string,number,number,number,number,WaterDef['kind']];
const WATER_SPECS:Record<string,WaterSpec[]>={
  S01:[['s01-stonebridge-river',14,0,6,144,'river']],
  S02:[['s02-south-harbor',-38,-28,22,18,'harbor']],
  S06:[['s06-reed-pool',43,0,12,22,'pool']],
  S07:[['s07-waterwheel-race',-56,31,12,28,'canal']],
  S11:[['s11-broken-bridge-gully',-10,-23,6,18,'river']],
  S14:[['s14-wet-wood-pool',-53,-44,12,10,'pool']],
  S15:[['s15-old-pump-canal',-47,-29,16,30,'canal']],
  'S01-T4':[['t4-warehouse-waterfront',-15,-11,8,8,'harbor']],
  'U2-01':[['u201-retreated-water',-42,-25,13,22,'canal']],
};

function bridge(id:string,x:number,z:number,width:number,depth:number,axis:BridgeDef['axis'],deckHeight:number,material:BridgeDef['material']):BridgeDef{
  const supports:Point[]=[];
  for(const a of [-1,1])for(const b of [-1,1])supports.push({x:x+a*width*.32,z:z+b*depth*.32});
  return {id,x,z,width,depth,axis,deckHeight,material,supports};
}
interface Rect extends Point {width:number;depth:number}
// Subtract the deck footprint from water collision, retaining separately
// addressable water strips on both sides rather than an invisible river wall.
function subtract(rect:Rect,cut:Rect):Rect[]{
  const left=Math.max(rect.x-rect.width/2,cut.x-cut.width/2),right=Math.min(rect.x+rect.width/2,cut.x+cut.width/2);
  const south=Math.max(rect.z-rect.depth/2,cut.z-cut.depth/2),north=Math.min(rect.z+rect.depth/2,cut.z+cut.depth/2);
  if(right<=left||north<=south)return [rect];
  const result:Rect[]=[];
  const add=(x1:number,z1:number,x2:number,z2:number)=>{if(x2-x1>.01&&z2-z1>.01)result.push({x:(x1+x2)/2,z:(z1+z2)/2,width:x2-x1,depth:z2-z1});};
  add(rect.x-rect.width/2,rect.z-rect.depth/2,left,rect.z+rect.depth/2);
  add(right,rect.z-rect.depth/2,rect.x+rect.width/2,rect.z+rect.depth/2);
  add(left,rect.z-rect.depth/2,right,south);
  add(left,north,right,rect.z+rect.depth/2);
  return result;
}

const cache=new WeakMap<AreaDef,TerrainDef>();
// Height is sampled by movement, collision, actors and effects. Keep bank
// interpolation outside that hot path instead of allocating a closure per bank.
const shore=(distance:number,half:number,width:number)=>1-smooth((distance-half)/width);
export function getTerrain(area:AreaDef):TerrainDef{
  const existing=cache.get(area);if(existing)return existing;
  const campaign=CAMPAIGN_TERRAIN[area.id],spec=RAMP_SPECS[area.id]??campaign?.ramp;
  const ramps:RampDef[]=spec?[{id:spec[0],start:point(spec[1],spec[2]),end:point(spec[3],spec[4]),rise:spec[5],startHeight:0,endHeight:spec[5],width:Math.max(area.width,area.depth),material:area.palette==='stone'||area.kind==='underground'?'rock':'earth'}]:[];
  const baseHeight=(p:Point):number=>{
    let height=0;
    for(let i=0;i<ramps.length;i++){
      const ramp=ramps[i],dx=ramp.end.x-ramp.start.x,dz=ramp.end.z-ramp.start.z;
      height=height+ramp.rise*smooth(((p.x-ramp.start.x)*dx+(p.z-ramp.start.z)*dz)/(dx*dx+dz*dz));
    }
    return height;
  };
  const waters:WaterDef[]=(WATER_SPECS[area.id]??campaign?.waters??[]).map(([id,x,z,width,depth,kind])=>({id,x,z,width,depth,kind,y:baseHeight({x,z})-.65}));
  const gorges:GorgeDef[]=(campaign?.gorges??[]).map(([id,x,z,width,depth,drop,kind,walkable])=>({id,x,z,width,depth,drop,kind,walkable,bankWidth:9,y:baseHeight({x,z})-drop}));
  const bridges:BridgeDef[]=area.id==='S01'?[bridge('s01-complete-stone-bridge',14,0,22,10,'x',0,'stone')]
    :area.id==='S02'?[bridge('s02-working-wooden-landing',-38,-28,36,6,'x',0,'wood')]
    :area.id==='S11'?[bridge('s11-repaired-gully-crossing',-10,-18,20,6,'x',0,'wood')]
    :(campaign?.bridges??[]).map(([id,x,z,width,depth,axis,material])=>bridge(id,x,z,width,depth,axis,baseHeight({x,z}),material));
  const brokenBridges:BrokenBridgeDef[]=area.id==='S11'?[{...bridge('s11-broken-old-stone-span',-10,-29,20,3,'x',0,'stone'),gapWidth:6}]:[];
  const barriers:Obstacle[]=waters.flatMap(water=>{
    let pieces:Rect[]=[water];
    for(const deck of bridges)pieces=pieces.flatMap(piece=>subtract(piece,deck));
    return pieces.map(piece=>({...piece,height:2.5,kind:'water'}));
  });
  // Reuse rectangle subtraction without changing the original water records.
  for(const gorge of gorges.filter(gorge=>!gorge.walkable)){
    let pieces:Rect[]=[gorge];
    for(const deck of bridges)pieces=pieces.flatMap(piece=>subtract(piece,deck));
    barriers.push(...pieces.map(piece=>({...piece,height:2.5,kind:'gorge'})));
  }
  const height=(p:Point):number=>{
    let elevation=baseHeight(p);
    for(let waterIndex=0;waterIndex<waters.length;waterIndex++){
      const water=waters[waterIndex];
      // 1.2m beds / 6m banks and 8m bridge approaches keep the combined
      // gradient below35degrees. Smooth endpoints meet flat deck tops exactly.
      let depression=shore(Math.abs(p.x-water.x),water.width/2,6)*shore(Math.abs(p.z-water.z),water.depth/2,6);
      for(let deckIndex=0;deckIndex<bridges.length;deckIndex++){
        const deck=bridges[deckIndex];
        if(Math.abs(deck.x-water.x)>water.width/2+deck.width/2||Math.abs(deck.z-water.z)>water.depth/2+deck.depth/2)continue;
        const across=deck.axis==='x'?Math.abs(p.z-deck.z):Math.abs(p.x-deck.x);
        const half=(deck.axis==='x'?deck.depth:deck.width)/2;
        depression*=smooth((across-half)/8);
      }
      elevation-=1.2*depression;
    }
    for(let gorgeIndex=0;gorgeIndex<gorges.length;gorgeIndex++){
      const gorge=gorges[gorgeIndex];
      let depression=shore(Math.abs(p.x-gorge.x),gorge.width/2,gorge.bankWidth)*shore(Math.abs(p.z-gorge.z),gorge.depth/2,gorge.bankWidth);
      for(let deckIndex=0;deckIndex<bridges.length;deckIndex++){
        const deck=bridges[deckIndex];
        if(Math.abs(deck.x-gorge.x)>gorge.width/2+deck.width/2||Math.abs(deck.z-gorge.z)>gorge.depth/2+deck.depth/2)continue;
        const across=deck.axis==='x'?Math.abs(p.z-deck.z):Math.abs(p.x-deck.x),half=(deck.axis==='x'?deck.depth:deck.width)/2;
        depression*=smooth((across-half)/8);
      }
      elevation-=gorge.drop*depression;
    }
    // Only expanded campaign decks flatten their inherited broad slope. This
    // leaves every original first-chapter height calculation unchanged.
    if(campaign?.bridges?.length)for(let deckIndex=0;deckIndex<bridges.length;deckIndex++){
      const deck=bridges[deckIndex];
      const along=deck.axis==='x'?Math.abs(p.x-deck.x):Math.abs(p.z-deck.z),across=deck.axis==='x'?Math.abs(p.z-deck.z):Math.abs(p.x-deck.x),halfLength=(deck.axis==='x'?deck.width:deck.depth)/2,halfWidth=(deck.axis==='x'?deck.depth:deck.width)/2;
      const weight=(1-smooth((along-halfLength)/8))*(1-smooth((across-halfWidth)/8));
      if(weight===1)elevation=deck.deckHeight;else if(weight>0)elevation+=(deck.deckHeight-elevation)*weight;
    }
    return elevation;
  };
  const terrain:TerrainDef={id:area.id,height,waters,bridges,brokenBridges,gorges,ramps,barriers};cache.set(area,terrain);return terrain;
}
