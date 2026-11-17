import type {GameState} from '../../../core/GameSession';
import {localizeCampaignStages} from '../locales/CampaignStageText';

export interface CampaignStageAction {kind:'task'|'event'|'action'|'exit'|'boss';area:string;taskId?:string;eventId?:string;action?:string;flag?:string;bossId?:string;branch?:'quarry'}
export interface CampaignStage {id:string;chapter:1|2;name:string;story:string;area:string;experience:number;targetTotalXp:number;actions:CampaignStageAction[]}
/** Cumulative main-route targets include all mandatory sources, not optional
 * exploration or repeat kills. The evacuation/pressure stages fund boss entry. */
export const CAMPAIGN_STAGE_XP_TARGETS:Record<string,number>={
 'c1-traces':300,'c1-mill':700,'c1-herd':1250,'c1-camp':2100,'c1-letter':2450,'c1-sentinel':3300,
 'c1-table':4300,'c1-cells':5000,'c1-exit':8000,'c1-captain':8800,'c1-gate':9700,'c1-return':10600,
 'c2-front':11900,'c2-orders':14000,'c2-workshop':17800,'c2-stop':20500,'c2-heat':24200,'c2-quarry':31000,
 'c2-evidence':35000,'c2-post':40500,'c2-post-return':44500,'c2-command':48000,'c2-oath':58000,'c2-pressure':64500,
 'c2-guardian':67500,'c2-bridge':69500,'c2-armory':71000,'c2-contact':74200,
};
type State=Pick<GameState,'receipts'|'flags'>;
const task=(area:string,taskId:string):CampaignStageAction=>({kind:'task',area,taskId});
const event=(area:string,eventId:string):CampaignStageAction=>({kind:'event',area,eventId});
const action=(area:string,action:string,flag:string):CampaignStageAction=>({kind:'action',area,action,flag});
const boss=(area:string,bossId:string):CampaignStageAction=>({kind:'boss',area,bossId,flag:'boss_defeated:'+bossId});
const stage=(id:string,chapter:1|2,name:string,area:string,experience:number,story:string,actions:CampaignStageAction[]):CampaignStage=>({id,chapter,name,area,experience,targetTotalXp:CAMPAIGN_STAGE_XP_TARGETS[id],story,actions});
/** Source identities and physical actions stay stable. Completion XP is 15%
 * of each stage's main budget; its actual nodes own the remaining 85%. */
