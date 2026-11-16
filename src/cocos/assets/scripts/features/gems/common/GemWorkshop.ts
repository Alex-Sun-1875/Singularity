import type {GameState} from '../../../core/GameSession';
import {EQUIPMENT,canonicalItem,type ItemDef} from '../../equipment/data/Equipment';
import {JOURNEY_TASKS,chapterForArea,journeyTaskKey,playableArea} from '../../journey/data/ChapterJourney';
import {GEM_STATS,GEM_POLICY,GEM_OPEN_COST,gemUnits,gemBankKey,gemTierCap,gemCapacity,gemAmount,gemOpenCost,gemOpeningInvestment,type GemStat,type GemTier} from '../data/Gems';
import {gemText} from '../locales';

export type {GemStat,GemTier} from '../data/Gems';
export interface SocketGem {stat:GemStat;tier:GemTier;units:number}
export interface ItemGems {opened:number;sockets:(SocketGem|null)[]}
export interface GemBonus {power:number;maxHp:number;armor:number;criticalChance:number;criticalDamage:number;strength:number;dexterity:number;intellect:number;vitality:number}
/** Per spawn slot only: ordinary farming never appends one entry per kill/reward. */
interface HuntRecord {cycle:number;count:number;rewards:number}
export interface GemGrant {source:string;shards:number;drills:number}
export interface GemPending {gold:number;drills:number;bank:Record<string,number>}
export type GemActionKind='open'|'inlay'|'extract'|'synthesis'|'exchange'|'transfer'|'recycle'|'claim';
export interface GemTransaction {request:string;kind:GemActionKind;stage:number;gold:number;rules:2;item?:string;hole?:number;stat?:GemStat;tier?:number;from?:string;to?:string;claim?:GemPending}
/** One current ruleset. Pending balances only hold refunds from current cultivation. */
export interface GemState {version:2;revision:number;shards:number;drills:number;bank:Record<string,number>;items:Record<string,ItemGems>;hunts:Record<string,HuntRecord>;grants:GemGrant[];transactions:GemTransaction[];pending:GemPending}
export interface GemQuote {allowed:boolean;reason:string;reasonKey:string;token:string;gold:number;refundGold:number;drills:number;shards:number;units:number;stock:number;result:number;bank?:Record<string,number>;claim?:GemPending;item?:string;hole?:number;opened?:number;gem?:SocketGem|null;previous?:SocketGem|null;stat?:GemStat;tier?:number;fromUnits?:number;toUnits?:number;from?:string;to?:string;source?:ItemGems;target?:ItemGems;returned?:number;investment?:number}
type GemHostState=GameState;
interface Host {state():GemHostState;availability():{available:boolean;reason:string};id(prefix:string):string;changed():void;recalculate():void;emit(type:string,text:string):void}
const emptyItem=(item?:ItemDef):ItemGems=>({opened:gemCapacity(item)>0?1:0,sockets:[null,null,null,null,null]});
const emptyPending=():GemPending=>({gold:0,drills:0,bank:{}});
const rewardChapterCap=(s:GemHostState)=>s.progression.secondChapter||s.progression.level>=11?2:1;
const zeroBonus=():GemBonus=>({power:0,maxHp:0,armor:0,criticalChance:0,criticalDamage:0,strength:0,dexterity:0,intellect:0,vitality:0});
export const freshGems=():GemState=>({version:2,revision:0,shards:0,drills:0,bank:{},items:{},hunts:{},grants:[],transactions:[],pending:emptyPending()});
const own=(s:GemHostState,id:string)=>!!EQUIPMENT[id]&&EQUIPMENT[id].kind!=='spell'&&(s.inventory[id]??0)>0&&!!s.provenance[id];
const validStat=(s:unknown):s is GemStat=>GEM_STATS.includes(s as GemStat);
const integer=(n:unknown,max:number=GEM_POLICY.capacity,min=0):n is number=>typeof n==='number'&&Number.isSafeInteger(n)&&n>=min&&n<=max;
const object=(v:unknown):v is Record<string,any>=>!!v&&typeof v==='object'&&!Array.isArray(v)&&Object.getPrototypeOf(v)===Object.prototype;
const keys=(v:object,wanted:string[])=>Object.keys(v).sort().join()===wanted.slice().sort().join();
const copy=<T>(v:T):T=>JSON.parse(JSON.stringify(v));
const slot=(d:ItemDef)=>d.kind==='ring'?'ring':d.slot;
const bonusFor=(g:ItemGems|undefined,capacity=5):GemBonus=>{const b=zeroBonus();for(const gem of(g?.sockets??[]).slice(0,Math.min(g?.opened??0,capacity)))if(gem)b[gem.stat]+=gemAmount(gem.stat,gem.tier,gem.units);return b;};
export function itemGemBonus(s:GemHostState,id:string):GemBonus {return bonusFor(s.gems?.items[id],gemCapacity(EQUIPMENT[id]));}
/** One item-ID owns one cultivation set; wearing its second copy cannot clone it. */
export function equippedGemBonus(s:GemHostState):GemBonus {const b=zeroBonus(),seen=new Set<string>();for(const [key,id]of Object.entries(s.equipment)){if(key==='spells'||typeof id!=='string'||seen.has(id)||key==='offhand'&&EQUIPMENT[s.equipment.weapon]?.twoHanded)continue;seen.add(id);const q=itemGemBonus(s,id);for(const stat of Object.keys(b) as (keyof GemBonus)[])b[stat]+=q[stat];}for(const stat of Object.keys(b) as (keyof GemBonus)[])b[stat]=Math.round(b[stat]*1e6)/1e6;b.maxHp=Math.round(b.maxHp);return b;}
export function itemGemView(s:GemHostState,item:string){const id=canonicalItem(item),d=EQUIPMENT[id],g=s.gems?.items[id]??emptyItem(d),cap=gemTierCap(s),capacity=gemCapacity(d),copies=Object.values(s.equipment).filter(value=>value===id).length;return {id,item:d,opened:Math.min(g.opened,capacity),sockets:copy(g.sockets),units:d?gemUnits(d):5,capacity,eligible:capacity>0,tierCap:cap,maxTier:cap,bonus:itemGemBonus(s,id),duplicate:copies>1,owned:own(s,id)};}
export function pendingGemView(s:GemHostState){const p=s.gems?.pending??emptyPending(),totalUnits=Object.values(p.bank).reduce((n,v)=>n+v,0);return {...copy(p),totalUnits,available:p.gold>0||p.drills>0||totalUnits>0};}
const put=(bank:Record<string,number>,key:string,delta:number)=>{const n=(bank[key]??0)+delta;if(!integer(n))throw new Error('reason.full');if(n)bank[key]=n;else delete bank[key];};
const charge=(g:GemState,key:'shards'|'drills',amount:number)=>{const n=g[key]-amount;if(!integer(n))throw new Error(amount>g[key]?key==='shards'?'reason.noShards':'reason.noDrills':'reason.full');g[key]=n;};
const pending=(g:GemState)=>g.pending;
const hold=(g:GemState,key:'gold'|'drills',amount:number)=>{const p=pending(g),next=p[key]+amount;if(!integer(next,1e8))throw new Error('reason.full');p[key]=next;};
const returnGem=(g:GemState,gem:SocketGem|null)=>{if(!gem)return;const key=gemBankKey(gem.stat,gem.tier),free=GEM_POLICY.capacity-(g.bank[key]??0),taken=Math.min(free,gem.units);if(taken)put(g.bank,key,taken);if(taken<gem.units){const p=pending(g);p.bank[key]=(p.bank[key]??0)+gem.units-taken;}};

