import type {Camera,Node} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {GameEvent} from '../../../core/Contracts';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {Actors} from './Actors';
import {FlatActors} from './FlatActors';
import type {CampaignBeat} from '../../cinematics/data/CampaignScenes';

/** Reuse the native skinned hero inside the existing painted world and cast. */
export class Player3DActors {
 readonly player:Actors;
 readonly cast:FlatActors;
 private ownsPlayer=true;private ready=false;
 set reducedMotion(value:boolean){this.player.reducedMotion=value;this.cast.reducedMotion=value;}
 get reducedMotion(){return this.cast.reducedMotion;}
 constructor(scene:Node,world:SceneBuilder,camera:Camera,player?:Actors){
  this.player=player??new Actors(scene,world,true);if(player)this.player.adoptWorld(world);
  this.cast=new FlatActors(scene,world,camera,true);
 }
 takePlayer():Actors|undefined{if(!this.ready||!this.ownsPlayer)return;this.player.detachPlayer();this.ownsPlayer=false;return this.player;}
 async build(game:GameSession,onProgress?:(done:number,total:number)=>void){
  this.player.setStartingWeapon(game.state.equipment.weapon);
  let hero=0,done=0,total=0;
  const progress=()=>onProgress?.(done+hero,total+1);
  await Promise.all([
   (this.player.playerModel()?this.player.preparePlayer(game):this.player.create('player','raphael',game.state.player.x,game.state.player.z)).then(()=>{hero=1;progress();}),
   this.cast.build(game,(d,t)=>{done=d;total=t;progress();}),
  ]);
  this.player.update(game,0,false);this.ready=true;onProgress?.(total+1,total+1);
 }
 preparePlayerWeapon(id:string){return this.player.preparePlayerWeapon(id);}
 update(game:GameSession,dt:number,moving:boolean,paused=false,moveAmount=1){if(!this.ready)return;this.cast.update(game,dt,moving,paused,moveAmount);if(this.ownsPlayer)this.player.update(game,dt,moving,paused,moveAmount);}
 onCombatEvents(events:readonly GameEvent[],time:number){this.cast.onCombatEvents(events,time);this.player.onCombatEvents(events,time);}
 playerPresentation(){return this.player.playerPresentation();}
 playerModel(){return this.player.playerModel();}
 enemyHeadPoint(id:string){return this.cast.enemyHeadPoint(id);}
 presentCampaign(beat:CampaignBeat|undefined,time:number,game:GameSession){this.cast.presentCampaign(beat,time,game);}
 inspect(){return [...this.player.inspect(),...this.cast.inspect()];}
 inspectTextureOwnership(){return this.cast.inspectTextureOwnership();}
 destroy(){this.ready=false;this.cast.destroy();if(this.ownsPlayer)this.player.destroy();}
}
