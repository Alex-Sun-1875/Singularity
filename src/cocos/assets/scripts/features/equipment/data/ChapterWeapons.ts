import type {ItemDef} from './Equipment';

const styles=[
 {id:'WAR',kind:'sword',family:'单手剑',art:'W05',names:['守夜者','断岳']},
 {id:'BOW',kind:'bow',family:'双手弓',art:'W10',names:['林间月','穿岩']},
 {id:'FIR',kind:'staff',family:'双手火杖',art:'W12',names:['余烬','熔光']},
 {id:'THU',kind:'staff',family:'双手雷杖',art:'W14',names:['鸣雷','裂空']},
] as const;
export const CHAPTER_WEAPONS:ItemDef[]=[];
for(const chapter of [1,2])for(const route of ['task','boss','hunt'])for(const style of styles){
 const power=chapter===1?24:60,requiredLevel=chapter===1?6:16;
 CHAPTER_WEAPONS.push({id:`CJ${chapter}_${route.toUpperCase()}_${style.id}`,name:`${style.names[chapter-1]}${route==='task'?'之约':route==='hunt'?'猎誓':'战誓'}`,kind:style.kind,slot:'weapon',level:chapter===1?2:4,quality:'史诗',weaponFamily:style.family,artSource:style.art,twoHanded:style.kind!=='sword',power,requiredLevel,description:`Lv${requiredLevel}起可装备 · 第${chapter}章${route==='task'?'任务':route==='hunt'?'狩猎':'关底'}史诗武器\n武器强度 ${power}：基础攻击与技能威力 +${power/3}%。\n${style.family}；阶段属性固定，传奇与神器另按人物等级成长。`,source:route==='task'?'完成本章五段战役任务后自选':route==='hunt'?'本章累计击败40只游荡怪后自选，无需领取悬赏':'实际击败本章关底Boss后自选，无需任务前置'});
}
export function chapterWeaponIds(chapter:number,route:string){return CHAPTER_WEAPONS.filter(i=>i.id.startsWith(`CJ${chapter}_${route.toUpperCase()}_`)).map(i=>i.id);}
