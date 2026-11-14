import {BlockInputEvents,Camera,isValid,Node} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import type {CampaignScene,CampaignBeat} from '../common/CinematicTypes';
import {CINEMATIC_STYLE as S,subtitlePages,subtitleSeconds} from '../common/CinematicLayout';
import {cinematicText} from '../locales';
import {onLocaleChanged} from '../../../shared/i18n/Localization';
import {CinematicSubtitles} from './CinematicSubtitles';
import {CinematicCamera} from './CinematicCamera';
import {CinematicCues} from './CinematicCues';

/** One presenter for every authored scene. Save/quest receipts stay in the director. */
export class CampaignPresentation {
 private view:CinematicSubtitles;private cues:CinematicCues;private shot:CinematicCamera;
 private scene?:CampaignScene;private beat=0;private page=0;private pages:string[]=[];
 private time=0;private pageTime=0;private entrance=0;private change=0;private exit=0;
 private leaving=false;private width=0;private height=0;private hidden=new Map<Node,boolean>();
 private stopLocale:()=>void;
 constructor(private hud:Hud,camera:Camera,private world:SceneBuilder,private game:GameSession,
  private done:(id:string)=>void,private sound:(cue:string)=>void,
  private army:(beat:CampaignBeat|undefined,time:number)=>void){
  this.shot=new CinematicCamera(camera,world);
  this.layout=()=>{
   this.restore();this.view?.destroy();this.width=hud.width;this.height=hud.height;
   this.view=new CinematicSubtitles(hud);this.view.root.addComponent(BlockInputEvents);
   this.cues=new CinematicCues(this.view.root,hud,camera,world,game);this.view.root.active=this.active;
   if(this.scene){this.reflow();this.conceal();}
  };
  this.layout();this.stopLocale=onLocaleChanged(()=>{if(this.scene){this.reflow();this.view.refreshControls();}});
 }
 private layout:()=>void;
 get active(){return !!this.scene;}
 private current(){return this.scene!.beats[this.beat];}
 private focus(){return this.current().focus??this.world.area.objects.find(o=>!!this.scene?.focusActor&&o.actor===this.scene.focusActor);}
 inspect(){return this.scene?{id:this.scene.id,beat:this.beat,page:this.page,pages:this.pages.length,time:this.time,
  title:cinematicText(this.scene.title),phase:this.leaving?'leaving':this.entrance<S.enter?'entering':'playing',subtitles:this.view.inspect()}:null;}
 private restore(){for(const[n,active]of this.hidden)if(isValid(n,true))n.active=active;this.hidden.clear();}
 private conceal(){for(const n of this.hud.root.children)if(n!==this.view.root&&isValid(n,true)){if(!this.hidden.has(n))this.hidden.set(n,n.active);n.active=false;}}
 suspend(){if(isValid(this.view.root,true))this.view.root.active=false;this.army(undefined,0);this.restore();}
 start(scene:CampaignScene){
  if(this.active)return;if(!isValid(this.view.root,true)||this.width!==this.hud.width||this.height!==this.hud.height)this.layout();
  this.scene=scene;this.beat=0;this.page=0;this.time=0;this.pageTime=0;this.entrance=0;this.change=0;this.exit=0;this.leaving=false;
  this.shot.begin(this.game.state.player,this.focus());this.conceal();this.view.root.active=true;this.showBeat();this.view.fade(this.hud.reducedMotion?1:0);
 }
 private reflow(){
  const l=this.view.layout,offset=this.pages.slice(0,this.page).join('').replace(/\n/g,'').length;
  this.pages=subtitlePages(cinematicText(this.current().text),l.captionWidth,S.caption*l.unit);
  let total=0;this.page=0;while(this.page<this.pages.length-1&&total+this.pages[this.page].replace(/\n/g,'').length<=offset){total+=this.pages[this.page].replace(/\n/g,'').length;this.page++;}
  this.display();
 }
 private display(){this.view.show(cinematicText(this.current().speaker),this.pages[this.page]);}
 private showBeat(){
  this.pages=[];this.page=0;this.pageTime=0;this.time=0;this.change=0;this.reflow();
  const b=this.current();if(b.cue)this.sound(b.cue);this.shot.frame(this.game.state.player,this.focus());
 }
 next(){
  if(!this.scene||this.leaving)return;
  if(this.page+1<this.pages.length){this.page++;this.pageTime=0;this.change=0;this.display();return;}
  if(this.beat+1<this.scene.beats.length){this.beat++;this.showBeat();return;}
  this.finish();
 }
 private finish(){if(this.scene&&!this.leaving){this.leaving=true;this.exit=0;this.army(undefined,0);this.cues.clear();}}
 private complete(){
  const id=this.scene?.id;if(!id)return;this.scene=undefined;this.leaving=false;this.shot.restore();this.view.root.active=false;this.restore();this.done(id);
 }
 handle(action:string){if(action==='campaign:next'){this.next();return true;}if(action==='campaign:skip'){this.finish();return true;}return this.active;}
 update(dt:number,allowed:boolean){
  if(!this.scene)return false;if(!allowed){this.suspend();return false;}
  if(!isValid(this.view.root,true)||this.width!==this.hud.width||this.height!==this.hud.height)this.layout();
  this.conceal();this.view.root.active=true;dt=Math.max(0,Math.min(.1,dt));
  if(this.leaving){this.exit+=dt;const amount=this.hud.reducedMotion?1:Math.min(1,this.exit/S.exit);this.view.fade(1-amount);this.shot.restore(amount);if(amount>=1)this.complete();return true;}
  this.entrance+=dt;this.change+=dt;const fade=this.hud.reducedMotion?1:Math.min(1,this.entrance/S.enter);
  this.view.fade(fade,this.hud.reducedMotion?1:Math.min(1,this.change/S.change));this.shot.update(dt,this.hud.reducedMotion);
  const b=this.current();this.army(b,this.time);this.cues.draw(b,this.time);this.time+=dt;this.pageTime+=dt;
  if(this.pageTime>=subtitleSeconds(this.pages[this.page],b.seconds,this.pages.length))this.next();return true;
 }
 destroy(){this.stopLocale();this.army(undefined,0);if(this.scene)this.shot.restore();this.scene=undefined;this.restore();this.view?.destroy();}
}