/** Apply one deterministic action to a disposable ledger copy, including previews. */
function apply(g:GemState,t:GemTransaction,s:GemHostState):number {
 const item=t.item&&EQUIPMENT[t.item],units=item?gemUnits(item):5,stage=t.stage,capacity=gemCapacity(item||undefined);let gold=0;
 if(t.kind==='open'||t.kind==='inlay'||t.kind==='extract'||t.kind==='recycle'){
  if(!t.item||!own(s,t.item))throw new Error('reason.unowned');const q=g.items[t.item]??emptyItem(item||undefined);
  if(t.kind==='recycle'){if(q.opened<2&&!q.sockets.some(Boolean))throw new Error('reason.noProgress');for(const gem of q.sockets)returnGem(g,gem);const refund=gemOpeningInvestment(q.opened,units);hold(g,'gold',refund);hold(g,'drills',refund);delete g.items[t.item];}
  else{
   if(!integer(t.hole,4))throw new Error('reason.invalid');const hole=t.hole;if(!capacity)throw new Error('reason.quality');if(hole>=capacity)throw new Error('reason.socketLimit');
   if(t.kind==='open'){if(hole!==q.opened||hole>=capacity)throw new Error(hole<q.opened?'reason.occupied':'reason.nextHole');const cost=gemOpenCost(hole,units);charge(g,'drills',cost);q.opened++;gold=cost;}
   else {if(hole>=q.opened)throw new Error('reason.closed');const old=q.sockets[hole];
    if(t.kind==='extract'){if(!old)throw new Error('reason.empty');returnGem(g,old);q.sockets[hole]=null;}
    else {if(!validStat(t.stat)||!integer(t.tier,5,1))throw new Error('reason.invalid');if(t.tier>stage)throw new Error('reason.tierLocked');if(old?.stat===t.stat&&old.tier===t.tier)throw new Error('reason.occupied');const key=gemBankKey(t.stat,t.tier);if((g.bank[key]??0)<units)throw new Error('reason.noCrystals');put(g.bank,key,-units);returnGem(g,old);q.sockets[hole]={stat:t.stat,tier:t.tier as GemTier,units};gold=units;}
   }
   g.items[t.item]=q;
  }
 }else if(t.kind==='exchange'){if(!validStat(t.stat))throw new Error('reason.invalid');charge(g,'shards',5);put(g.bank,gemBankKey(t.stat,1),5);}
 else if(t.kind==='synthesis'){if(!validStat(t.stat)||!integer(t.tier,4,1))throw new Error('reason.invalid');if(t.tier>=stage)throw new Error('reason.maxTier');const key=gemBankKey(t.stat,t.tier);if((g.bank[key]??0)<15)throw new Error('reason.noCrystals');put(g.bank,key,-15);put(g.bank,gemBankKey(t.stat,t.tier+1),5);gold=5*Math.pow(3,t.tier-1);}
 else if(t.kind==='transfer'){
  if(!t.from||!t.to||!own(s,t.from)||!own(s,t.to))throw new Error('reason.unowned');if(t.from===t.to)throw new Error('reason.sameItem');const a=EQUIPMENT[t.from],b=EQUIPMENT[t.to];if(slot(a)!==slot(b))throw new Error('reason.differentSlot');const source=g.items[t.from]??emptyItem(a),target=g.items[t.to]??emptyItem(b),targetCapacity=gemCapacity(b);if(!targetCapacity)throw new Error('reason.quality');if(source.opened<2&&!source.sockets.some(Boolean))throw new Error('reason.noProgress');if(target.opened!==1||target.sockets.some(Boolean))throw new Error('reason.targetOccupied');
  if(gemUnits(a)===gemUnits(b)){const next=copy(source);next.opened=Math.min(source.opened,targetCapacity);for(let i=next.opened;i<5;i++){returnGem(g,next.sockets[i]);next.sockets[i]=null;}const refund=gemOpeningInvestment(source.opened,gemUnits(a))-gemOpeningInvestment(next.opened,gemUnits(b));if(refund){hold(g,'gold',refund);hold(g,'drills',refund);}g.items[t.to]=next;}
  else {const budget=gemOpeningInvestment(source.opened,gemUnits(a));let opened=1,used=0;while(opened<targetCapacity&&used+gemOpenCost(opened,gemUnits(b))<=budget){used+=gemOpenCost(opened,gemUnits(b));opened++;}for(const gem of source.sockets)returnGem(g,gem);hold(g,'gold',budget-used);hold(g,'drills',budget-used);g.items[t.to]={opened,sockets:[null,null,null,null,null]};}
  delete g.items[t.from];
 }else if(t.kind==='claim'){
  const c=t.claim,p=pending(g);if(!object(c)||!keys(c,['gold','drills','bank'])||!integer(c.gold,9999)||!integer(c.drills)||!object(c.bank)||c.gold>p.gold||c.drills>p.drills||Object.values(c.bank).some(n=>!integer(n,GEM_POLICY.capacity,1))||!c.gold&&!c.drills&&!Object.keys(c.bank).length)throw new Error('reason.noProgress');
  for(const[key,n]of Object.entries(c.bank)){if(n>(p.bank[key]??0))throw new Error('reason.invalid');put(g.bank,key,n);p.bank[key]-=n;if(!p.bank[key])delete p.bank[key];}charge(g,'drills',-c.drills);p.gold-=c.gold;p.drills-=c.drills;gold=-c.gold;
 }else throw new Error('reason.invalid');
 return gold;
}

