import {Color,Node,PointLight,Vec3,ParticleSystem} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from './SceneBuilder';
import {VfxAssets,constant} from '../../../shared/assets/VfxAssets';

export type PracticalSource={node:Node;kind:'lantern'|'candlestick'|'firepit';height:number};

/** Native environmental light/particles only; never changes navigation or state. */
export class EnvironmentPresentation {
 private root:Node;
 private sources:PracticalSource[]=[];private existing:PointLight[]=[];private pools:{node:Node;light:PointLight;flame:Node;system:ParticleSystem;source:PracticalSource}[]=[];private lightTime=-100;private lightPosition={x:Infinity,z:Infinity};
 constructor(private readonly world:SceneBuilder,sources:PracticalSource[]){
  this.root=new Node('EnvironmentalPresentation');world.root.addChild(this.root);
  this.existing=world.root.getComponentsInChildren(PointLight);const budget=Math.max(0,6-this.existing.length);
  this.sources=sources.filter(source=>!this.existing.some(light=>Vec3.distance(light.node.worldPosition,source.node.worldPosition)<2.2));
  const start=world.area.spawn;
  for(const source of this.sources.slice().sort((a,b)=>Math.hypot(a.node.worldPosition.x-start.x,a.node.worldPosition.z-start.z)-Math.hypot(b.node.worldPosition.x-start.x,b.node.worldPosition.z-start.z)).slice(0,budget)){
   const node=new Node('PracticalLight');this.root.addChild(node);const light=node.addComponent(PointLight),flame=VfxAssets.emitter('flame',this.root);flame.system.capacity=20;
   const pool={node,light,flame:flame.node,system:flame.system,source};this.pools.push(pool);this.placeLight(pool,source);
  }
 }
 private placeLight(pool:{node:Node;light:PointLight;flame:Node;system:ParticleSystem;source:PracticalSource},source:PracticalSource):void {
  const p=source.node.worldPosition,fire=source.kind==='firepit',candle=source.kind==='candlestick',height=fire?source.height*.8:source.height*(candle?.96:.6),x=p.x,y=p.y+height,z=p.z;
  pool.node.name='PracticalLight:'+source.kind;pool.node.setPosition(x,y+.16,z);pool.node.active=true;
  // Flux controls the inverse-square hotspot next to a wall; range alone only
  // trims distant spill and leaves the clipped white stone around lanterns.
  const light=pool.light;light.color=fire?new Color(255,182,114):new Color(255,199,132);light.range=fire?4:candle?1.8:3;light.term=0;light.luminousFlux=(fire?160:candle?35:85)*(this.world.area.kind==='underground'?.6:1);
  pool.flame.name='PracticalFlame:'+source.kind;pool.flame.setPosition(x,y,z);pool.flame.setScale(fire?.55:candle?.095:.17,fire?.7:candle?.13:.23,fire?.55:candle?.095:.17);pool.flame.active=true;constant(pool.system.rateOverTime,fire?13:6);if(pool.source!==source){pool.system.stop();pool.system.play();}pool.source=source;
 }
 private nearbyLights(game:GameSession):void {
  const p=game.state.player;if(game.state.time-this.lightTime<.35&&Math.hypot(p.x-this.lightPosition.x,p.z-this.lightPosition.z)<3)return;
  this.lightTime=game.state.time;this.lightPosition={x:p.x,z:p.z};const chosen:PracticalSource[]=[];
  for(const source of this.sources.slice().sort((a,b)=>Math.hypot(a.node.worldPosition.x-p.x,a.node.worldPosition.z-p.z)-Math.hypot(b.node.worldPosition.x-p.x,b.node.worldPosition.z-p.z))){
   if(!source.node.isValid||chosen.some(other=>Vec3.distance(other.node.worldPosition,source.node.worldPosition)<2.6))continue;chosen.push(source);if(chosen.length===this.pools.length)break;
  }
  this.pools.forEach((pool,index)=>{const source=chosen[index];if(source){this.placeLight(pool,source);if(!pool.system.isPlaying)pool.system.play();}else{pool.node.active=false;pool.flame.active=false;}});
 }

 update(game:GameSession):void {
  // Character heading belongs to MiniMap; combat ranges belong to Effects.
  this.nearbyLights(game);
 }
 destroy():void {this.root.destroy();}
}
