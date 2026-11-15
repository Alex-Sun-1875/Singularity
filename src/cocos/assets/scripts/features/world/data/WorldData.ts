import type { AreaDef, Building, EnemySpawn, InteractionDef, Obstacle, Point } from '../../../core/Contracts';
import {installJourney} from '../../journey/data/ChapterJourney';
import {installCampaign} from './CampaignWorld';
import {CAMPAIGN_EVENTS} from '../../campaign/data/CampaignEvents';
import {CAMPAIGN_ENEMY_TEMPLATES} from '../../campaign/data/Campaign';
import {FIELD_DISCOVERIES} from '../../campaign/data/FieldQuests';
import {worldText} from '../locales';
import {installCampaignScenes} from '../../cinematics/data/CampaignScenes';
import {installMonsterEcology} from './MonsterEcology';
import {installGrowingSources,GROWING_SCENES} from '../../equipment/data/GrowingEquipment';
import {installCampaignCombat} from '../../campaign/data/CampaignBattles';

// Local coordinates are metres: +X east and +Z north. Atlas coordinates are
// composition references only; each scene has its own continuous walking space.
export const R1_ROADS: [string, string][] = [
  ['S01','S02'], ['S01','S03'], ['S01','S04'], ['S01','S20'],
  ['S02','S18'], ['S02','S19'], ['S03','S04'], ['S03','S19'],
  ['S04','S07'], ['S04','S08'], ['S05','S19'], ['S05','S06'], ['S05','S07'],
  ['S06','S14'], ['S06','S15'], ['S07','S08'], ['S07','S13'], ['S07','S14'], ['S07','S17'],
  ['S08','S09'], ['S08','S11'], ['S09','S10'], ['S09','S20'], ['S10','S11'],
  ['S11','S12'], ['S11','S17'], ['S12','S13'], ['S12','S16'],
  ['S13','S14'], ['S13','S16'], ['S13','S17'], ['S14','S15'], ['S15','S16'],
];

const p = (x: number, z: number): Point => ({ x, z });
function building(name: string, style: Building['style'], x: number, z: number, width: number, depth: number, height = 6, enter?: string, rotation?: number): Building {
  return { name, style, x, z, width, depth, height, ...(enter ? { enter } : {}), ...(rotation ? { rotation } : {}) };
}
function obstacle(kind: string, x: number, z: number, width: number, depth = width, height = 2): Obstacle {
  return { kind, x, z, width, depth, height };
}
function object(id: string, label: string, action: string, x: number, z: number, description: string, properties: Partial<InteractionDef> = {}): InteractionDef {
  return { id, label, action, x, z, radius: 2.5, description, ...properties };
}
function evidence(id: string, label: string, x: number, z: number, description: string): InteractionDef {
  return object(id, label, 'inspect', x, z, description, { evidence: id });
}
function cache(id: string, label: string, item: string, x: number, z: number, description: string, amount = 1): InteractionDef {
  return object(id, label, 'cache', x, z, description, { item, amount });
}
function enemy(id: string, kind: EnemySpawn['kind'], x: number, z: number): EnemySpawn {
  return { id, kind, x, z };
}
function area(id: string, name: string, subtitle: string, kind: AreaDef['kind'], palette: AreaDef['palette'], width: number, depth: number, atlas: Point, buildings: Building[], objects: InteractionDef[], enemies: EnemySpawn[] = [], obstacles: Obstacle[] = [], spawn: Point = p(0, -12), checkpoint = false): AreaDef {
  return { id, name, subtitle, kind, palette, width, depth, atlas, spawn, buildings, objects, enemies, exits: [], checkpoint,
    obstacles: [...buildings.map(b => ({ x:b.x, z:b.z, width:b.width, depth:b.depth, height:b.height, kind:'building' })), ...obstacles] };
}

// Human scale indoor floors have cut wall segments, rather than solid building
// boxes masquerading as enterable rooms. Four metre door gaps admit both the
// player collider and a readable threshold. All furniture is also collision.
function townRoom(id: string, name: string, subtitle: string, width: number, depth: number, doors: string, objects: InteractionDef[], furniture: Obstacle[], partitions: Obstacle[], palette: AreaDef['palette'] = 'warm'): AreaDef {
  const walls: Obstacle[] = [];
  for (const side of ['north','east','south','west']) {
    const horizontal = side === 'north' || side === 'south';
    const length = horizontal ? width : depth;
    const fixed = (horizontal ? depth : width) / 2 - .3;
    const sign = side === 'south' || side === 'west' ? -1 : 1;
    const add = (along: number, size: number) => walls.push(obstacle('wall',horizontal ? along : fixed*sign,horizontal ? fixed*sign : along,horizontal ? size : .6,horizontal ? .6 : size,id === 'S01-T6' ? 1.3 : 3.2));
    if (doors.includes(side[0])) { const size = (length-4)/2; add(-2-size/2,size); add(2+size/2,size); }
    else add(0,length);
  }
  return area(id,name,subtitle,'interior',palette,width,depth,p(18,40),[],objects,[],[...walls,...partitions,...furniture],p(0,-7),id === 'S01-T1');
}