const huntSource=(source:string)=>/^hunt:([^:]+):(.+):(\d+)$/.exec(source);
const bossSource=(source:string)=>/^boss:([^:]+):(.+):(\d+)$/.exec(source);
function enemyIn(s:GemHostState,area:string,id:string){return (s.area===area?s.enemies:s.encounters[area]??[]).find(e=>e.id===id);}
function validHunt(s:GemHostState,source:string,live=false){const m=huntSource(source);if(!m||!playableArea(m[1]))return null;const cycle=Number(m[3]),e=enemyIn(s,m[1],m[2]);if(!integer(cycle,1e7,1)||!e?.respawnSeconds||e.bossId||e.trainingEnemy||Number(s.receipts[`hunt-cycle:${m[1]}:${m[2]}`]??0)<cycle)return null;if(live&&(e.hp>0||e.phase!=='dead'||cycle!==(e.respawnCount??0)+1))return null;return {area:m[1],id:m[2],cycle,e,key:`${m[1]}:${m[2]}`,chapter:chapterForArea(m[1])};}
function validGrant(s:GemHostState,r:GemGrant){
 if(!object(r)||!keys(r,['source','shards','drills'])||typeof r.source!=='string'||!integer(r.shards)||!integer(r.drills)||huntSource(r.source))return false;
 if(r.source.startsWith('journey:task:'))return JOURNEY_TASKS.some(t=>journeyTaskKey(t.id)===r.source)&&s.receipts[r.source]===true&&r.shards===10&&r.drills===2;
 const m=bossSource(r.source);if(!m||!playableArea(m[1]))return false;const e=enemyIn(s,m[1],m[2]),cycle=Number(m[3]),chapter=r.shards/10;return !!e?.bossId&&!e.trainingEnemy&&integer(cycle,1e7)&&s.receipts[`kill:${m[1]}:${m[2]}`]===true&&Number(s.receipts[`boss:v3:${m[1]}:${m[2]}:life`]??-1)>=cycle&&integer(chapter,rewardChapterCap(s),1)&&(cycle>0||chapter===chapterForArea(m[1]))&&r.drills===2*chapter;
}
export const gemSignature=(t:GemTransaction)=>JSON.stringify(t);

