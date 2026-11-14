import type {ItemDef} from './Equipment';
import {lifecycleWeaponBase} from './EquipmentLifecycle';

export const FIELD_QUEST_ITEMS:ItemDef[]=[
 {id:'SQ_LETTER_RING',name:'归信指环',kind:'ring',slot:'ringLeft',level:1,requiredLevel:6,chapter:1,quality:'史诗',growthMode:'fixed',maxHp:18,artSource:'J03',description:'最大生命 +18。老猎人终于收下了营地的回信。',source:'野外支线「未送达的归信」固定奖励'},
 {id:'SQ_HUNT_BOOTS',name:'逐迹护靴',kind:'armor',slot:'feet',level:1,requiredLevel:8,chapter:1,quality:'史诗',growthMode:'fixed',maxHp:20,armor:2,artSource:'A10',description:'最大生命 +20，护甲 +2。沿着兽群离开的方向，留下可以折返的路。',source:'野外支线「兽群最后的退路」固定奖励'},
 {id:'SQ_LAMP_HANDS',name:'守灯护手',kind:'armor',slot:'hands',level:2,requiredLevel:14,chapter:2,quality:'史诗',growthMode:'fixed',maxHp:28,armor:3,artSource:'A09',description:'最大生命 +28，护甲 +3。灯架上的余温留在修理者的手套里。',source:'野外支线「灯不可熄」固定奖励'},
 {id:'SQ_DAWN_NECKLACE',name:'守望者的遗念',kind:'necklace',slot:'necklace',level:1,requiredLevel:8,chapter:1,quality:'传奇',growthMode:'fixed',maxHp:30,armor:2,artSource:'J06',description:'最大生命 +30，护甲 +2。纪念一位为别人撑住闸门的守望者。',source:'第一章隐藏任务「未写完的墓志」固定奖励'},
];
for(const [style,kind,family,art]of [['WAR','sword','单手剑','W03'],['BOW','bow','双手弓','W09'],['FIR','staff','双手火杖','W12'],['THU','staff','双手雷杖','W14']] as const){
 const power=Math.round(lifecycleWeaponBase(16)*1.1);
 FIELD_QUEST_ITEMS.push({id:'SQ_ARMS_'+style,name:'归还者的'+({WAR:'剑',BOW:'弓',FIR:'火杖',THU:'雷杖'}[style]),kind,slot:'weapon',weaponFamily:family,twoHanded:style!=='WAR',level:2,requiredLevel:16,chapter:2,quality:'史诗',growthMode:'fixed',power,artSource:art,description:`武器强度 ${power}。追回的军械终于交到了有名字的人手里。`,source:'野外支线「失窃的军械」四流派自选奖励'});
}