export const AREAS: Record<string, AreaDef> = {
  S01: area('S01', '石桥镇', '河风穿过铁匠街；旅店、行会与渡口各有真实入口。', 'town', 'meadow', 156, 144, p(18,40), [
    building('第三杯旅店', 'inn', -35,-32,22,18,9,'S01-T1',180),
    building('行会副本室', 'house', 35,32,22,18,8,'S01-T2'),
    building('洛恩的铁匠街', 'workshop', -35,32,22,18,7,'S01-T3'),
    building('渡口转运仓', 'barn', 35,-32,24,18,8,'S01-T4',180),
    building('镇拘留所', 'gate', 0,52,20,10,7,'S01-T5'),
    building('广场回返亭', 'house', 0,-52,14,10,5,'S01-T6',180),
  ], [
    object('s01-cp','石桥镇整备处','checkpoint',0,-12,'长凳与清水旁可以安全整理装备；已领取的物资不会因休整补回。'),
    evidence('s01-streets','镇内街路牌',-8,0,'旅店连渡口街，行会后巷通拘留所；广场上有人等着安全回返者。'),
    evidence('s01-memorial','第七远征阵亡碑',5,9,'碑上称所有人已经阵亡，石缝却卡着近年更换灯油的收据；这不是完整真相。'),
    evidence('s01-riverwall','石桥旧水位',-54,-7,'墙面有三道洪水刻线，南渡的旧仓院曾淹过；桥下河水仍向南流。'),
  ], [], [obstacle('tree',-60,48,4,4,8),obstacle('tree',58,-48,4,4,8),obstacle('crate',49,-17,3,4,2)], p(0,-12), true),

  S02: area('S02','南渡码头','栈桥、坡街与旧仓院之间仍有往来的脚印。','town','marsh',132,112,p(25,17),[
    building('河运旧仓','barn',-28,24,24,16,8), building('坡街船工屋','house',28,23,16,14,7),
    building('栈桥值房','house',29,-29,14,12,5),
  ],[
    evidence('s02-manifest','转运底簿',-28,12,'底簿记下遗物匣的换船日期，信使不是向南逃走，而是返回了劫车隘口。'),
    evidence('s02-rope','新系的渡绳',14,-26,'渡绳结法来自猎场避居者。河道照常通行，不需要替任何人搬箱交货。'),
    evidence('s02-slope','泥坡上的两种车辙',-13,-19,'轻车辙向镇上，宽军车辙绕去旧军需站；坡街是调查的分路口。'),
  ],[],[obstacle('crate',-44,22,4,5,2),obstacle('tree',47,39,4,4,7)]),

  S03: area('S03','农庄与墓园','菜畦外的旧墓墙留下了比碑文更新的痕迹。','wild','meadow',132,120,p(38,28),[
    building('田边农舍','house',-29,-27,18,16,7),building('谷物棚','barn',29,-28,22,16,7),
    building('墓园守夜屋','ruin',28,29,16,12,4),
  ],[
    evidence('s03-witness','篱外的目击记录',-29,-15,'农人看见带测距线的年轻人被押向石场，袖口有一道新鲜炭印。'),
    evidence('s03-graves','没有遗体的纪念墓',19,17,'远征者的名字刻在空墓上，封土里没有棺钉；当年有人急着结束追问。'),
    object('s03-dated-grave','调查 · 空墓上的第二层刻痕','dice_check',19,14,'比对空墓上被改过的日期，看看工役是否在“阵亡”之后仍然留着自己的锤痕。',{check:'grave-record'}),
    evidence('s03-hedge','菜园旁的小径',-12,27,'压低的篱口可以步行绕开主路，通向林间车轮痕；不是需要消耗品的门。'),
  ],[],[obstacle('wall',-37,24,18,2,2),obstacle('wall',36,40,20,2,2),obstacle('rock',-46,-39,5,4,2),obstacle('tree',47,-8,4,4,8)]),

  S04: area('S04','劫车隘口','信使的车仍完整；新的封签盖在旧的拉线痕上。','wild','stone',144,124,p(46,40),[
    building('桥边扣车棚','barn',-32,29,22,14,6),building('高地守望屋','ruin',34,29,16,14,5),
    building('侧口废税房','house',-34,-28,16,14,6),
  ],[
    object('s04-relic','归位车轴，取回遗物匣','recover',-12,4,'车轴支撑和匣锁仍可徒手操作。先解除车前守军，再取回原信和完整星片；主线车不会受损。'),
    object('s04-letter','查看有近日日期的原信','letter',-12,8,'原信写着“请让我们看一次真正的早晨”。纸上是伊芙琳的签名，与旅店的试光样片不同。'),
    evidence('s04-hammer','轴边的新锤痕',-27,18,'三短一长的锤痕来自洛恩工坊，不是灰披军制式维修；有人临行时留下记号。'),
    evidence('s04-blind','高地遮光板',30,17,'把日光挡在星片之外，星点才显出地下没有登记的星座。高地和侧路都能走回车旁。'),
    object('s04-cp','隘口安全转角','checkpoint',0,-18,'石壁转角留出清理装备的位置。救车成功后记录此处，来回走路不会重置守军。'),
  ],[enemy('s04-raider-front','raider',10,6),enemy('s04-raider-axle','raider',18,16),enemy('s04-archer-bank','archer',34,4)],
  [obstacle('rock',-48,3,9,18,6),obstacle('rock',50,22,8,14,6),obstacle('crate',-28,34,3,3,2),obstacle('barrel',28,-12,2,2,2)],p(0,-18),true),

  S05: area('S05','白桦猎场','夜祈在安全营屋旁修弓，猎径从树根与岩脊间分开。','wild','forest',144,124,p(60,24),[
    building('猎人营屋','house',-31,-27,20,14,6),building('晾皮棚','tent',-31,27,16,14,5),
    building('岩脊巡林亭','tower',33,28,12,12,10),
  ],[
    object('s05-nightqi','夜祈：猎径与弓具','merchant',-31,-16,'夜祈先看你的鞋底，再指向伏击地。她售出的路线曾被转卖，实际见到她即可访问独立的猎商库存。',{actor:'nightqi',merchant:'nightqi'}),
    cache('find-a06','白桦树根宝囊','A06',34,-27,'游猎者皮甲缝在干燥的树根囊里，皮革留着旧猎径的弯折；此处只保存这一件装备。'),
    evidence('s05-prints','避开营地的铁靴印',17,8,'铁靴印在猎屋外突然转向，不是普通猎人跟踪兽群；可以沿南侧小径去看。'),
    evidence('s05-keeper','修过的猎径标记',-15,25,'三角刻痕指向可步行的岩脊绕路。夜祈给的是观察方法，不是每条路必有战斗的保证。'),
  ],[],[obstacle('tree',45,-37,4,4,10),obstacle('tree',-47,41,4,4,11),obstacle('tree',47,13,5,5,12),obstacle('rock',36,-40,8,5,3)]),

  S06: area('S06','芦苇避居营','干地平台上的棚屋相互留出门道，炊烟藏在芦苇之后。','camp','marsh',126,108,p(73,10),[
    building('西侧食棚','tent',-26,-24,17,12,5),building('共用修补棚','tent',28,-24,18,13,5),
    building('高台避雨屋','house',-26,24,18,14,6),building('芦苇藏物棚','tent',29,25,15,12,4),
  ],[
    evidence('s06-cook','仍然温热的锅',-12,-20,'锅边列着轮值的人名。这里的人愿意谈通路和失踪者，但不会变成第六个商人账户。'),
    evidence('s06-reed','芦苇内的隐蔽出口',-16,26,'剪断的芦茎让出干地路面，足以让伤者步行撤离；位置只记在自己的日志里。'),
    evidence('s06-routes','传给夜祈的窄纸条',24,13,'纸条记着一辆沿堤道东去的军车，路线标记比猎场旧图新；庄园可能保留付款副本。'),
  ],[],[obstacle('tree',-45,-36,4,4,8),obstacle('crate',-39,25,3,4,2)]),

  S07: area('S07','废磨坊村','街巷绕过水轮院与旧驿房；地窖插销就在地表这一侧。','town','forest',156,144,p(60,52),[
    building('废磨坊与水轮','mill',-34,31,24,20,13),building('旧驿房','inn',35,31,24,18,8),
    building('空置村舍','house',-35,-30,22,16,7),building('村口小工棚','workshop',34,-31,20,16,6),
  ],[
    object('s07-signal','核对猎记上的回短信号','independent_clue',-13,18,'窗板内侧有近日的回短信号，独立证明下城有人居住；不必先信任弥菈才能发现。',{evidence:'s07-living-signal'}),
    cache('find-t02','旧驿房双钉线索箱','T02',35,18,'双钉木箱只存三张黑契封印及对应制作笔记；与陷井谷隐龛的弓是两笔独立收据。',3),
    evidence('s07-huntbook','水轮院猎记',-34,17,'纸页把猎径伏击与地下转运连在一起，末行提醒不要把住处标在公开图上。'),
    evidence('s07-latch','磨坊地窖的普通插销',-11,31,'插销从地表能够直接够到，不耗钥匙，也不需要击败队长。下去后可以原路返回。'),
    evidence('s07-receipts','不同付款方的两张收条',34,-18,'相同货号分别向军营和庄园收款，磨坊不只是藏箱子的空院。两张收条留作后续对质。'),
  ],[enemy('s07-lane-raider','raider',18,0),enemy('s07-lane-shield','shield',32,3),enemy('s07-mill-archer','archer',-17,-8)],
  [obstacle('crate',48,27,3,4,2),obstacle('barrel',17,-16,2,2,2),obstacle('tree',58,-47,4,4,9)]),

  S08: area('S08','陷井谷','谷底采坑与高道相互可见，危险有绕行的余地。','wild','stone',148,136,p(43,67),[
    building('旧采坑吊棚','workshop',-33,-28,20,14,6),building('高道警戒残屋','ruin',34,31,18,14,5),
    building('誓痕隐龛背墙','ruin',-33,30,18,12,4),
  ],[
    cache('find-w08','双线索指向的誓痕隐龛','W08',-33,20,'旧誓道标与废驿收条指向同一处隐龛。银鹿的足迹只有这一把；这里不是第二个地下地窖。'),
    evidence('s08-fault','边坡上的新断层',20,-25,'碎石仍在松动，北侧高道有完整路面；没有必须跳下致命采坑的入口。'),
    evidence('s08-drag','采坑拖痕',-12,5,'拖痕从旧吊架通向军营，但绳结方向显示人曾被活着转运，不是坠崖遗骸。'),
    object('s08-pass','扶正高道的旧誓路标','secret_pass',20,24,'路标露出背面的弯枝记号，证明高道可以安全折返；这一条发现只结算一次。'),
  ],[enemy('s08-pass-warden','raider',35,-5),enemy('s08-pit-archer','archer',15,-6)],
  [obstacle('rock',-39,1,13,14,6),obstacle('rock',43,40,8,9,5),obstacle('rock',-54,-42,7,12,5)]),

  S09: area('S09','灰披军营','外营、军需仓与办公棚分成三个院面，侧后岗哨仍可绕过。','camp','meadow',156,144,p(23,72),[
    building('灰披军需仓','barn',-35,32,24,18,8),building('军饷办公棚','tent',35,32,22,18,6),
    building('西侧兵帐','tent',-35,-31,22,16,6),building('东侧兵帐','tent',35,-31,22,16,6),
  ],[
    cache('find-a01','外营武备箱','A01',-35,18,'白枝护额留在编制已注销的武备箱里，箱号与被扣工役的旧名单一致。'),
    cache('find-a09','篝火旁的旧兵袋','A09',-20,-29,'旧兵袋中的护手“老兵的回敬”经过多次缝补；它与武备箱有独立的发现收据。'),
    evidence('s09-payroll','两列不相符的兵饷名单',35,18,'仍在领饷的人被写成阵亡，付款附约指向湿林庄园。名单可以支持后续交涉。'),
    evidence('s09-sideentry','巡逻换班缝隙',-16,30,'侧后的运水面没有连续岗哨。这里的放行只影响这一处接近面，不会让整个地区停战。'),
    evidence('s09-order','队长的扣押令抄件',17,-28,'扣押令要求星片与有测绘本领的工匠分别移交，北岭哨关保管着原件。'),
  ],[enemy('s09-tax-raider','raider',18,1),enemy('s09-tax-shield','shield',33,0),enemy('s09-back-raider','raider',-19,3),enemy('s09-back-archer','archer',-34,0)],
  [obstacle('crate',-49,32,4,6,2),obstacle('barrel',8,17,2,2,2),obstacle('wall',49,28,3,22,3)]),

  S10: area('S10','北岭哨关','先看盾锤与石墩，再进入关前战场；关后扣货架仍清晰可见。','camp','stone',144,136,p(24,91),[
    building('北岭关墙西段','gate',-29,30,28,12,10),building('北岭关墙东段','gate',29,30,28,12,10),
    building('扣货值房','house',-31,-31,18,14,7),building('哨关修整棚','tent',32,-31,18,14,5),
  ],[
    object('s10-cp','关前安全转角','checkpoint',0,-23,'队长战前可在石墙转角整备。重试保留已完成事件，未败队长恢复完整战斗状态。'),
    evidence('s10-pillar-marks','观察石墩的新撞痕',-11,-12,'两座石墩承受过盾冲。侧走让队长撞墩能制造失衡，零油与基础武器也有完整解法。'),
    object('s10-gate','抬起主横杆，开启扣货架','captain_gate',0,22,'灰披队长败后亲自抬起横杆，领取未熄之誓与这一阶段的固定报酬。武备与主线收据分别去重，战胜本身不会把剑塞进背包。'),
    evidence('s10-detention','带着原封签的扣押令',-31,-20,'原令把活着的工匠写成“设施附属人员”。它能作为证据，普通道路不因此变成剧情出口。'),
  ],[enemy('s10-captain','captain',0,5)],
  [obstacle('pillar',-3,0,1.4,1.4,2.8),obstacle('pillar',3,0,1.4,1.4,2.8),obstacle('barrel',19,13,2,2,2)],p(0,-23),true),

  S11: area('S11','松岬石塔','阶坡绕塔而上，军营、废誓院与谷中道路分别落在视野里。','ruin','stone',132,124,p(52,87),[
    building('松岬塔基','tower',-30,28,18,18,18),building('塔旁守夜屋','house',30,29,18,14,6),
    building('断桥旧亭','ruin',-29,-28,18,12,4),
  ],[
    cache('find-a02','断桥眺望袋','A02',-29,-17,'游隼兜帽藏在眺望点的干燥袋中。这里提供方向与视野，不能隔着整片石壁攻击军营。'),
    evidence('s11-horizon','三处不同的远方轮廓',-15,28,'西北是关墙，东方是坍塌的礼堂，东南有崖边平台；远望只记录地理，不自动发现内部。'),
    evidence('s11-stair','塔基完整的缓阶',-30,15,'石阶沿塔基外侧接回平地，扶手上留有测距线的磨痕；上下层没有跳崖捷径。'),
  ],[],[obstacle('rock',45,-24,8,14,5),obstacle('wall',29,41,20,2,2),obstacle('tree',-48,41,4,4,8)]),

  S12: area('S12','废誓院','坍塌礼堂、侧室与檐廊围成留有退路的旧院。','ruin','stone',144,132,p(77,78),[
    building('坍塌礼堂','ruin',-32,30,28,20,10),building('誓院记录侧室','ruin',33,30,22,16,6),
    building('南侧檐廊残段','ruin',33,-28,24,10,5),
  ],[
    evidence('s12-command','三天轮换的旧命令',33,18,'命令原文许诺三天轮换，后附封条却没有放人记录。它是背景证据，不是万能开门钥匙。'),
    evidence('s12-swordtrace','朝向门内的剑痕',-32,17,'剑痕朝向礼堂内部，旧守卫也许在拦阻离开的人；只有痕迹还不足以指认全部责任。'),
    evidence('s12-coldlight','没有燃料的冷白余光',18,-25,'碎金属在遮光后重复一段手势，记录有缺帧，不能把它当成读心或死者的同意。'),
  ],[enemy('s12-scavenger-raider','raider',10,5),enemy('s12-scavenger-archer','archer',28,4)],
  [obstacle('rock',-45,-28,9,10,4),obstacle('wall',-34,43,30,2,3),obstacle('rock',46,43,6,6,4)]),

  S13: area('S13','旧石场','采面前有工棚与吊料平台，固定梯的绞把在上方这一侧。','wild','stone',148,136,p(80,57),[
    building('露天采面旧支架','workshop',-33,31,24,18,8),building('工役登记棚','house',34,31,20,16,6),
    building('吊料机房','workshop',34,-30,20,16,7),
  ],[
    evidence('s13-witness','工棚留下的目击板',34,18,'有人看见凯尔带着测距线被送进旧采掘廊，他在石壁上刻了可复核的退路标记。'),
    evidence('s13-ladder','固定梯的上方绞把',-12,29,'绞把从地表安全处放下固定梯，之后双向通行；下方未放梯时无法隔墙操作。'),
    evidence('s13-workmarks','新旧不同的工役锤痕',-33,18,'新锤痕压在旧封矿记号上，表明停工记录与实际运作不符；东北的山路通向断岳山驿与仍在征工的矿业聚落。'),
    object('s13-sequence-runes','调查 · 三短一长的检修记号','dice_check',-33,15,'用新旧锤痕还原连动锁的检修顺序。',{check:'quarry-runes'}),
    evidence('s13-sling','可回退的吊料平台',19,-27,'吊索旁留出步行通道，平台不是消耗合成材料的收费传送，也不吞掉学徒关键证据。'),
  ],[enemy('s13-overseer-shield','shield',21,0),enemy('s13-overseer-raider','raider',34,0)],
  [obstacle('rock',-48,-25,9,22,7),obstacle('crate',47,-30,4,5,2),obstacle('rock',48,44,7,8,6)]),

  S14: area('S14','湿林庄园','墙内庭院通账房，侧门保留另一种接近方式。','town','marsh',156,140,p(88,30),[
    building('湿林主宅','house',-35,32,26,20,11),building('独立账房','house',35,32,22,18,7),
    building('林边马厩','barn',-35,-31,24,16,8),building('庄园守门屋','gate',35,-31,20,14,7),
  ],[
    evidence('s14-contract','付款链的第二份契约',35,18,'契约副本把军营军饷与地下工役的费用并列，弥菈附约中的缺项在这里有独立旁证。'),
    evidence('s14-huntroute','被转卖的猎径副图',-35,18,'副图保留了原售图者没有同意公开的住处位置。它会改变之后对刻板的讨论。'),
    evidence('s14-sidedoor','庭院运柴侧门',-18,-28,'侧门通向马厩院，人可以徒步通过；已有名单能帮助解释来意，失败仍有实体绕行面。'),
    evidence('s14-clock','没有署名的押工时刻表',18,-28,'时刻表标出泵院与石场的交接，却不记工匠姓名。它不会因玩家休息自动推进新的扣押。'),
  ],[enemy('s14-yard-shield','shield',18,0),enemy('s14-yard-raider','raider',34,0),enemy('s14-yard-archer','archer',-18,0)],
  [obstacle('wall',-54,29,2,32,3),obstacle('wall',54,29,2,32,3),obstacle('tree',57,-45,4,4,10)]),

  S15: area('S15','古渠泵院','干阶通向西北前厅，旧渠堤道继续伸向东南。','ruin','marsh',144,124,p(93,12),[
    building('古渠泵屋','workshop',-32,28,24,18,8),building('堤路检修所','house',32,28,20,16,6),
    building('废水闸塔','tower',32,-28,12,12,12),
  ],[
    evidence('s15-steps','通往E04的稳定干阶',-15,26,'干阶足够完整，可以普通进入西北前厅并原路返回；前厅深闸的控制位在另一侧。'),
    evidence('s15-canal','人工渠与自然河的分水碑',-17,-26,'渠水来自东南检修系统，与石桥河不是一条会逆坡的河；堤道沿地形折行。'),
    object('s15-r3-boundary','东南堤道：沉钟河湾方向','boundary',50,-12,'这里是真实地理延续的可见入口。沉钟河湾尚未制作，当前停在路障前，不会传送至空场景。'),
    evidence('s15-pressure','旧泵检修图',32,16,'图上把西北前厅与深部闸室分开，证明勘探支口不能直接穿过终堡或领取后期奖励。'),
  ],[],[obstacle('rock',48,41,8,7,4),obstacle('crate',-47,28,3,4,2)]),

  S16: area('S16','东境驿口','关外驿道与旧渠堤路在分路碑前相接，远山仍是远山。','wild','stone',144,128,p(96,67),[
    building('东境驿亭','inn',-31,29,22,18,7),building('石料称重棚','workshop',32,29,20,16,6),
    building('废关检查屋','gate',31,-29,18,14,7),
  ],[
    object('s16-r2-boundary','东北驿道：沉桥高地方向','boundary',50,20,'驿道继续通向沉桥高地，当前只展示未制作地区的地理边缘；发现路牌不会领取下一幕奖励。'),
    evidence('s16-fork','两套不同年代的分路碑',-15,27,'较新的刻字指向矿业聚落，旧字沿渠南下。两条线不是穿过庄园房屋的空中直路。'),
    evidence('s16-mail','退回的矿务函件',-31,16,'函件称矿工需要“继续保障安全”，日期新于停工公告；这只是下一幕可追的钩子。'),
  ],[],[obstacle('rock',-49,-30,8,16,6),obstacle('tree',48,-43,4,4,8)]),

  S17: area('S17','峭壁洞窟','平台与洞厅都有退路，封门只能从地下内侧先解开。','ruin','stone',128,120,p(64,70),[
    building('崖侧残亭','ruin',-28,-28,20,14,5),building('洞口石门框','gate',29,28,20,14,9),
    building('观察者旧旁屋','house',-28,29,18,14,6),
  ],[
    evidence('s17-sealed','只能从内侧解开的石门',16,29,'门楔藏在地下回声洞一侧。地表只能观察封门，追踪线不会让你从这里首次开门。'),
    evidence('s17-track','折回林地的追踪痕',-28,-17,'兽蹄印绕过石门而去，猎径秘密与地下门槛是两件事；平台上没有必须跳下的断崖。'),
    evidence('s17-echo','会重放敲击声的岩缝',-28,18,'岩缝中的白枝金属重复三次旧敲击，间隔完全相同；声音不是门内此刻有人答应。'),
  ],[],[obstacle('rock',44,-25,12,26,8),obstacle('rock',-43,1,9,16,6)]),

  S18: area('S18','旧军需站','旧车道绕仓院返回南渡，墙上只剩过期的转交条。','ruin','meadow',128,112,p(11,12),[
    building('废军需仓','barn',-28,26,24,18,8),building('车道小值房','house',29,26,18,14,6),
    building('旧修车棚','workshop',29,-26,18,14,6),
  ],[
    evidence('s18-transfer','装备已送修的转交条',-28,13,'旧营垒箱里只有送修单，阵线之锚现在由洛恩专售；这里不会再留一双复制装备。'),
    evidence('s18-road','通回码头的旧车道',-14,-23,'青苔下的石轮槽仍连着南渡，军需站是一段调查回环，不是免费领齐装备的第二起点。'),
    evidence('s18-ration','被划掉的配给姓名',29,15,'配给簿划掉了几位被宣布阵亡的工匠，之后仍有同样数量的口粮领用；可以留待独立核对。'),
  ],[],[obstacle('crate',-43,24,4,5,2),obstacle('tree',-43,-35,4,4,9),obstacle('wall',30,39,20,2,3)]),

  S19: area('S19','林间伏击地','箭位高坡、侧路与幸存者躲处围着一段被反复利用的车辙。','wild','forest',144,128,p(45,18),[
    building('高坡箭位残棚','ruin',-32,30,20,14,5),building('幸存者藏身猎屋','house',32,-29,18,14,6),
    building('路旁破车棚','barn',-32,-30,20,14,6),
  ],[
    evidence('s19-hammer','车轮上的三短一长锤痕',-32,-18,'锤痕与洛恩的工坊手法相同；即使先绕去找人，关键线索也不会被油火烧毁。'),
    evidence('s19-survivor','幸存者留下的口述',32,-18,'口述先讲箭从哪里来，再提一位带测距线的年轻人被活着押走；学徒与猎径在同一现场交叠。'),
    evidence('s19-arrowline','提前削好的箭位',-32,19,'箭位早于商队抵达就已修好，说明伏击者拿到了猎径位置，单看军靴印还不能认定泄密者。'),
    evidence('s19-wheeltrack','偏离大道的窄轮痕',-12,23,'窄轮痕通向磨坊，不是每个岔口都藏着同样一队敌人。侧路可以回到现场中心。'),
  ],[enemy('s19-road-raider','raider',15,1),enemy('s19-arrow-archer','archer',-14,2),enemy('s19-flank-raider','raider',31,7)],
  [obstacle('tree',47,34,4,4,11),obstacle('tree',-48,-42,4,4,10),obstacle('rock',47,-39,7,6,4),obstacle('barrel',22,22,2,2,2)]),

  S20: area('S20','铁脊观察台','西侧山脊路径接镇与军营，观察屋旁的旧路标仍能扶正。','wild','stone',128,120,p(8,65),[
    building('铁脊旧警戒屋','house',-28,28,20,16,7),building('山脊观察残塔','tower',29,28,14,14,12),
    building('背风修路棚','workshop',-28,-27,18,14,5),
  ],[
    cache('find-a14','旧路标后的背囊','A14',17,26,'林海行者短靴收在修路人的背囊里，装备独立记录，不被道标事件或材料结算吞掉。'),
    cache('s20-sign-fee','道标背旧驿费袋','gold',-28,16,'驿费袋只剩十五枚旧币，和短靴、道标各有独立收据；普通休整不会补回。',15),
    evidence('s20-sign','扶正旧誓道标',-13,25,'道标背面描着弯枝与双钉，把谷中隐龛同磨坊收条连起来；它不是必需钥匙。'),
    evidence('s20-view','军营侧背的观察位',29,16,'看得到军需仓的运水面，山脊石壁仍会挡住射线；情报要靠亲自接近才能利用。'),
  ],[],[obstacle('rock',44,-25,10,20,7),obstacle('rock',-43,1,8,14,5)]),

  'S01-T1': townRoom('S01-T1','第三杯旅店','公共厅后是客房与厨房，两道侧门实际连着镇内街巷。',36,32,'ews',[
    object('t1-mira','弥菈：一份遗库委托','offer',-5,0,'弥菈把试光样片移到背光处：“拿回遗物匣，先谈清分成。”她衣内另有一份近日求援信抄件。',{actor:'mira',merchant:'mira'}),
    object('t1-lockbox','拆械 · 遗落的铜簧匣','dice_check',4,-5,'无人认领的铜簧匣；沿旧痕拆解锁舌，失败不影响委托。',{check:'inn-lockbox'}),
    evidence('t1-thirdcup','倒扣的第三只杯子',-8,3,'杯底留着旧磨痕。问起给谁，弥菈说是一个欠她钱的人，却没有说出名字。'),
    evidence('t1-sample','只含零散星点的试光样片',-2,4,'样片在背光下才有星点，无法显示完整路线；原信与完整星片仍在隘口的遗物匣里。'),
    evidence('t1-guestbook','旅店最近的住客簿',10,9,'信使先送抄件与样片，再返程运原件。两次来访日期不同，来路可以独立核对。'),
  ],[obstacle('table',-5,3,4,2,.9),obstacle('bench',-5,-2,4,.7,.55),obstacle('shelf',12,13,6,1.2,2),obstacle('table',10,12,3,2,.9)],
  [obstacle('wall',-14,7,8,.5,3.2),obstacle('wall',0,7,12,.5,3.2),obstacle('wall',14,7,8,.5,3.2)]),

  'S01-T2': townRoom('S01-T2','行会办事处与副本室','等候厅通往两间副本室，纸上记录能独立核对。',34,30,'news',[
    object('t2-independent','查阅信使的独立报失副本','independent_clue',-10,9,'报失副本注明遗物匣遭截与近日求援日期。你可以带着不信任独立追查，接约不是唯一入局方式。',{evidence:'t2-courier-copy'}),
    evidence('t2-contract','两份契约的装订孔',10,9,'公开副本比弥菈手里的契约少一页，装订孔证明附约被抽走；后面仍需名单和活人作证。'),
    evidence('t2-notice','行会的证人回返告示',-7,-8,'安全撤回的人在广场登记，再到相应工坊安置；空白栏位不是已经完成的救援。'),
  ],[obstacle('shelf',-11,12,8,1.2,2),obstacle('shelf',11,12,8,1.2,2),obstacle('table',-10,7,4,2,.9),obstacle('table',8,-7,4,2,.9)],
  [obstacle('wall',-13,5,8,.5,3.2),obstacle('wall',0,5,10,.5,3.2),obstacle('wall',13,5,8,.5,3.2)]),

  'S01-T3': townRoom('S01-T3','铁匠街与洛恩工坊','锻造间与测绘小室分开，南面的工作院留着试装空间。',40,32,'ens',[
    object('t3-lorn','洛恩：失踪的测绘学徒','merchant',-11,9,'洛恩认得三短一长的维修锤痕，谈起凯尔时把盾放下。工坊提供阵线之锚的唯一付费来源。',{actor:'lorn',merchant:'lorn'}),
    cache('find-j08','可跳过的整备教学：归乡信物','J08',-5,-5,'洛恩把归乡信物放在教学台上。拿取不要求击打次数，跳过讲解也保留唯一领取记录。'),
    evidence('t3-measure','凯尔未完成的通路图',11,9,'图上每一段退路都有测距，空白指向石场和地下旧居；凯尔想画人人都能走的地图。'),
    evidence('t3-transfer','阵线之锚送修单',11,-7,'旧军需箱中的靴子已经送到此处，价签三十二币；旧箱不会再复制一双。'),
  ],[obstacle('forge',-12,12,5,3,1.5),obstacle('shelf',12,12,8,1.5,2),obstacle('table',10,-10,5,2,.9),obstacle('bench',-12,-9,6,1,.55)],
  [obstacle('wall',-11.5,5,17,.5,3.2),obstacle('wall',11.5,5,17,.5,3.2)]),

  'S01-T4': townRoom('S01-T4','渡口街与镇仓院','北仓与票房隔着装卸门道，临水工作院接回旅店街。',44,36,'ens',[
    evidence('t4-courier','信使到镇的签收印',-12,9,'先到的是不含路线的样片与抄件，第二趟原件没有抵镇。签收印与南渡底簿可交叉核对。'),
    evidence('t4-warehouse','不一致的转运货号',12,9,'同一货号在军营与镇仓出现两种收费标准；这里只是转运证据，不要求跑一趟送货任务。'),
    evidence('t4-watergate','通向南渡的水门街',-5,-10,'街面上的退水线指向真正的南渡码头，镇内部街路不额外充当检查点或传送奖励。'),
  ],[obstacle('shelf',-13,14,10,1.2,2),obstacle('table',12,12,6,2,.9),obstacle('bench',9,-10,5,1,.55)],
  [obstacle('wall',-13,5,18,.5,3.2),obstacle('wall',13,5,18,.5,3.2)],'marsh'),

  'S01-T5': townRoom('S01-T5','拘留所与值房','中央走廊连接值班桌和旧拘留间，外门通行会和广场。',32,30,'wns',[
    evidence('t5-registry','没有审判日期的登记簿',-10,8,'登记簿把工役写成暂押，日期栏却空了十八年；此处与未来的救援结果分别记录。'),
    evidence('t5-watch','值房交接牌',10,8,'镇拘留所只负责本地登记，灰披军的命令不能自动让所有岗哨放行，也不能代替现场救人。'),
    evidence('t5-evidence','证物转交清单',10,-6,'清单指向军营原令，不会凭一张纸就完成队长战或领取扣货架上的装备。'),
  ],[obstacle('table',-10,11,5,2,.9),obstacle('shelf',10,12,6,1.2,2),obstacle('shelf',11,-10,6,1.2,2)],
  [obstacle('wall',-6,10,.5,10,3.2),obstacle('wall',6,10,.5,10,3.2)],'stone'),

  'S01-T6': townRoom('S01-T6','广场与回返接洽点','围合小广场里桌椅等着真实回返的人，石路接行会与铁匠街。',48,40,'news',[
    evidence('t6-return','尚待填写的回返记录',-12,7,'姓名只有在人实际安全撤回后才填上。广场没有复制一位仍在地下的学徒或守卫。'),
    evidence('t6-line','通往工坊的测距刻线',12,7,'凯尔曾沿这条线练习测绘，石路现在仍能通往洛恩工坊；地图需要亲自走过才算可用。'),
    evidence('t6-table','三把不同高度的椅子',12,-9,'椅子为伤者、工匠与普通旅人留出位置。等待回返不会自动产生额外金币或物资。'),
  ],[obstacle('table',-12,10,5,2,.9),obstacle('bench',12,10,6,1,.55),obstacle('shelf',13,-12,6,1.2,1.6)],
  [obstacle('wall',-14,15,14,.6,1.3),obstacle('wall',14,15,14,.6,1.3)],'meadow'),

  'U1-01': area('U1-01','地下货栈','装卸洞厅的旧账架之间仍留着交涉与侧行的空间。','underground','cave',136,116,p(60,52),[
    building('旧账架室','house',-30,27,22,16,5),building('看守卸货房','workshop',31,27,22,16,6),
    building('侧道货物棚','barn',31,-28,22,16,6),
  ],[
    evidence('u101-ledger','仍在更新的转运账',-30,15,'账本记着活人的口粮、劳役和向庄园收款的货号；它同时回应契约与猎径，却不是两次领奖。'),
    evidence('u101-living','用头盔作锅盖的灶痕',16,-25,'锅盖边是今天才落下的面粉，早已宣布阵亡的队伍并没有停止生活。'),
    evidence('u101-watch','可说话的看守留下的便笺',31,15,'便笺提醒交班者别堵住侧通道。局部交涉失败仍可沿另一侧接近，不会把E01永久焊死。'),
  ],[enemy('u101-watch-raider','raider',15,0),enemy('u101-watch-shield','shield',31,0)],
  [obstacle('rock',-47,-26,9,24,6),obstacle('crate',45,28,4,6,3)]),

  'U1-02': area('U1-02','回声洞','天然洞厅里高低岩台相通，石门内楔就在洞侧。','underground','cave',128,116,p(64,70),[
    building('旧测声棚','workshop',-28,27,20,14,5),building('通地表的石门基座','gate',29,27,20,16,9),
    building('岩台避风小室','ruin',-28,-27,18,14,5),
  ],[
    evidence('u102-echo','三次相同的敲击',-28,16,'白枝金属重放同一段敲击，间隔没有变化；记录缺少视角，不能当成此刻的呼救者。'),
    evidence('u102-wedge','E03石门的内楔',16,27,'从这一侧解开门楔，才会把峭壁洞窟变成双向返回出口；门外的人无法隔墙首次操作。'),
    evidence('u102-ramp','连接高低岩台的干坡',-12,-24,'碎石铺出的干坡有完整脚印，从回声源可步行退回货栈，不需要坠落或跳跃系统。'),
  ],[],[obstacle('rock',43,-24,12,22,8),obstacle('rock',-43,0,9,18,5)]),

  'U1-03': area('U1-03','废采掘廊','分段支护把矿道分成岔口，未放下的固定梯只能从上方操作。','underground','cave',144,116,p(80,57),[
    building('西段支护工房','workshop',-33,27,24,16,6),building('矿梯机台','tower',33,27,16,16,10),
    building('东段旧工具间','house',33,-27,22,16,5),
  ],[
    evidence('u103-ladder','固定梯下方的安全立足点',17,27,'这里能够看见上方绞把，但放梯前不能够到它。可以退回E01或已开的E03，不会困在梯底。'),
    evidence('u103-marks','凯尔的退路测量记号',-33,16,'每段岔路都标出可折返的距离，测绘者在尝试让普通工匠也能离开，而不是寻找宝箱。'),
    object('u103-arsenal-boundary','深处军械长廊与绞盘井','boundary',49,-22,'成段矿道继续通往U1-06与U1-09，属于后续幕的未制作空间。当前保留实体封闭面与返回路线。'),
  ],[enemy('u103-prospector-raider','raider',15,0),enemy('u103-prospector-archer','archer',33,0)],
  [obstacle('rock',-49,-27,10,24,7),obstacle('wall',34,42,22,2,4)]),

  'U1-04': area('U1-04','工匠旧居','阵亡者正在吃晚饭。长桌旁留出了测距线和一把空椅子。','underground','warm',144,128,p(68,62),[
    building('工匠共用厨房','house',-33,30,24,18,6),building('伊芙琳的值守居所','house',34,30,24,18,7),
    building('测绘与修补间','workshop',34,-29,24,16,6),building('工匠旧卧房','house',-33,-29,24,16,6),
  ],[
    object('u104-dinner','伊芙琳：阵亡者的晚饭','meeting',-10,6,'伊芙琳按住凯尔跨过碗沿的测距线：“吃完再量。”她问弥菈这次带了几个回来的人，旧关系在现场显露。',{actor:'evelyn'}),
    object('u104-kael','凯尔：复核一张可走的退路图','inspect',11,6,'凯尔先请你走一次自己测出的退路，随后才谈被押工役。他是一位有目标的成年测绘师，不是可领取的人质奖励。',{actor:'kael',evidence:'u104-kael-route'}),
    evidence('u104-bread','用头盔压过的面团',-33,18,'头盔边还沾着面粉，桌边每个人都真实吃饭。碑上被宣布阵亡的姓名与眼前生活互相矛盾。'),
    evidence('u104-lamp','十八年换过的灯罩',34,18,'灯罩修补了许多次，伊芙琳仍在准备撤离；继续值守不是别人可以替她默认的选择。'),
    object('u104-finish','核对撤离与扣押令，结束第一幕','finish',0,-25,'确认救援已实际完成、灰披扣押令与星片分别结算。第一幕到此收尾，后续地区仍需要制作，不生成空地图。'),
    object('u104-cp','工匠公共空地整备','checkpoint',0,-12,'公共空地可安全整备和保存，已获证据、已解救的人与地下门楔不会因普通回访重置。'),
  ],[],[obstacle('crate',-49,28,4,5,2)],p(0,-12),true),

  'U1-05': area('U1-05','囚工监区','值房、工作带与检修侧廊围着真实的囚室，正门不是唯一接近面。','underground','cave',148,128,p(72,58),[
    building('西侧囚工房','gate',-34,30,26,18,7),building('监工值房','house',35,30,24,18,7),
    building('强制工作带','workshop',35,-30,26,18,7),building('检修工具小室','house',-34,-29,20,16,5),
  ],[
    object('u105-release','解除囚室横闩，释放工役','release_workers',-34,17,'囚室横闩由工作带控制。先处理现场守卫或通过检修侧廊解除陷阱，再真正带人离开危险位置。'),
    object('u105-trap','从检修侧廊拆除诱片','disable_trap',-34,-17,'侧廊可以徒步接近诱片背面。拆除是可选的接近方式，不消耗关键证据，也不要求先做满人物支线。'),
    object('u105-precision-disarm','拆械 · 逆转诱片连动锁','dice_check',-31,-17,'按检修痕迹逆转连动锁；失败消耗20专注，仍可沿侧廊或击败守军救援。',{check:'undercity-disarm'}),
    evidence('u105-list','附有活人指印的工役名单',35,17,'名单上的指印与军营阵亡栏对应，活人证据揭开契约附约；读取和救援不是同一个动作。'),
    evidence('u105-tools','被扣下的测距工具',35,-17,'工具仍标着凯尔的刻线。归还工具不会自动获得他的原谅，安全撤离与后续合作分别处理。'),
    object('u105-furnace-boundary','通往回声工坊的深廊','boundary',-50,33,'工作带后继续通向U1-06与U1-07，深层炉厅留待下一幕；这里没有凭空生成新Boss或新装备。'),
  ],[enemy('u105-overseer-shield','shield',18,1),enemy('u105-overseer-raider','raider',34,0),enemy('u105-corridor-archer','archer',-18,0)],
  [obstacle('crate',49,28,4,5,3),obstacle('barrel',9,22,2,2,2),obstacle('rock',-52,-30,7,18,6)]),

  'U2-01': area('U2-01','沉钟地宫·西北前厅','干阶、泵管与深闸构成一个能原路返回的勘探前厅。','underground','cave',120,108,p(93,12),[
    building('西北检修侧室','workshop',-27,25,22,16,6),building('深闸石框','gate',28,25,22,18,10),
    building('旧探勘休息室','house',28,-25,20,14,5),
  ],[
    evidence('u201-dry','来自泵院的稳定干阶',-14,-22,'干阶通回古渠泵院，前厅内没有水下操作或一次性跳落；随时可以沿原路回到地表。'),
    evidence('u201-gate-map','深闸内侧控制示意',-27,14,'控制位明确画在U2-03一侧，要从河湾旧堂等合法道路进入深部再开；前厅不直通终堡。'),
    object('u201-deep-gate','从U2-03内部才能开启的深闸','boundary',28,13,'隔着闸门能看见退水石渠，当前未制作水道长厅与闸室；没有可用的传送连接，也不会发后期主奖。'),
    evidence('u201-pipe','冷水管上的旧检修符号',28,-14,'符号与泵院检修图一致，冷水阴影仍保留青灰；地下暖灯不会把整片水道染成黄色。'),
  ],[],[obstacle('rock',43,38,6,7,5)]),
};