export class GemWorkshop {
 constructor(private host:Host){}
 private get s(){return this.host.state();}
 private get g(){return this.s.gems;}
 private quote(kind:GemActionKind,args:Partial<GemTransaction>):GemQuote {
  const s=this.s,g=s.gems,stage=gemTierCap(s),t={request:'preview',kind,stage,gold:0,rules:2,...args} as GemTransaction,d=t.item?EQUIPMENT[t.item]:undefined,units=d?gemUnits(d):5;
  const quote:GemQuote={allowed:false,reason:'',reasonKey:'',token:JSON.stringify([g.version,g.revision,s.sequence,s.player.gold,s.progression.level,s.progression.secondChapter,kind,args]),gold:0,refundGold:0,drills:0,shards:0,units,stock:0,result:0,...args};
  if(t.item){const v=itemGemView(s,t.item);quote.opened=v.opened;quote.previous=integer(t.hole,4)?v.sockets[t.hole]:null;quote.gem=t.kind==='inlay'&&t.stat&&t.tier?{stat:t.stat,tier:t.tier as GemTier,units}:quote.previous;}
  if(t.kind==='open'){quote.drills=gemOpenCost(t.hole??0,units);quote.gold=quote.drills;quote.stock=g.drills;quote.result=(quote.opened??1)+1;}
  if(t.kind==='inlay'){quote.gold=units;quote.stock=g.bank[gemBankKey(t.stat!,t.tier!)]??0;quote.result=units;}
  if(t.kind==='exchange'){quote.shards=5;quote.stock=g.shards;quote.result=5;quote.fromUnits=5;quote.toUnits=5;}
  if(t.kind==='synthesis'){quote.gold=5*Math.pow(3,(t.tier??1)-1);quote.stock=g.bank[gemBankKey(t.stat!,t.tier!)]??0;quote.result=5;quote.fromUnits=15;quote.toUnits=5;}
  if(t.kind==='transfer'&&t.from&&t.to){quote.source=copy(g.items[t.from]??emptyItem(EQUIPMENT[t.from]));quote.target=copy(g.items[t.to]??emptyItem(EQUIPMENT[t.to]));quote.investment=EQUIPMENT[t.from]?gemOpeningInvestment(quote.source.opened,gemUnits(EQUIPMENT[t.from])):0;}
  if(t.kind==='claim'&&t.claim){quote.bank=copy(t.claim.bank);quote.drills=t.claim.drills;quote.result=Object.values(t.claim.bank).reduce((n,v)=>n+v,0);}
  const access=this.host.availability();
  try {const preview:GemState={...g,bank:{...g.bank},items:copy(g.items),pending:copy(g.pending??emptyPending())},gold=apply(preview,t,s);quote.gold=Math.max(0,gold);quote.refundGold=Math.max(0,-gold)+Math.max(0,(preview.pending?.gold??0)-(g.pending?.gold??0));if(t.kind==='transfer'&&t.to){quote.target=copy(preview.items[t.to]??emptyItem(EQUIPMENT[t.to]));quote.returned=Math.max(0,(preview.pending?.drills??0)-(g.pending?.drills??0));}if(t.kind==='recycle'){quote.returned=Math.max(0,(preview.pending?.drills??0)-(g.pending?.drills??0));quote.investment=quote.refundGold;}if(gold>s.player.gold)throw new Error('reason.noGold');if(s.player.gold-gold>9999)throw new Error('reason.full');if(!access.available){quote.reason=access.reason;quote.reasonKey='reason.busy';}else if(g.transactions.length>=GEM_POLICY.ledgerLimit){quote.reasonKey='reason.recordLimit';quote.reason=gemText('reason.recordLimit');}else quote.allowed=true;}
  catch(error){quote.reasonKey=error instanceof Error?error.message:'reason.invalid';quote.reason=gemText(quote.reasonKey as Parameters<typeof gemText>[0]);}
  return quote;
 }
 open(item:string,hole:number){return this.quote('open',{item:canonicalItem(item),hole});}
 inset(item:string,hole:number,stat:GemStat,tier:number){return this.quote('inlay',{item:canonicalItem(item),hole,stat,tier});}
 remove(item:string,hole:number){return this.quote('extract',{item:canonicalItem(item),hole});}
 synthesis(stat:GemStat,tier:number){return this.quote('synthesis',{stat,tier});}
 exchange(stat:GemStat){return this.quote('exchange',{stat});}
 transfer(from:string,to:string){return this.quote('transfer',{from:canonicalItem(from),to:canonicalItem(to)});}
 reclaim(item:string){return this.quote('recycle',{item:canonicalItem(item)});}
 private pendingClaim(){const s=this.s,g=s.gems,p=g.pending,bank:Record<string,number>={};for(const[key,n]of Object.entries(p.bank)){const take=Math.min(n,GEM_POLICY.capacity-(g.bank[key]??0));if(take>0)bank[key]=take;}return {gold:Math.min(p.gold,Math.max(0,9999-s.player.gold)),drills:Math.min(p.drills,GEM_POLICY.capacity-g.drills),bank};}
 claimPending(){const q=this.quote('claim',{claim:this.pendingClaim()});if(!q.allowed&&q.reasonKey==='reason.noProgress'&&pendingGemView(this.s).available){q.reasonKey='reason.full';q.reason=gemText('reason.full');}return q;}
 private commit(kind:GemActionKind,args:Partial<GemTransaction>,token:string){const quote=this.quote(kind,args);if(!quote.allowed||quote.token!==token)return false;const s=this.s,g=this.g,t={request:'',kind,stage:gemTierCap(s),gold:0,rules:2,...args} as GemTransaction,next=copy(g);t.gold=apply(next,t,s);t.request=this.host.id('gem-'+kind);next.transactions.push(t);next.revision++;s.gems=next;s.player.gold-=t.gold;s.receipts[t.request]=gemSignature(t);this.host.recalculate();this.host.changed();const event=({inlay:'inset',extract:'remove',recycle:'transfer',claim:'claim'} as Partial<Record<GemActionKind,string>>)[kind]??kind;this.host.emit('gems',gemText(('event.'+event) as Parameters<typeof gemText>[0]));return true;}
 openSocket(item:string,hole:number,token:string){return this.commit('open',{item:canonicalItem(item),hole},token);}
 inlay(item:string,hole:number,stat:GemStat,tier:number,token:string){return this.commit('inlay',{item:canonicalItem(item),hole,stat,tier},token);}
 extract(item:string,hole:number,token:string){return this.commit('extract',{item:canonicalItem(item),hole},token);}
 synthesize(stat:GemStat,tier:number,token:string){return this.commit('synthesis',{stat,tier},token);}
 convert(stat:GemStat,token:string){return this.commit('exchange',{stat},token);}
 inherit(from:string,to:string,token:string){return this.commit('transfer',{from:canonicalItem(from),to:canonicalItem(to)},token);}
 recycle(item:string,token:string){return this.commit('recycle',{item:canonicalItem(item)},token);}
 claimPendingReward(token:string){return this.commit('claim',{claim:this.pendingClaim()},token);}
 /** Called after the normal life receipt exists, before XP can change the level. */
 recordHunt(source:string,enemyLevel:number){const s=this.s,event=validHunt(s,source,true);if(!event||enemyLevel!==(event.e.level??1)||enemyLevel<s.progression.level-3)return false;const g=this.g,old=g.hunts[event.key];if(old&&old.cycle>=event.cycle)return false;const total=Object.values(g.hunts).reduce((n,r)=>n+r.count,0)+1,pays=total%10===0;if(pays&&(g.shards+event.chapter*5>GEM_POLICY.capacity||g.drills+event.chapter>GEM_POLICY.capacity))return false;g.hunts[event.key]={cycle:event.cycle,count:(old?.count??0)+1,rewards:(old?.rewards??0)+(pays?1:0)};if(pays){g.shards+=event.chapter*5;g.drills+=event.chapter;this.host.emit('gems',gemText('event.reward',{shards:event.chapter*5,drills:event.chapter}));}g.revision++;this.host.changed();return true;}
 /** Only existing, verified free journey/Boss receipts are accepted; never a payment callback. */
 reward(source:string,shards:number,drills:number){const s=this.s,r={source,shards,drills};if(!validGrant(s,r)||huntSource(source))return false;const g=this.g;if(g.grants.some(x=>x.source===source)||g.grants.length>=GEM_POLICY.ledgerLimit||g.shards+shards>GEM_POLICY.capacity||g.drills+drills>GEM_POLICY.capacity)return false;g.grants.push(r);g.shards+=shards;g.drills+=drills;g.revision++;this.host.changed();this.host.emit('gems',gemText('event.reward',{shards,drills}));return true;}
}

