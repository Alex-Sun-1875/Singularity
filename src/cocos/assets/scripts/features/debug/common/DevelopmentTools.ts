import {CAMPAIGN_MAX_LEVEL} from '../../progression/data/CampaignProgression';
import type {GameState} from '../../../core/GameSession';
import {BUILD_PROFILE} from '../../../shared/BuildProfile';
import {SUPPLIES} from '../../equipment/data/Supplies';
import {cumulativeXp} from '../../progression/common/Progression';

interface Host {state():GameState;experience(source:string,amount:number):boolean;changed():void}
export interface DevelopmentResult {ok:boolean;message:string}

/** Explicit actions on the isolated dev journey. No passive immunity, free casts or story flags. */
export class DevelopmentTools {
 private feedback='';
 constructor(private host:Host){}
 get enabled(){return BUILD_PROFILE.name==='dev'&&BUILD_PROFILE.developmentTools;}
 private result(ok:boolean,message:string):DevelopmentResult{this.feedback=message;return {ok,message};}
 view(){
  const s=this.host.state(),p=s.player;
  return {enabled:this.enabled,level:s.progression.level,hp:p.hp,maxHp:p.maxHp,resource:p.focus,maxResource:p.maxFocus,
   gold:p.gold,iron:p.iron,runes:p.runes,cores:p.cores,
   bossWaits:Object.keys(s.receipts).filter(key=>key.startsWith('boss:v3:ready:')&&Number(s.receipts[key])>0).length,
   feedback:this.feedback};
 }
 run(action:string):DevelopmentResult{
  if(!this.enabled)return this.result(false,'快速验证工具仅在 dev 构建启用。');
  const s=this.host.state(),p=s.player;
  if(s.status==='dead'||p.hp<=0)return this.result(false,'请先通过正常重试恢复旅程。');
  if(s.dialogue||s.dice.active)return this.result(false,'请先完成当前对话或检定。');
  let message='';
  switch(action){
   case 'refill':
    if(p.hp===p.maxHp&&p.focus===p.maxFocus)return this.result(false,'生命与职业资源已满。');
    p.hp=p.maxHp;p.focus=p.maxFocus;message='生命与职业资源已补满。';break;
   case 'supplies':{
    const definitions=Object.values(SUPPLIES);
    if(definitions.every(d=>p[d.stock]===d.capacity))return this.result(false,'药水已达携带上限。');
    for(const d of definitions)p[d.stock]=d.capacity;
    message='生命、体力、专注与法力药水已补齐。';break;
   }
   case 'materials':
    if((['gold','iron','runes','cores'] as const).every(key=>p[key]>=9999))return this.result(false,'金币与锻造材料已达调试上限。');
    for(const key of ['gold','iron','runes','cores'] as const)p[key]=Math.max(p[key],9999);
    message='金币、铁、符文与核心已各补至 9999。';break;
   case 'level5':case 'levelMax':case 'level40':{
    const target=action==='level5'?Math.min(CAMPAIGN_MAX_LEVEL,s.progression.level+5):CAMPAIGN_MAX_LEVEL,amount=cumulativeXp(target)-s.progression.totalXp;
    if(amount<=0)return this.result(false,`已达到当前 ${CAMPAIGN_MAX_LEVEL} 级上限。`);
    const ok=this.host.experience(`dev:level:${target}`,amount);
    return this.result(ok,ok?`已提升至 ${s.progression.level} 级，按正常规则获得技能与属性点。`:'本次等级调整未生效。');
   }
   case 'boss-ready':{
    const keys=Object.keys(s.receipts).filter(key=>key.startsWith('boss:v3:ready:')&&Number(s.receipts[key])>0);
    if(!keys.length)return this.result(false,'目前没有已击败 Boss 的再战等待记录。');
    for(const key of keys)s.receipts[key]=0;
    message='已清除 Boss 再战等待，请从旅程页发起正常再战。';break;
   }
   default:return this.result(false,'未知的快速验证操作。');
  }
  this.host.changed();return this.result(true,message);
 }
}