type Side = 'north'|'east'|'south'|'west';
function sideToward(from: AreaDef, to: AreaDef): Side {
  const dx = to.atlas.x - from.atlas.x, dz = to.atlas.z - from.atlas.z;
  return Math.abs(dx) > Math.abs(dz) ? (dx > 0 ? 'east' : 'west') : (dz > 0 ? 'north' : 'south');
}
function borderPoint(area: AreaDef, side: Side, along: number, inset: number): Point {
  return side === 'east' ? p(area.width/2-inset,along) : side === 'west' ? p(-area.width/2+inset,along)
    : side === 'north' ? p(along,area.depth/2-inset) : p(along,-area.depth/2+inset);
}

// Road gates are at actual scene borders. Distinct ports on the same side leave
// broad, visible approach space; loading places the walker behind the matching
// reciprocal gate rather than at an unrelated scene centre.
const roadPorts = new Map<string,{ at: Point; entry: Point }>();
for (const current of Object.values(AREAS).filter(a => /^S\d\d$/.test(a.id))) {
  for (const side of ['north','east','south','west'] as Side[]) {
    const neighbors = R1_ROADS.flatMap(([a,b]) => a === current.id ? [b] : b === current.id ? [a] : []).filter(id => sideToward(current,AREAS[id]) === side)
      .sort((a,b) => (side === 'north' || side === 'south') ? AREAS[a].atlas.x-AREAS[b].atlas.x : AREAS[a].atlas.z-AREAS[b].atlas.z);
    neighbors.forEach((id,i) => {
      const length = side === 'north' || side === 'south' ? current.width : current.depth;
      const along = neighbors.length === 1 ? 0 : (i-(neighbors.length-1)/2)*Math.min(20,length/(neighbors.length+2));
      roadPorts.set(`${current.id}:${id}`, { at:borderPoint(current,side,along,2),entry:borderPoint(current,side,along,6) });
    });
  }
}
for (const [a,b] of R1_ROADS) {
  const ap = roadPorts.get(`${a}:${b}`)!, bp = roadPorts.get(`${b}:${a}`)!;
  AREAS[a].exits.push({ id:`road-${a}-${b}`,to:b,label:`前往${AREAS[b].name}`, ...ap.at, entry:bp.entry });
  AREAS[b].exits.push({ id:`road-${b}-${a}`,to:a,label:`返回${AREAS[a].name}`, ...bp.at, entry:ap.entry });
}

