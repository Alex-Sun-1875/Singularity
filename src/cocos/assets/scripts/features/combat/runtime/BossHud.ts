import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {Node,Sprite,UITransform,sys} from 'cc';
import type {EnemyState} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';

export const BOSS_HEAD_HEIGHT=38,BOSS_HEAD_GAP=6;
export const bossHudScale=(hud:Hud)=>sys.isMobile?hud.height/Math.max(1,viewportMetrics.windowSize.height/Math.max(1,viewportMetrics.devicePixelRatio)):1.25;

/** Part of the world-anchored boss nameplate. No screen-wide banner or input. */
export class BossHealthStrip {
 readonly node:Node;readonly barWidth:number;private fill:Sprite;private value='';private level='';
 constructor(hud:Hud,parent:Node,width:number,unit:number){
  this.node=hud.node('BossHealthStrip',parent,0,0,width,14*unit);
  this.barWidth=width-64*unit;const barWidth=this.barWidth,bar=hud.node('BossHealth',this.node,0,0,barWidth,16);
  this.fill=UiSkin.bar(bar,barWidth,'health');bar.setScale(1,10*unit/16,1);
  // Keep the actual red fill readable inside the thin gold-edged track.
  const fillSize=this.fill.node.getComponent(UITransform)!;fillSize.setContentSize(fillSize.width,12/this.fill.node.scale.y);
 }
 update(enemy:EnemyState){this.value=`${Math.ceil(enemy.hp)}/${enemy.maxHp}`;this.level=`Lv${enemy.level??1}`;F.bar(this.fill,enemy.hp,enemy.maxHp,'health.enemy');}
 get readout(){return `${this.value} · ${this.level}`;}
 inspect(){return {text:this.value,level:this.level,fraction:this.fill.fillRange};}
}