export const CAMPAIGN_STAGES:CampaignStage[]=[
 stage('c1-traces',1,'暮色下的足迹','S02',45,'兽群逃离群山。核对渡口痕迹，并亲手为居民确定安全的撤离方向。',[task('S02','border-traces'),event('S02','c1-warning')]),
 stage('c1-mill',1,'夺回断轮磨坊','S07',60,'夺回磨坊后，危险还没有结束。救出被困者，检查地下异响与磨坊的损伤。',[task('S07','border-mill'),event('S07','c1-mill-rescue')]),
 stage('c1-herd',1,'猎场反击','S08',83,'阻止先头兽群冲入道路，再处理迁徙中的现场危机。真实狩猎累计继续有效。',[task('S08','border-hunt'),event('S08','c1-herd-crossing')]),
 stage('c1-camp',1,'灰披营地攻坚','S09',128,'击破营地守军后核验扣押名册，追查工匠被送去了哪里。',[task('S09','border-camp'),event('S09','c1-detention-roll')]),
 stage('c1-letter',1,'原信上的近日日期','S04',53,'遗物匣里不止有星片。亲自读信，核对近期求援与十八年前的阵亡记录。',[action('S04','recover','recovered'),action('S04','letter','read_letter')]),
 stage('c1-sentinel',1,'初醒的旧军','U1-03',128,'旧军与现代驻军似乎服从不同目标。通过警戒组后，核验遗卫留下的命令。',[task('U1-03','border-watch'),event('U1-03','c1-old-sentinel')]),
 stage('c1-table',1,'阵亡者的晚饭','U1-04',150,'在长桌听取伊芙琳与弥菈各自的解释。可以追问，也可以保持独立行动。',[action('U1-04','meeting','meeting'),event('U1-04','c1-table-truth')]),
 stage('c1-cells',1,'监区的两种接近法','U1-05',105,'核验监区路线，选择击败守卫或从检修侧廊拆除诱片，真正释放工匠。',[event('U1-05','c1-cell-route'),action('U1-05','release_workers','workers_released')]),
 stage('c1-exit',1,'真正离开扣押间','U1-05',450,'先核验出口锚点与安全线，再带获释工匠实际离开。获释和离场分别记录。',[event('U1-05','c1-exit-anchor'),event('U1-05','c1-exit-test'),{kind:'exit',area:'U1-05',flag:'workers_departed'}]),
 stage('c1-captain',1,'裂隘关的灰披队长','S10',120,'真正击败守住关口的灰披队长，为救援者打开地表道路。',[boss('S10','BOSS_R1')]),
 stage('c1-gate',1,'亲手抬起横杆','S10',135,'亲手抬起关口横杆，沿用未熄之誓的真实获得来源。',[action('S10','captain_gate','gate_raised')]),
 stage('c1-return',1,'回来的人与留下的约定','S01-T6',135,'确认工匠已经有地方落脚，再回长桌交代救援结果；合作与独立立场都能结束本章。',[event('S01-T6','c1-town-return'),event('U1-04','c1-renewed-oath')]),
 stage('c2-front',2,'战火中的山驿','H01',195,'听取工匠、守军和居民的不同处境，确定工位与撤离方向。',[task('H01','highland-front'),event('H01','c2-front-voices')]),
 stage('c2-orders',2,'谁在接收征用令','H01',315,'核验征用令印记，沿道路追查命令的接收者，而非只凭一张公文判断。',[event('H01','c2-order-seal'),event('H02','c2-order-road')]),
 stage('c2-workshop',2,'熔镜工位保卫战','H03',570,'击败威胁工匠通道的固定敌阵，保住撤离面。',[task('H03','highland-workers')]),
 stage('c2-stop',2,'先让工位停稳','H03',405,'疏散转动面旁的工人，再逐段核验东西工位的停机状态。',[event('H03','h03-evacuate'),event('H03','c2-stop-west'),event('H03','c2-stop-east')]),
 stage('c2-heat',2,'一次可以回退的试验','H03',555,'实际转开散热叶片，读取升温与回落刻线，完成可安全回退的试验。',[event('H03','m3-heat-test')]),
 stage('c2-quarry',2,'采坑中的两份证据','H04',1020,'检查制动器，再选择护送证人或保全货签；两种救援都能推进。',[task('H04','highland-hunt')]),
 stage('c2-evidence',2,'带走证据之后','H06',4000,'按此前选择完成证人接应或货签核验，不要求补做互斥的另一条路线。',[{kind:'event',area:'H06',branch:'quarry'}]),
 stage('c2-post',2,'石梁前哨的抉择','H07',825,'凭证人交涉、用货签切断警报后突破，或进行真实战斗。',[task('H07','highland-ridge')]),
 stage('c2-post-return',2,'前哨放行之后','H07',600,'根据前哨的解决方式，完成接应、军械封存或战损处置。',[event('H07','c2-post-settle')]),
 stage('c2-command',2,'号令与旧档的差异','H07',525,'把现代号令与旧档对照，核验供能线索和命令来源。',[event('H07','c2-command-source')]),
 stage('c2-oath',2,'三誓阵的回应','U1-06',1500,'通过三处控制台停机或真实战斗解决三誓阵，再核验现场后果。',[task('U1-06','highland-oath'),event('U1-06','c2-oath-aftermath')]),
 stage('c2-pressure',2,'深炉侧翼的退路','U1-07',975,'逐段泄压并停炉，走到退路处确认随时能够撤回。',[event('U1-07','u107-pressure'),event('U1-07','c2-pressure-return')]),
 stage('c2-guardian',2,'守桥铠卫','H08',450,'真正击败断岳前堡的守桥铠卫。',[boss('H08','BOSS_R2')]),
 stage('c2-bridge',2,'接回手柄放下矿桥','H08',300,'亲手放桥，恢复通往军械岸的双向道路。',[event('H08','h08-lower-bridge')]),
 stage('c2-armory',2,'桥后的武备台','H09',225,'沿用武备台原有的装备与工艺来源，不重复领取。',[event('H09','m4-bridge-reward')]),
 stage('c2-contact',2,'第一次可中止的接触','U1-08',480,'建立接触并主动验证断开措施，再回山驿交代结果；拒绝核心请求仍能完成本章。',[event('U1-08','m4-contact'),event('U1-08','c2-contact-failsafe'),event('H01','c2-inn-return')]),
];
localizeCampaignStages(CAMPAIGN_STAGES);
export const campaignStageKey=(id:string)=>'journey:stage:v2:'+id;
export function campaignStageActions(s:State,stage:CampaignStage):CampaignStageAction[]{return stage.actions.map(value=>value.branch==='quarry'?{kind:'event',area:s.receipts['chapter2:quarry-rescue:choice']==='ledger'?'H07':'H06',eventId:s.receipts['chapter2:quarry-rescue:choice']==='ledger'?'c2-ledger-safe':'c2-witness-safe'}:{...value});}
export function campaignStageActionDone(s:State,value:CampaignStageAction){return value.kind==='task'?s.receipts['journey:task:'+value.taskId]===true:value.kind==='event'?s.receipts['campaign:'+value.eventId]===true:!!value.flag&&s.flags[value.flag]===true;}
export function campaignStageSatisfied(s:State,stage:CampaignStage){return campaignStageActions(s,stage).every(value=>campaignStageActionDone(s,value));}
export function campaignStageDone(s:State,stage:CampaignStage){return s.receipts[campaignStageKey(stage.id)]===true;}
export function nextCampaignStage(s:State,chapter?:number){return CAMPAIGN_STAGES.find(stage=>(chapter===undefined||stage.chapter===chapter)&&!campaignStageDone(s,stage));}
export function nextCampaignStageAction(s:State,stage:CampaignStage){return campaignStageActions(s,stage).find(value=>!campaignStageActionDone(s,value));}
export function validateCampaignStages(s:GameState){
 let chapter=0,gap=false;
 for(const stage of CAMPAIGN_STAGES){
  if(stage.chapter!==chapter){chapter=stage.chapter;gap=false;}
  const key=campaignStageKey(stage.id),record=s.receipts[key],xp=s.progression.xpReceipts[key];
  if(record===undefined){gap=true;if(xp!==undefined)throw new Error('阶段经验缺少实际完成凭证');continue;}
  // The registry registers this exact completion amount; keep the content
  // validator below it in the dependency graph rather than importing it back.
  const expected=stage.experience;
  if(record!==true||gap||!campaignStageSatisfied(s,stage)||(expected?xp!==expected:xp!==undefined))throw new Error('无效的章节行动阶段凭证');
 }
}