function passage(a: string, b: string, aPoint: Point, bPoint: Point, id: string, aLabel: string, bLabel: string, flag?: string): void {
  const landing = (definition: AreaDef, gate: Point): Point => {
    const target = definition.spawn, length = Math.hypot(target.x-gate.x,target.z-gate.z);
    return length < 3.5 ? {...target} : p(gate.x+(target.x-gate.x)/length*3.5,gate.z+(target.z-gate.z)/length*3.5);
  };
  AREAS[a].exits.push({ id:`${id}-${a}`,to:b,...aPoint,label:aLabel,entry:landing(AREAS[b],bPoint),...(flag ? {unlock:flag} : {}) });
  AREAS[b].exits.push({ id:`${id}-${b}`,to:a,...bPoint,label:bLabel,entry:landing(AREAS[a],aPoint),...(flag ? {requires:flag} : {}) });
}

// Actual doors in the town exterior; interior passages preserve the T1–T6
// walking graph, while every district also has its own visible street door.
for (const [n,door] of [[1,p(-35,-20)],[2,p(35,20)],[3,p(-35,20)],[4,p(35,-20)],[5,p(0,44)],[6,p(0,-44)]] as [number,Point][]) {
  const insideDoor = n === 6 ? p(22.4,0) : p(0,-AREAS[`S01-T${n}`].depth/2+1.6);
  passage('S01',`S01-T${n}`,door,insideDoor,`door-town-${n}`,`进入${AREAS[`S01-T${n}`].name}`,'回到石桥镇街面');
}
passage('S01-T1','S01-T2',p(16.4,0),p(-15.4,0),'town-lane-12','沿后巷去行会','沿后巷回旅店');
passage('S01-T2','S01-T6',p(0,13.4),p(0,-18.4),'town-lane-26','步行前往广场','回行会办事处');
passage('S01-T6','S01-T3',p(-22.4,0),p(18.4,0),'town-lane-63','穿过广场去铁匠街','沿石路回广场');
passage('S01-T3','S01-T4',p(0,14.4),p(0,16.4),'town-lane-34','沿坡街去仓院','沿坡街回工坊');
passage('S01-T4','S01-T1',p(20.4,0),p(-16.4,0),'town-lane-41','沿渡口街去旅店','回渡口街仓院');
passage('S01-T5','S01-T2',p(-14.4,0),p(15.4,0),'town-lane-52','沿值房侧道去行会','沿侧道去拘留所');
passage('S01-T5','S01-T6',p(0,13.4),p(0,18.4),'town-lane-56','由正门去广场','走向拘留所值房');

