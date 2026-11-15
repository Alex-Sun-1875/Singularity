import {BlockInputEvents,ButtonComponent as Button,Label,Node,UITransform,Vec2} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {BossEntry} from '../common/BossDirectory';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {applyRpgFont} from '../../../shared/ui/RpgFont';
import {bossPortrait} from './BossPresentation';
import {bossText as tr} from '../locales/bosses';

/** Only the 48px travel action captures input; the frame and captions are passive. */
export class BossNotice {
 private root:Node|null=null;private travel:Node|null=null;private body:Node|null=null;
 private stamp='';private key='';private unit=1;
 constructor(private readonly hud:Hud){}
 mount(unit:number){
  this.unit=unit;this.stamp='';this.root=this.hud.node('BossSpawnNotice',this.hud.root,0,0,310*unit,52*unit);
  UiSkin.panel(this.root,310*unit,52*unit,C.inset,'panel',false,.75*unit);
  this.body=this.hud.node('BossNoticeIdentity',this.root);
  this.travel=this.hud.node('boss-notice-go',this.root,124*unit,0,48*unit,48*unit);
  const button=this.travel.addComponent(Button);button.transition=Button.Transition.NONE;this.travel.addComponent(BlockInputEvents);
  this.travel.on(Button.EventType.CLICK,()=>this.hud.actions.click('boss-go:'+this.key));
  const label=this.hud.text(this.travel,tr('travel'),0,0,44*unit,13*unit,F.color('state.running'),24*unit);applyRpgFont(label);label.horizontalAlign=Label.HorizontalAlign.CENTER;
  UiSkin.asset(this.root,'settings-footer-rule-v11',4*unit,23*unit,false).node.setPosition(94*unit,0);
  this.root.active=false;
 }
 get visible(){return !!this.root?.activeInHierarchy;}
 get height(){return 52*this.unit;}
 contains(point:Vec2){return !!this.travel?.activeInHierarchy&&!!this.travel.getComponent(UITransform)?.hitTest(point);}
 layout(top:number,notice:{entry:BossEntry;ready:boolean}|null,available:boolean){
  const root=this.root;if(!root?.isValid)return;
  root.active=available&&!!notice;
  if(!notice)return;
  if(root.position.x!==0||root.position.y!==top-this.height/2)root.setPosition(0,top-this.height/2);
  const row=notice.entry,s=this.unit,stamp=`${row.key}|${notice.ready}|${row.level}`;
  this.key=row.key;if(this.stamp===stamp)return;this.stamp=stamp;
  for(const child of [...this.body!.children]){child.removeFromParent();child.destroy();}
  UiSkin.sprite(this.body!,bossPortrait(row),36*s,36*s).node.setPosition(-127*s,0);
  const label=(name:string,value:string,x:number,y:number,w:number,size:number,role:'text.normal'|'text.secondary'|'state.ready'|'state.success')=>{
   const l=this.hud.text(this.body!,value,x*s,y*s,w*s,size*s,F.color(role),18*s);l.node.name=name;applyRpgFont(l);l.enableWrapText=false;l.lineHeight=16*s;return l;
  };
  label('BossNoticeName',row.name,-45,9,108,12.5,'state.ready');
  label('BossNoticeState',tr(notice.ready?'ready':'alive'),49,9,66,9.5,'state.success');
  label('BossNoticePlace',`${row.place} · Lv${row.level}`,-6,-10,186,9.5,'text.secondary');
 }
}
