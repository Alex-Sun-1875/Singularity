import type {CampaignEventDef} from './CampaignEvents';
import {fieldQuestText as text} from '../locales/FieldQuestText';

type Extra=Partial<CampaignEventDef>;
const step=(id:string,area:string,key:Parameters<typeof text>[0],requires:string[],flag:string,extra:Extra={}):CampaignEventDef=>({
 id,area,label:text(key),description:text(key,true),requires,sets:[flag],optional:true,
 choices:[{id:'continue',label:text('ui.continue'),text:text(key,true),sets:[]}],...extra,
});
const npc=(actor:string,x:number,z:number,actorModel='mine-worker')=>({actor:'field-npc-'+actor,actorModel,at:{x,z}});
export const FIELD_QUEST_EVENTS:CampaignEventDef[]=[
 step('dg-letter-escort','S19','letter.start',[],'dg:letter-escort',{clearEncounter:true,...npc('orin',-12,-24)}),
 step('dg-letter-recipient','S06','letter.recipient',['dg:letter-escort'],'dg:letter-recipient',{at:{x:12,z:-24}}),
 step('dg-letter-return','S19','letter.return',['dg:letter-recipient'],'dg:letter-complete',{...npc('orin',-12,-24),items:['SQ_LETTER_RING'],gold:65,iron:3,experience:150}),
 step('field-hunt-start','S05','hunt.start',[],'field:hunt-start',{actor:'nightqi',at:{x:12,z:-24}}),
 step('field-hunt-tracks','S08','hunt.tracks',['field:hunt-start'],'field:hunt-tracks',{at:{x:-12,z:-24}}),
 step('field-hunt-choice','S19','hunt.choice',['field:hunt-tracks'],'field:hunt-choice',{at:{x:12,z:-24},clearEncounter:true,choices:[
  {id:'open',label:text('hunt.open'),text:text('hunt.open',true),sets:['field:herd-free']},
  {id:'clean',label:text('hunt.clean'),text:text('hunt.clean',true),sets:['field:young-safe']},
 ]}),
 step('field-hunt-return','S05','hunt.return',['field:hunt-choice'],'field:hunt-complete',{actor:'nightqi',at:{x:12,z:-24},items:['SQ_HUNT_BOOTS'],gold:80,iron:4,experience:200}),
 step('dg-lamp-rescue','H03','lamp.start',[],'dg:lamp-rescued',{clearEncounter:true,...npc('bren',-12,-24)}),
 step('dg-lamp-steady','H03','lamp.steady',['dg:lamp-rescued'],'dg:lamp-steady',{at:{x:12,z:-24}}),
 step('dg-lamp-return','H03','lamp.return',['dg:lamp-steady'],'dg:lamp-complete',{...npc('bren',-12,-24),items:['SQ_LAMP_HANDS'],gold:160,iron:8,runes:2,experience:600}),
 step('field-arms-start','H01','arms.start',[],'field:arms-start',{...npc('tarek',12,-24,'raider-shield')}),
 step('field-arms-tracks','H04','arms.tracks',['field:arms-start'],'field:arms-tracks',{at:{x:-12,z:-24}}),
 step('field-arms-choice','H17','arms.choice',['field:arms-tracks'],'field:arms-choice',{at:{x:12,z:-24},clearEncounter:true,choices:[
  {id:'guard',label:text('arms.guard'),text:text('arms.guard',true),sets:['field:arms-guard']},
  {id:'workers',label:text('arms.workers'),text:text('arms.workers',true),sets:['field:arms-workers']},
 ]}),
 step('field-arms-return','H01','arms.return',['field:arms-choice'],'field:arms-complete',{...npc('tarek',12,-24,'raider-shield'),choices:undefined,choiceItems:['SQ_ARMS_WAR','SQ_ARMS_BOW','SQ_ARMS_FIR','SQ_ARMS_THU'],gold:180,iron:8,experience:800}),
 step('dg-dawn-name','S03','dawn.name',['dg:dawn-found'],'dg:dawn-name',{...npc('keeper',12,-24)}),
 step('field-dawn-record','S12','dawn.record',['dg:dawn-name'],'field:dawn-record',{at:{x:-12,z:-24},clearEncounter:true}),
 step('dg-dawn-return','S12','dawn.return',['field:dawn-record'],'dg:dawn-complete',{at:{x:12,z:-24},items:['SQ_DAWN_NECKLACE'],gold:150,iron:6,experience:350}),
 step('field-bell-start','H17','bell.start',['field:bell-found'],'field:bell-start',{...npc('milo',-12,-24)}),
 step('field-bell-fork','H07','bell.fork',['field:bell-start'],'field:bell-fork',{at:{x:-12,z:-24}}),
 step('field-bell-tune','U1-06','bell.tune',['field:bell-fork'],'field:bell-tune',{at:{x:12,z:-24},clearEncounter:true}),
 step('field-bell-return','H17','bell.return',['field:bell-tune'],'field:bell-complete',{...npc('milo',-12,-24),choices:undefined,choiceItems:['DG_A01','DG_A03','DG_A04','DG_A05'],gold:350,iron:14,runes:4,cores:1,experience:1200}),
 step('field-letter-camp','S06','letter.epilogue',['dg:letter-complete'],'field:letter-revisited',{...npc('orin-camp',-12,-24)}),
 step('field-lamp-inn','H01','lamp.epilogue',['dg:lamp-complete'],'field:lamp-revisited',{...npc('bren-inn',-12,-24)}),
];
export const FIELD_QUESTS=[
 {id:'letter',chapter:1,name:'未送达的归信',steps:['dg-letter-escort','dg-letter-recipient','dg-letter-return'],reward:'紫色史诗 · 归信指环'},
 {id:'hunt',chapter:1,name:'兽群最后的退路',steps:['field-hunt-start','field-hunt-tracks','field-hunt-choice','field-hunt-return'],reward:'紫色史诗 · 逐迹护靴'},
 {id:'dawn',chapter:1,name:'未写完的墓志',hidden:'dg:dawn-found',steps:['dg-dawn-name','field-dawn-record','dg-dawn-return'],reward:'橙色传奇 · 守望者的遗念'},
 {id:'lamp',chapter:2,name:'灯不可熄',steps:['dg-lamp-rescue','dg-lamp-steady','dg-lamp-return'],reward:'紫色史诗 · 守灯护手'},
 {id:'arms',chapter:2,name:'失窃的军械',steps:['field-arms-start','field-arms-tracks','field-arms-choice','field-arms-return'],reward:'紫色史诗武器 · 四流派自选一件'},
 {id:'bell',chapter:2,name:'第十三声钟响',hidden:'field:bell-found',steps:['field-bell-start','field-bell-fork','field-bell-tune','field-bell-return'],reward:'成长神器武器 · 四流派自选一件'},
] as const;
export const FIELD_DISCOVERIES=[{chapter:1,flag:'dg:dawn-found',name:'未写完的墓志'},{chapter:2,flag:'field:bell-found',name:'第十三声钟响'}] as const;
const NPC_FLAGS:Record<string,{flag:string;present:boolean}>={
 'field-npc-orin':{flag:'dg:letter-complete',present:false},'field-npc-orin-camp':{flag:'dg:letter-complete',present:true},
 'field-npc-bren':{flag:'dg:lamp-complete',present:false},'field-npc-bren-inn':{flag:'dg:lamp-complete',present:true},
 'field-npc-milo':{flag:'field:bell-found',present:true},'field-npc-keeper':{flag:'dg:dawn-found',present:true},
};
export function fieldNpcVisible(id:string,flags:Record<string,boolean>){const rule=NPC_FLAGS[id];return !rule||!!flags[rule.flag]===rule.present;}