passage('S07','U1-01',p(-15,32),p(0,-54),'E01','拉开普通插销，走下磨坊地窖','沿干阶回废磨坊村','e01_open');
passage('S13','U1-03',p(-14,32),p(0,54),'E02','从上方放下固定梯，进入采掘廊','攀梯回旧石场','e02_open');
passage('U1-02','S17',p(16,30),p(15,30),'E03','从内侧解开石门，走向峭壁洞窟','通过已解开的石门回声洞','e03_open');
passage('S15','U2-01',p(-15,30),p(0,-50),'E04','沿稳定干阶进入西北前厅','沿干阶回古渠泵院');
passage('U1-01','U1-02',p(-66,0),p(62,0),'u1-corridor-0102','沿岩廊去回声洞','沿岩廊回地下货栈');
passage('U1-01','U1-03',p(66,0),p(-70,0),'u1-corridor-0103','进入分段支护的采掘廊','沿装卸道回地下货栈');
passage('U1-01','U1-04',p(0,56),p(0,-62),'u1-corridor-0104','顺着面包气味去工匠旧居','沿公共通道回地下货栈');
passage('U1-02','U1-04',p(0,56),p(-70,0),'u1-corridor-0204','沿干坡去工匠旧居','从居所侧门去回声洞');
passage('U1-04','U1-05',p(70,0),p(-72,0),'u1-corridor-0405','穿过工作带去囚工监区','沿检修通道回工匠旧居');

