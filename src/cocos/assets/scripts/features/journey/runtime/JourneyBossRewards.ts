import {Label} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {Hud} from '../../../app/Hud';
import type {MenuRow} from '../../../shared/ui/MenuPanel';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {mainBossEquipmentView,mainBossChapter,bossRandomPool,bossRewardKind} from '../../equipment/common/BossLoot';
import {PLAYABLE_CHAPTERS,chapterForArea,playableArea} from '../data/ChapterJourney';
import {AREAS,getArea} from '../../world/data/WorldData';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';
import {peacefulBossRetired} from '../../campaign/common/PeacefulBosses';
import {encounterText as text} from '../../campaign/locales/ChapterTwoEncounterText';
import {journeyText as tr} from '../locales';
import {bossRewardSummary,randomBossRewardText} from '../../combat/runtime/BossRewardPresentation';

const styleName=(style:string)=>tr(style==='WAR'?'life.styleWar':style==='BOW'?'life.styleBow':style==='FIR'?'life.styleFire':'life.styleThunder');
export function journeyBossState(game:GameSession,boss:string){
 const enemy=[...game.state.enemies,...Object.values(game.state.encounters).flat()].find(e=>e.bossId===boss);
 if(enemy&&enemy.hp>0)return text('boss.alive');
 if(!game.state.flags['boss_defeated:'+boss])return text('boss.unbeaten');
 const remaining=game.bossLoot.view(boss).remaining,time=`${Math.floor(remaining/60)}:${String(remaining%60).padStart(2,'0')}`;
 return remaining?tr('life.cooldown',{time}):tr('life.bossReady');
}
function bindClock(hud:Hud,action:string,boss:string){
 const label=hud.root.getComponentsInChildren(Label).find(l=>l.node.name==='MenuRowDetail'&&l.node.parent?.name===action);if(label)label.node.name='BossCooldown:'+boss;
}
export function renderJourneyBossRewards(hud:Hud,game:GameSession,menu:string):boolean {
 const parts=menu.split(':'),chapter=Number(parts[1]);
 if(parts[0]==='journey-main-boss-rewards'){
  const view=mainBossEquipmentView(game.state,chapter),boss=PLAYABLE_CHAPTERS.find(c=>c.id===chapter);if(!boss)return true;
  hud.showList(text('boss.fixedTitle'),boss.bossName+' · '+text('boss.previewStyle',{style:styleName(view.style)})+'\n'+text('boss.fixedRules'),view.rewards.map(r=>({label:EQUIPMENT[r.item].quality+' · '+EQUIPMENT[r.item].name,detail:text(r.onGround?'boss.pendingGround':r.owned?'boss.owned':r.awarded?'boss.awarded':'boss.awaitFirstWin'),action:`journey-boss-item:${r.item}:${chapter}:fixed:${parts[2]??''}`})),[{back:true,label:parts[2]==='loot'?text('boss.backRewards'):text('ui.backChapter'),action:parts[2]==='loot'?`journey-loot:${chapter}`:`journey-chapter:${chapter}`},{label:text('ui.map'),action:'journey-map:'+boss.arena}],0,{placement:'center'});return true;
 }
 if(parts[0]==='journey-loot'){
  const style=game.bossLoot.view().style,rows:MenuRow[]=[{label:text('boss.fixedTitle'),detail:text('boss.fixedShort'),action:`journey-main-boss-rewards:${chapter}:loot`}];
  for(const tier of [1,2,3])for(const id of bossRandomPool(chapter,tier,style)){const item=EQUIPMENT[id];if(item)rows.push({label:item.quality+' · '+item.name,detail:tr('life.randomDetail',{level:item.requiredLevel??1}),action:`journey-boss-item:${id}:${chapter}:random`});}
  rows.push({label:tr('life.preference',{style:styleName(style)}),detail:tr('life.preferenceHint'),action:`journey-loot-style:${chapter}`});
  const bosses=Object.values(AREAS).filter(a=>playableArea(a.id)&&chapterForArea(a.id)===chapter).flatMap(a=>a.enemies.filter(e=>!!e.bossId&&!peacefulBossRetired(game.state,e.id)).map(enemy=>({area:a.id,enemy})));
  for(const b of bosses)rows.push({label:`${getArea(b.area).name} · ${CAMPAIGN_ENEMY_TEMPLATES[b.enemy.bossId!]?.name??''}`,detail:journeyBossState(game,b.enemy.bossId!),action:`journey-boss-loot:${b.enemy.bossId}:${chapter}`});
  hud.showList(text('boss.sourcesTitle',{chapter}),text('boss.fixedRules')+'\n\n'+randomBossRewardText(),rows,[{back:true,label:text('ui.backChapter'),action:`journey-chapter:${chapter}`}],0,{placement:'center'});
  for(const b of bosses)bindClock(hud,`journey-boss-loot:${b.enemy.bossId}:${chapter}`,b.enemy.bossId!);return true;
 }
 if(parts[0]==='journey-boss-loot'){
  const id=parts[1],chapter=Number(parts[2]),main=mainBossChapter(id),name=CAMPAIGN_ENEMY_TEMPLATES[id]?.name??id;
  hud.showList(name,bossRewardSummary(id),[{label:text('boss.state'),detail:journeyBossState(game,id),action:menu,disabled:true},{label:text(bossRewardKind(id)==='fixed'?'boss.fixedTitle':'boss.randomTitle'),detail:main?text('boss.fixedRules'):randomBossRewardText(),action:main?`journey-main-boss-rewards:${main}:loot`:menu,disabled:!main}],[{back:true,label:text('boss.backRewards'),action:`journey-loot:${chapter}`}],0,{placement:'center'});bindClock(hud,menu,id);return true;
 }
 if(parts[0]==='journey-boss-item'){
  const item=EQUIPMENT[parts[1]],chapter=Number(parts[2]);if(!item)return true;
  hud.show(item.name,game.itemView(item.id).description,[{back:true,label:text('boss.backRewards'),action:parts[3]==='fixed'?`journey-main-boss-rewards:${chapter}${parts[4]?':'+parts[4]:''}`:`journey-loot:${chapter}`}]);return true;
 }
 return false;
}