/** Source and transaction replay prevent duplicate grants, minted cuts and hidden socket edits. */
export function validateGems(s:GemHostState){
 const fail=():never=>{throw new Error('无效的宝石材料、镶嵌或培养记录');};const g=s.gems;
 if(!object(g)||!keys(g,['version','revision','shards','drills','bank','items','hunts','grants','transactions','pending'])||g.version!==2||!integer(g.revision,1e8)||!integer(g.shards)||!integer(g.drills)||!object(g.bank)||!object(g.items)||!object(g.hunts)||!Array.isArray(g.grants)||!Array.isArray(g.transactions)||g.grants.length>GEM_POLICY.ledgerLimit||g.transactions.length>GEM_POLICY.ledgerLimit)return fail();
 if(!object(g.pending)||!keys(g.pending,['gold','drills','bank'])||!integer(g.pending.gold,1e8)||!integer(g.pending.drills,1e8)||!object(g.pending.bank)||Object.values(g.pending.bank).some(v=>!integer(v,1e8,1)))return fail();
 const replay=freshGems(),sources=new Set<string>();let hunts=0,rewardCount=0;
 for(const [key,r]of Object.entries(g.hunts)){if(!object(r)||!keys(r,['cycle','count','rewards'])||!integer(r.cycle,1e7,1)||!integer(r.count,1e7,1)||r.count>r.cycle||!integer(r.rewards,r.count)||!validHunt(s,`hunt:${key}:${r.cycle}`))return fail();hunts+=r.count;rewardCount+=r.rewards;const chapter=chapterForArea(key.split(':')[0]);replay.shards+=r.rewards*chapter*5;replay.drills+=r.rewards*chapter;}
 for(const grant of g.grants){if(!validGrant(s,grant)||sources.has(grant.source))return fail();sources.add(grant.source);replay.shards+=grant.shards;replay.drills+=grant.drills;if(!integer(replay.shards)||!integer(replay.drills))return fail();}
 if(rewardCount!==Math.floor(hunts/10)||g.revision!==hunts+g.grants.length+g.transactions.length)return fail();
 const requests=new Set<string>();let sequence=0;
 for(const t of g.transactions){
  if(!object(t)||!['open','inlay','extract','synthesis','exchange','transfer','recycle','claim'].includes(t.kind)||!integer(t.stage,gemTierCap(s),1)||!integer(Math.abs(t.gold),9999)||t.rules!==2)return fail();
  const expected=['request','kind','stage','gold','rules',...(t.kind==='claim'?['claim']:t.kind==='transfer'?['from','to']:t.kind==='synthesis'?['stat','tier']:t.kind==='exchange'?['stat']:t.kind==='recycle'?['item']:t.kind==='inlay'?['item','hole','stat','tier']:['item','hole'])];if(!keys(t,expected))return fail();
  const m=new RegExp(`^gem-${t.kind}:(\\d+)$`).exec(t.request),n=Number(m?.[1]);if(!m||!integer(n,s.sequence,1)||n<=sequence||requests.has(t.request)||s.receipts[t.request]!==gemSignature(t))return fail();requests.add(t.request);sequence=n;
  try {if(apply(replay,t,s)!==t.gold)return fail();}catch{return fail();}
 }
 const receiptKeys=Object.keys(s.receipts).filter(k=>k.startsWith('gem-'));if(receiptKeys.length!==requests.size||receiptKeys.some(k=>!requests.has(k)))return fail();
 const canonical=(v:any):any=>Array.isArray(v)?v.map(canonical):object(v)?Object.keys(v).sort().map(k=>[k,canonical(v[k])]):v;
 const stable=(v:unknown)=>JSON.stringify(canonical(v));
 if(g.shards!==replay.shards||g.drills!==replay.drills||stable(g.bank)!==stable(replay.bank)||stable(g.items)!==stable(replay.items)||stable(g.pending)!==stable(replay.pending))return fail();
}