installCampaign(AREAS);
installMonsterEcology(AREAS);
installCampaignCombat(AREAS);
installGrowingSources(AREAS);
installJourney(AREAS);
installCampaignScenes(AREAS);
// Prerequisites name their real source and location rather than internal flag IDs.
for(const event of Object.values(CAMPAIGN_EVENTS))for(const flag of [...event.requires??[],...event.requiresAny??[]]){
 if(event.prerequisiteHints?.[flag])continue;
 const source=Object.values(CAMPAIGN_EVENTS).find(e=>e.sets?.includes(flag)||e.choices?.some(c=>c.sets.includes(flag)));
 const legacy:Record<string,string>={workers_released:'release_workers',gate_raised:'captain_gate'};
 const clue=Object.values(AREAS).flatMap(area=>area.objects.filter(o=>o.evidence===flag||legacy[flag]&&o.action===legacy[flag]).map(object=>({area,object})))[0];
 const area=source?AREAS[source.area]:clue?.area,label=source?.label??clue?.object.label;
 const boss=flag.startsWith('boss_defeated:')?flag.slice(14):'',arena=boss?Object.values(AREAS).find(a=>a.enemies.some(e=>e.bossId===boss)):undefined;
 const discovery=FIELD_DISCOVERIES.find(d=>d.flag===flag),scene=GROWING_SCENES.find(s=>s.flag===flag);
 const hint=area&&label?worldText('interaction.prerequisite',{area:area.name,label}):arena?worldText('interaction.defeat',{area:arena.name,label:CAMPAIGN_ENEMY_TEMPLATES[boss]?.name??arena.name}):discovery?worldText('interaction.discovery',{chapter:discovery.chapter,name:discovery.name}):scene?worldText('interaction.investigate',{area:AREAS[scene.area].name,label:scene.label}):flag==='workers_returned'?worldText('interaction.returnWorkers'):undefined;
 if(hint)(event.prerequisiteHints??={})[flag]=hint;
}


export function getArea(id: string): AreaDef {
  const found = AREAS[id];
  if (!found) throw new Error(`Unknown or unbuilt area: ${id}`);
  return found;
}
