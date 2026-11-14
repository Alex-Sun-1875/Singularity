"""Build the authored campaign catalog and review documents; no runtime mutation.

Reuses v3 geography, the exported Cocos inventory and existing cloud concept art.
Only Python stdlib is needed. Run from any directory with Python 3.10+.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / 'source-art/encounters/cloud-world-v2'
DOC = ROOT / 'docs/design'

REGIONS = [
    dict(id='R1', old='石桥边地', name='铁誓边境', act=1, plate='r1-stonebridge.png', theme='钢灰、锈红、林绿；人类雇佣军与猎径陷阱', pool='P_R1'),
    dict(id='R2', old='沉桥高地', name='断岳高地', act=2, plate='r2-highlands.png', theme='石蓝、松绿、冷银；矿兵与废弃采掘机', pool='P_R2'),
    dict(id='R3', old='沉钟河湾', name='风暴河湾', act=3, plate='r3-bellriver.png', theme='海青、煤黑、琥珀；码头佣兵与古代钟卫', pool='P_R3'),
    dict(id='R4', old='灰石城域', name='黑冠城域', act=4, plate='r4-greyrock.png', theme='夜蓝、蓝钢、象牙白；盾阵、重弩与警戒镜', pool='P_R4'),
    dict(id='U1', old='旧誓下城', name='誓火深城', act=2, plate='u1-oathcity.png', theme='旧青铜、灰石、冷白炉光；机械遗卫与囚工看守', pool='P_U1'),
    dict(id='U2', old='沉钟地宫与旧水道', name='沉钟禁域', act=3, plate='u2-catacombs.png', theme='铜绿、灰白石、深蓝、紫晶；闸卫与档案机械', pool='P_U2'),
]

# id | display name | HP | hit damage | windup/lock/recovery seconds | tell/counter | role
MOB_ROWS = '''
R1-1|灰披刀兵|72|12|0.65/0.20/0.65|举棍亮扇；侧移或推断起手，圆盾不提供重盾减伤|近战
R1-2|铁板盾卫|105|16|0.75/0.25/0.85|抬方盾亮直道；绕背、推断抬盾|盾阵
R1-3|猎径弩手|60|14|1.10/0.30/1.80|虚线转实线；侧走、掩体、趁装填接近|远程
R1-4|绊索猎兵|66|10|1.20/0.35/1.10|蹲身展开可见绊索；跨旁路或攻击索桩，索命中仅减速20%持续1s|控场
R2-1|裂岩镐卫|118|18|0.90/0.30/1.00|镐头过肩、狭长红槽；横移后从侧面攻击|重击
R2-2|岩脊弩哨|88|16|1.20/0.35/1.90|高处弩光与弦响；石垛遮线，必须有步行可达的上坡|远程
R2-3|废矿爬机|96|14|1.00/0.30/1.20|四足压低、钳口亮弧；离开弧面，后腿转向慢|机械近战
R2-4|断岳号兵|90|12|1.50/0.40/1.30|举号出现圈纹；推断号声，否则现有同组敌未来一次起手缩短0.10s且不低于0.65s，不增援|支援
R3-1|码头快刀|100|14|0.70/0.25/0.80|屈膝亮短扇；退一步，出手后侧击|近战
R3-2|黑油投手|90|12|1.20/0.35/1.00|举陶罐、斜线圆；推断或离开落区，火区4/s持续3s|区域压制
R3-3|青铜钟卫|140|18|1.15/0.35/1.30|钟腹倾斜、地面环带；走进内圈或退外圈，警示无声模式也可读|机械重击
R3-4|拖钩打手|116|16|1.00/0.30/1.15|钩杆后收、窄直道；横移，命中推移0.6m且不拖入水中|位移
R4-1|黑冠盾兵|150|18|0.85/0.30/1.00|半圆钢盾抵地；绕侧、推断起盾|盾阵
R4-2|堡垒重弩手|104|20|1.40/0.40/2.10|重弩架定、长实线；石垛遮挡，禁止穿墙|远程
R4-3|折镜工兵|112|14|1.50/0.40/1.30|实体镜框转亮并画窄光带；离开光带、攻击镜架可打断，不能反射全部玩家法术|控场
R4-4|铁旗军士|164|20|1.00/0.30/1.20|旗杆下压、两段各有扇形；退圈等第二击结束，号令仅移动现有同伴|精锐近战
U1-1|铸炉卫兵|120|17|1.00/0.30/1.10|锤臂拉后亮矩形；侧移、打膝关节|机械近战
U1-2|鸣震甲虫|54|9|0.85/0.25/0.90|六足停步触角发亮；离开小圈，按一组两只计且不会分裂生新怪|机械群体
U1-3|提灯狱卒|100|15|1.00/0.30/1.00|灯举高、钩杆直线；绕柱，推断前摇；投降后不再判敌|人类看守
U1-4|负重搬机|160|20|1.40/0.40/1.50|配重架升起、方形落点；走出方框，搬机不投掷任务物|机械重击
U2-1|渠底爬卫|104|13|0.90/0.30/1.00|钩足张开亮四角；侧移，在干道战斗不用游泳|机械近战
U2-2|铭板守卫|146|18|1.10/0.35/1.20|石板护身、棍击短扇；诱挥后绕背|盾阵
U2-3|巡游镜眼|68|12|1.30/0.35/1.30|单镜头光点沿地走；打实体镜头或侧移，漂浮高度仍在所有基础武器命中范围|机械远程
U2-4|撞钟傀儡|156|19|1.35/0.40/1.40|木槌抬起、缺口环带；去缺口或推断起手，钟声不召幽魂|机械控场
'''

MOBS = []
for row in MOB_ROWS.strip().splitlines():
    key, name, hp, damage, timing, counter, role = row.split('|')
    windup, lock, recovery = map(float, timing.split('/'))
    MOBS.append(dict(id=key, name=name, region=key.split('-')[0], hp=int(hp), damage=int(damage),
                     windup=windup, lock=lock, recovery=recovery, counter=counter, role=role))

# New design keys deliberately cannot be confused with equip-able runtime IDs.
# id | region | name | slot | grade | weight | effect | silhouette
GEAR_ROWS = '''
DR1-01|R1|铁誓护盔|头|精良|30|最大生命+6|灰铁眉梁、暗红衬布
DR1-02|R1|佣兵护胸|身|精良|30|受到物理伤害-4%|皮革叠钢胸片、可见铆钉
DR1-03|R1|裂隘护手|手|稀有|20|推击命中普通敌后，下次直接近战+8%，持续3s，CD6s|护指凿纹、粗钢关节
DR1-04|R1|猎隙指环|戒|稀有|20|命中超过5m目标恢复专注2，CD4s|灰银环、绿色窄晶
DR2-01|R2|矿脊护胫|靴|精良|30|受普通敌推移距离-10%|钢趾、岩屑磨痕
DR2-02|R2|断岳兜帽|头|精良|30|最大生命+8|灰蓝羊毛、铜护眉
DR2-03|R2|碎岩短杖|单手杖|稀有|20|R直接命中盾挡普通敌额外削韧4，CD6s；Boss额外削韧2|石英杖首、青铜束圈
DR2-04|R2|山风吊坠|项链|稀有|20|闪避后下一次蓄力箭耗时-8%，3s内一次，CD8s|开口铜翼、淡绿晶
DR3-01|R3|潮痕皮靴|靴|精良|30|火抗+6%|油浸皮面、青布绑带
DR3-02|R3|水手护腕|手|精良|30|最大生命+8|绳结扣、黄铜腕片
DR3-03|R3|破浪弯刀|单手剑|稀有|20|直接近战命中正在燃烧的目标恢复专注3，CD3s；不引爆火区|单刃弧刀、铜护手
DR3-04|R3|雷潮指环|戒|史诗|20|造成直接雷伤后，下次主攻击+6%，持续4s，CD8s|分叉银架、琥珀与蓝晶
DR4-01|R4|黑冠卫盔|头|稀有|30|最大生命+10|蓝钢半盔、象牙色护眉
DR4-02|R4|城垒护甲|身|稀有|30|受到物理伤害-5%|分层半板、夜蓝厚布
DR4-03|R4|破城长剑|单手剑|史诗|20|主攻击命中盾挡敌后，下次推击削韧+4，3s内一次，CD6s；Boss+2|长窄钢刃、开架银护手
DR4-04|R4|禁卫指环|戒|史诗|20|生命首次低于35%获得护盾8持续4s，CD20s，不叠加同名效果|双环黑银、蓝方晶
DU1-01|U1|炉工护额|头|精良|30|火抗+6%|隔热皮额带、灰铜眉片
DU1-02|U1|深城工装|身|精良|30|最大生命+8|皮围甲、暗白布层
DU1-03|U1|震纹护手|手|稀有|20|直接攻击机械敌额外削韧2，CD3s；Boss+1|测量刻痕、冷白窄嵌线
DU1-04|U1|冷焰短杖|单手杖|稀有|20|每第三次直接杖弹命中追加奥术4，CD3s，不再触发计数|封闭铜笼、白石核心
DU2-01|U2|铭廊软靴|靴|稀有|30|冰抗+6%|深蓝布、单道银缝
DU2-02|U2|覆文护腕|手|稀有|30|最大专注+10；换装不补当前专注|铭板分片、哑银铰链
DU2-03|U2|听潮护符|项链|史诗|20|直接主攻击命中冰缓敌恢复专注3，CD4s|钟形银框、冷蓝晶
DU2-04|U2|禁域短弓|双手弓|史诗|20|蓄力箭命中已标记敌额外奥术4，CD4s；额外伤害不复制标记|窄木肢、三环镜扣
DE01|R1|断镐印戒|戒|稀有|0|推断普通敌起手后，下次直接主攻击+10%，3s内一次，CD8s；Boss仅明示可打断窗触发|镐形铁印、琥珀
DE02|R2|裂风长弓|双手弓|史诗|0|蓄力箭命中后2s移动+8%，CD5s；R仍用标准穿甲箭|不对称风叉、双浅绿晶
DE03|R3|深潜者护手|手|史诗|0|脱战3s后专注自然恢复+1/s；总恢复≤8/s|青皮、船缆黄铜扣
DE04|R4|铁棘战靴|靴|史诗|0|受到普通敌推移-15%；闪避后下次近战削韧+3，3s内一次，CD8s|低矮铁棘后跟、关节踝甲
DE05|U1|震炉战锤|单手锤|史诗|0|R命中机械敌额外削韧6，CD6s；Boss+3，削韧失衡遵守共享保护|双错位锤面、冷白共振槽
DE06|U1|三誓长剑|单手剑|史诗|0|每第三次直接近战命中得护盾4持续3s，CD8s；不叠加自有护盾|三叉银护手、三颗象牙晶
DE07|U2|深闸轮盾|副手盾|史诗|0|沿用持续格挡耗专注10/s；成功挡住一次远程物理后回专注3，CD4s，不能正收益永续格挡|偏心闸轮、旋齿银缘
DE08|U2|覆文镜匣|副手法器|史诗|0|符咒直接命中后下次杖弹+8%，4s内一次，CD6s；不返符不复制符|双镜翼、闭合紫晶光笼
'''
GEAR = []
for row in GEAR_ROWS.strip().splitlines():
    key, region, name, slot, grade, weight, effect, visual = row.split('|')
    GEAR.append(dict(id=key, region=region, name=name, slot=slot, grade=grade, weight=int(weight),
                     effect=effect, visual=visual, runtimeStatus='design-only'))

# id | region | arena | name | hp | fixed loot event | drop | moves
BOSS_ROWS = '''
B01|R1|S10|裂隘统领·灰披队长|360|M2|W02+T03×3|锤横扫：0.80s前摇/末0.25s锁向，150°×2.1m，22伤，后摇1.00s；盾冲：1.00/0.35s，3.8m直道24伤，撞墩失衡1.50s；半血横扫追加：另给0.60s短扇，14伤，后摇1.20s
B02|R2|H08|断岳铁卫·守桥铠卫|150|M4|W03+A05|抬盾直推：0.75/0.25s，1.2m、16伤，后摇0.85s；两名岩脊弩哨各1.20s瞄准错开攻击槽；架盾受推0.50m、失衡0.25s，绕背无盾减伤，不加第二生命条
B03|R3|B10|黑油屠夫·灰烬掠夺者|132|M6|W10+J05|举壶投油：1.20/0.35s，直接12伤、火区4/s×3s，回收1.00s/CD3.50s；只布最多2个敌方危险位且留干路；两快刀一弩手固定随从，首领受推1.35m，不加狂暴与新援兵
B04|R4|F13|黑冠统帅·阿德里安|540|M7|W06|重斩两段：0.85/0.25s→22伤，另0.65s提示→18伤，后摇1.35s；盾冲：1.05/0.35s，4.8m、26伤，撞墩失衡1.40s；半血号令1.40s后两内弩口依次锁线1.00s各16伤，仅一轮，外弩台不复活
E01|R1|S13|断镐监工|240|V_E01|DE01|裂地镐：0.95/0.30s窄直道18伤，后摇1.10s；横拉绳：1.20/0.35s地面绳带12伤与20%减速1s，后摇1.20s，可砍索；半血收灯：1.10s举灯后横扫16伤，亮扇照常可见、无熄屏
E02|R2|H14|裂风督猎|280|V_E02|DE02|双风箭：首箭1.25/0.35s、第二箭另0.70s提示，各14伤，后摇1.60s；钉地箭：1.30/0.40s圆落点16伤，留下可破坏索桩4s；半血换岩位：沿可见山路走位2s，无瞬移无无敌
E03|R3|B14|沉船打捞王|320|V_E03|DE03|拖钩：1.10/0.35s直道18伤推0.6m，后摇1.20s；缆绳横扫：1.20/0.35s扇形20伤，后摇1.40s；半血吊锚：1.50/0.50s固定圆落点22伤，锚落后站立恢复1.80s，无必死落水
E04|R4|F17|铁棘典狱长|300|V_E04|DE04|钉甲盾推：1.00/0.35s直道20伤，后摇1.20s；锤击两段：1.10s起手18伤，另0.75s提示14伤，后摇1.50s；钥链锁道：1.40s可打断，画一条可绕锁链，12伤，不封唯一退路
E05|U1|U1-07|震炉巨像|400|V_E05|DE05|双锤落地：1.40/0.40s两个固定方框各22伤，同招只结一次，后摇1.60s；冷光泄压：1.60/0.50s带缺口环带18伤，后摇1.50s；半血过载：1.80s明确屈膝后重复一次锤击，暴露膝齿1.80s，无锁血
E06|U1|U1-06|三刃守誓阵|330|V_E06|DE06|第一剑：0.90/0.30s扇形16伤；第二剑：另0.85s矩形16伤；第三剑：另1.10s窄直道20伤朝门内，三击后1.80s全阵恢复；半血顺序仍1→2→3，仅第三剑多一道有缺口扇形，各段不重叠堵满地面
E07|U2|U2-03|深闸镇守|380|V_E07|DE07|闸轮盾撞：1.20/0.40s直道22伤，后摇1.40s；配重砸击：1.50/0.45s方框24伤，后摇1.60s；半血泄流：1.80s提示两道交替光槽各16伤，干石侧道始终安全，无淹水倒计时
E08|U2|U2-07|覆文守秘者|360|V_E08|DE08|双镜扫线：1.40/0.40s先左后右各14伤，每束独立0.80s提示，后摇1.50s；铭板落印：1.50/0.50s两小圆18伤，后摇1.40s；半血开镜：1.80s中枢聚光后20伤直线，完成后暴露镜芯2.00s，远近均可命中
'''
BOSSES = []
def boss_key(key, region=None):
    return 'BOSS_'+region if key.startswith('B') else 'ELITE_'+key[1:]

for row in BOSS_ROWS.strip().splitlines():
    key, region, arena, name, hp, event, loot, moves = row.split('|')
    BOSSES.append(dict(id=boss_key(key,region), region=region, arena=arena, name=name, hp=int(hp),
                       rewardEvent=event, fixedLoot=loot, moves=moves,
                       mandatory=key.startswith('B'), runtimeStatus='B01 mechanics exist; other encounters design-only' if key == 'B01' else 'design-only'))

# All 91 v3 locations plus 6 town interiors. Encounter strings use catalog keys.
# node | display name | type | encounter | active objective | payoff | approach/retreat
LEVEL_ROWS = '''
S01|石桥镇|安全枢纽|无|接寻宝合约，核对阵亡碑与近日油票|M1预支；商店；回镇人物场景|镇内6内景互通，不把检查点变远程商店
S02|南渡码头|调查|无|两份转运底簿比对，查出军车改道|Q3线索；金币20|沿坡街回镇，码头不强制搬货
S03|空誓墓园|调查|无|空墓日期与新锤痕比对|首次调查铁2+金币20|田埂与旧墓门均可退，不惊扰居民开战
S04|血刃隘口|主线战斗|R1-1×2+R1-3×1|分批救信使、归位车轴、亲读原信|M1夺匣包|高坡绕后、正面分批；任务车不毁，战前后均有退路
S05|白桦猎场|安全/跟踪|无|夜祈示范脚印，选择猎径|固定A06；夜祈商店；Q2起点|猎商营地安全，未知猎径先观察
S06|芦苇避居营|安全/人物|无|伤者指出押运去向，决定是否公开住处|Q2旁证；铁2+金币20|只登记同意公开的道路，不向营地引怪
S07|断轮磨坊|据点|R1-1×1+R1-2×1+R1-3×1|核对回短信号，开地窖E01|固定T02×3+C14；P_R1机会|正门、侧巷或付款副本交涉；E01可原路退
S08|陷井谷|野外战|R1-4×1+R1-1×2（含原隘口监守）|砍可见索桩、沿高道找誓痕隐龛|固定W08；原隐匣18%/监守25%传奇另算；P_R1机会|高道可绕，谷底不设强制跳落
S09|灰披军营|据点|R1-2×1+R1-3×1+R1-1×2|取扣押名单与兵饷副本|固定A01；Q1/Q3旁证；据点包|交涉、帐后侧入、战斗三选；离场不重生
S10|裂隘关|主线首领|B01|击败队长后亲手抬杆|M2包；W02+T03×3独立待领|场外检查点、12×10m战场、两石墩；死亡释放软边界
S11|松岬哨塔|观察战|R1-3×1+R1-1×1|沿实体阶坡到塔顶看军营|固定A02；P_R1机会|塔脚硬掩体、弩手可步行接近
S12|铁誓残院|遗迹/支线|R1-2×1+R1-4×1|观察空基座，找搬运簿|Q1起点；金币30+铁3|沿檐廊避正面，原铭牌可被独立记录
S13|断镐石场|可选首领/救援|E01|解除监工控制，放下固定梯E02|V_E01（内含P_R1池奖）；Q5锤痕|先疏散工人；交涉交出征用令也能解职领同包；梯由上方放
S14|湿林庄园|交涉据点|R1-2×1+R1-3×1|核对两份契据，公开付款链|Q3/Q6证据；据点包|会客正门、院墙侧门；成功交涉奖励不减
S15|古渠泵院|机关|R1-4×1+R1-1×1|读泵痕，打开通U2-01的干阶E04|金币25+铁3；P_R1机会|沿堤道可赴R3，深闸未开就回地表
S16|断岳驿口|过境|无|实走R2入口并记录旅行|地图发现，无跨章自动奖励|可以折返，后章未制作时明确边界
S17|峭壁洞窟|观察/近路|无|从地表看封门，从U1内侧解E03|Q5路线；首次开门铁2|未开门可原路回，不跳崖
S18|残旗军需站|探索|R1-1×2|比对接应绳与取消信货号|固定A09；Q3起点；P_R1机会|旧仓侧窗接近；副本不被火毁
S19|猎径伏杀地|野外/支线|R1-4×1+R1-3×1+R1-1×1|先找受伤猎人或先解除伏兵，观察古兽|Q2进展；P_R1机会|侧坡先救人；古兽可驱离，不强制击杀
S20|铁脊观察台|观察战|R1-3×1+R1-2×1|读取军营侧背和旧路标|固定A14；P_R1机会|有上下山实体路，敌人可沿路接近
S01-T1|第三杯旅店|安全内景|无|弥菈展示样片，选动机与合同|M1接约分支；完整报酬预览|拒约仍可独立调查
S01-T2|远征行会厅|安全内景|无|对质副本，登记原件持有人|Q3核对；商人账户不复制|回广场，两份合同不领两次奖
S01-T3|洛恩铁匠铺|安全内景|无|识别锤痕、买靴、查看制造|固定J08教学；洛恩独立库存|教学可跳，未学仍能用基础武器
S01-T4|南渡转运仓|安全内景|无|按日期查信使来路|Q3旁证；首次金币15|普通门回镇，不复制S02底簿原件
S01-T5|镇拘留所|人物内景|无|查看被押者去向与缴械队长处理|M2选择回响；无处决掉装|已投降者不再可攻击
S01-T6|归途广场亭|安全内景|无|见获救工匠自行返回|Q5回返场景；按Q5唯一收据领奖|休整不刷新人物奖励
H01|断岳山驿|安全过境|无|看到运往矿镇的军车和伤者|地图发现；整备|来路可回R1，不进章领大包
H02|岩炉镇|安全/调查|无|查两种目击，见瑟维恩|研究商店J06；M3线索|街巷安全，看守不追入住所
H03|熔镜工匠院|主线危机|U1-1×1+R2-1×1|先疏散、压住镜架，再做散热回退试验|M3包|固定卡销替代同伴；危机无隐形倒计时
H04|双裂采坑|地形战|R2-1×2+R2-3×1|利用矿车拆开三敌接近线|P_R2机会；铁4|上下采面有步行坡，退回坑外
H05|封炉矿井|机关|R2-3×2|停机后操作上方井架开E05|铁3+金币30；P_R2机会|不耗图纸材料，井未开保留来路
H06|伤工棚街|安全/人物|无|确认被征工匠姓名并选证词去向|Q5旁证；金币25|交谈不召敌，不增加人口管理
H07|天堑石梁|路线战|R2-2×1+R2-1×1+R2-4×1|先断号、用车挡弩，进入桥前|旧石柜固定T04×3+C16；P_R2机会；战前补给|高低接近面均通桥前，保留1.2m退缝
H08|断岳前堡|主线首领|B02+R2-2×2|清固定桥头组，绞盘与旁架手柄二选一放桥|M4触发；奖励在H09|桥前安全点；不要求远处另找手柄
H09|破阵军械岸|主线领奖|无|桥放下后开同岸武备台|M4包：W03+A05+工艺自选|H08未结不入，领取后可安全回桥前
H10|巨岩矿门|遗迹|U1-1×1+R2-3×1|辨别采掘机与古卫，读迁行记录|P_R2机会；C04线索|遗迹门外有完整退路；不能绕桥进H09
H11|铁契公署|交涉据点|R2-1×1+R2-2×1|取征用令，交涉解扣或战斗|据点包；Q1/Q3证据|办事厅侧路保留，文书不要求先杀人
H12|北岗军寨|据点|R2-4×1+R2-1×2|斩断号令协同，取押运时刻表|据点包；P_R2机会|营后哨路或交涉，最多3人一组
H13|风蚀誓廊|遗迹/探索|U1-1×1|以三段旧锤痕校准钟晶|J02独立石槽；C06线索|沿有护边的廊路，非跳跃谜题
H14|鹰背岩林|可选首领|E02|从岩柱判断射线，击败督猎或缴销猎契|V_E02|首领沿山路走位；和平撤猎同奖
H15|天索吊崖|地形战|R2-1×1+R2-2×1|沿固定平台调整吊料遮线|P_R2机会；铁4+金币25|机械旁可退，无悬空QTE
H16|山南古道|安全过境|无|实走下降山路到R3北岸|地图发现|不自动点验码头藏品
H17|余烬废窑|野外/支线|R2-3×1+R2-1×1|核对转运货痕与猎域刻板|P_R2机会；Q2旁证|窑沟有双路，不用火油开路
B01|旱谷出口|过境|无|从U1-10内开E07回地表|地图回环|只到R3边缘，不自动开宝匣
B02|北岸风道|野外|R3-1×2|沿旧路识别两队人的脚印|P_R3机会；金币25|绕矮墙或分批交战，可回R2
B03|归帆镇|安全枢纽|无|鉴定旧绳货号，决定谁保留原信|艾莉丝商店A07；Q3进展|镇内安全，摊铺并非远程菜单
B04|余烬灯坊|调查/机关|无|用反光壶校准影船镜组|Q6起点；固定J01|壶只重播，不能凭声音替人同意
B05|河湾旅店|安全/对质|无|夜祈指出路线被转卖|Q2后续；金币25|选择争论不扣商货不强制开战
B06|风帆市集|交涉据点|R3-4×1+R3-1×1|对照装载清单，止住不实交割|据点包；Q6证据|街面可绕，拒买货不锁线索
B07|沉钟山岗|路线战|R3-3×1+R3-1×1|看环带缺口，绕上旧堂|P_R3机会；战前补给|内圈与外圈都有干路
B08|沉钟旧堂|主线会面/入口|R3-3×1|听完阿德里安条件，核对记录，进E06|M5第一段；固定W12+A03|退谈不自动开战，守卫可复位关闭
B09|黑签仓院|据点|R3-4×1+R3-2×1|查伪造封签，留完好藏品|据点包；Q6终点材料|水槽与侧檐可避火，记录不烧毁
B10|怒潮码头|主线首领|B03+R3-1×2+R1-3×1|胜利后落链，同台点验三组藏品|M6包；W10+J05；护符/铜芯选择另记|场外补给，B12局部水槽保干路；不跨岸偷领
B11|天钩吊臂台|机关战|R3-4×1+R3-1×1|按原开臂条件移开接近障碍|P_R3机会；铁3|机关失败可回退，不强制点油
B12|分潮水渠|机关/整备|R3-2×1|调阀确认局部清火水槽|铁3+油1待领；P_R3机会|只清局部地面，不能把全图冲走
B13|芦苇迷湾|野外|R3-4×1+R3-1×2|从干石坡识别拖钩方向|P_R3机会；金币30|干岸双路，无氧气条
B14|沉船墓场|可选首领/支线|E03|核对真实船体潮痕，解除打捞者封锁|V_E03；Q3证据另记|船腹与甲板侧梯互通；交出合法返还凭据同奖
B15|南岸农庄|安全/观察|无|从旧渠观察古兽迁徙、接R1堤道|Q2终点；金币30|不强制农务，不出卖兽群换更好装备
B16|东岸古渡|过境|R3-1×1+R3-4×1|拆散截路小队，步行赴R4|P_R3机会|古渡陆桥免费；回程不刷敌
B17|旧誓墓园|遗迹/调查|R3-3×1|比对两批封炉年代与地宫石刻|Q1旁证；固定A15线索|可先关钟摆避战，安息者不产材料
B18|双契宅院|交涉据点|R3-1×1+R3-4×1|用不同付款凭据当面对质|Q3结算点；据点包|正门约谈或侧入账房，记录同一真相不重复领
F01|黑冠外集|安全枢纽|无|看见被征工匠车，核对城防令|整备；M7准备线索|不跨地图自动发终章包
F02|流火长街|安全/人物|无|向工匠家属确认实际出口|金币30；M7接应线索|不把居民设为掉装对象
F03|黑冠西门|交涉关口|R4-1×1+R4-2×1|通行证、侧入或解除门卫|据点包；P_R4机会|战败返回外集，通行只开外城
F04|铁锁工坊|主线救援|R4-3×1+R4-1×1|解危险工位、取备用镜组|M7准备A；据点包|谈判、检修侧入、战斗同奖；凯尔不被重复抓回
F05|黑旗旧营|据点|R4-4×1+R4-2×1|出示洛恩证词或沿营后进办公间|据点包；Q1回响|局部放行不等于全城停战
F06|黑印文书院|主线调查|R4-3×1+R4-1×1|比对抄本与征掘令，展示原刻证据|M7准备B；Q4见证|无公开副本仍能取正本，院落侧道可退
F07|东仓暗街|主线接应|R4-2×1+R4-1×1|实走出口、确认接应可执行|M7准备A替代；Q2/Q3回响|接应暴露仍有旧路；不付费买主线出口
F08|铁旗广场|路线战|R4-4×1+R4-1×1+R4-3×1|先拆镜线再绕盾阵|P_R4机会；铁4|三方向掩体，最多两种同时警示
F09|西境弩台|必经据点|R4-1×1+R4-2×1|清守卫，亲手拆西台销|据点包；M7西台状态|可先东后西，拆掉永不复活
F10|东境弩台|必经据点|R4-1×1+R4-2×1|清守卫，亲手拆东台销|据点包；M7东台状态|与西台独立，回路仍通F12
F11|凌城连廊|可选探索|R4-2×1|沿实体墙路发现开星环侧龛|固定W14；P_R4机会|不领侧龛也能去F12
F12|决战休整庭|安全整备|无|补给、检查两台与最低安全准备|主线缺项提示，不领奖|未拆两台仍可到此整备，只限制进F13
F13|黑冠决战庭|终章首领|B04|击败阿德里安，令内弩口停火|M7战果；开库动作另记|至少14×12m石垛战场；不关全城出口
F14|黑冠军械库|主线领奖|无|同平台转绞盘，开主箱；侧格另搜|M7包：W06+J07保底补领；T08另记|距战场2–3m安全领奖，不再清第二地牢
F15|黑冠档案楼|可选剧情|R4-3×1|核对当前征掘令的签名与限制|Q4后果；金币60+铁5|战后可回访，非开主箱跑腿前置
F16|干涸护城壕|过境|无|从U2侧开E08，实走外城坡|地图回环|只到堡外，不进首领场和宝库
F17|铁棘检修坡|可选首领|E04|解除典狱长扣押，开检修箱|V_E04；固定J07仅唯一收据|检修侧路与正坡均可；该场替换旧铁棘监守，不叠加
U1-01|暗仓货栈|交涉据点|U1-3×1+R1-2×1|查活人转运账，交涉或侧入|据点包；Q2/Q3证据|E01原路能退，谈判失败不焊门
U1-02|鸣岩洞厅|路线/支线|U1-2×2|实测高差，开E03内侧石门|Q5进展；P_U1机会|保留两层步行坡，不从地表强开
U1-03|断链矿廊|野外|U1-4×1+U1-2×2|避配重落点，核对两段路图|P_U1机会；铁4|E02须地表放梯；未放可退E01
U1-04|余火居所|安全/人物|无|阵亡者正在吃晚饭，听伊芙琳质问|M2救援段；Q5试走|居民不变敌，不把晚饭变开箱
U1-05|铁锁监区|主线救援|U1-3×2|救工匠并确认实际离场|M2救援包一次；据点包|值房交涉、侧廊、战斗均可；已救不再被抓
U1-06|三誓军械廊|可选首领/主线机关|E06|观察第三剑向门内，停机旁路或迎战|V_E06；Q1证词|主线只需机关读法，停机也领同首领包，不强制打第5主线Boss
U1-07|震炉工坊|可选首领/研究|E05|读冷白炉槽，泄压停机或战斗|V_E05；Q4讲堂另记|试验可回退；先救现场工人再启战
U1-08|天火深炉|主线核心/终局|无|两轮可中止接触、检查迁行口、最终选择|M4接触包；M8终局包，两个时点独立|核心是非人生命，拒绝战利品化；不同选择均有短操作
U1-09|悬链绞盘井|交通战|U1-4×1|操作实体平台，核对E05井架状态|P_U1机会；铁4|E05从地表开，井下保回工坊路
U1-10|见日长廊|安全/近路|无|从内开E07，让撤离者走到旱谷|Q5出口旁证；金币30|开门不跨幕领奖，不刷新人或怪
U2-01|封潮前厅|前期边界|无|从R1看见深闸，辨认回退柄|铁2+金币20一次|深闸由U2-03内开；前期不出P_U2与后期装备
U2-02|沉潮长厅|机关战|U2-1×2+U2-3×1|利用干渠折线破镜眼瞄准|P_U2机会；铁4|无游泳需求，外侧干阶能退
U2-03|镇闸广场|可选首领/主线试验|E07|分区泄压、停机或击败镇守，内开深闸|V_E07；M5泄压状态|主线试验始终可用；停机解法不耗稀有资源
U2-04|守库人旧居|安全/调查|无|核对守库记录和退出协议|固定J04配方C10；金币40|可交谈者有自身去向，不新增商户
U2-05|沉钟下殿|入口战|U2-2×1+U2-4×1|从E06进场，按钟纹找档案方向|固定T06×3+C17；P_U2机会|侧室可绕，E06原路能退
U2-06|覆文档案廊|主线/支线|U2-3×1+R4-3×1（仅侧室被占时）|两角度读原刻，比较瑟维恩现代拓本|M5包；固定A11；Q4演示|占领只影响侧室，不封原刻和主线道路
U2-07|禁域祭仪库|可选首领/主线记录|E08|解镜阵取迁行/静眠图，停机或战斗|V_E08；固定A15唯一收据|双侧廊连回档案；主线图不绑定战斗胜利
U2-08|无名囚室|调查/人物|无|对照旧封门与当前征用的不同责任|Q1证据；金币40+铁3|不重复学徒救援，不放突袭刷兵
U2-09|堡外检修道|交通战|U2-1×1+U2-2×1|从内侧开E08，走到干壕|P_U2机会；铁4|只能去F16外城，不绕两外弩台和终Boss
'''

LEVELS = []
for row in LEVEL_ROWS.strip().splitlines():
    key, name, kind, encounter, objective, reward, route = row.split('|')
    region = 'U1' if key.startswith('U1') else 'U2' if key.startswith('U2') else {'S':'R1','H':'R2','B':'R3','F':'R4'}[key[0]]
    encounter = re.sub(r'(?<![A-Z0-9-])B0([1-4])(?![A-Z0-9-])', lambda m: 'BOSS_R'+m[1], encounter)
    encounter = re.sub(r'(?<![A-Z0-9-])E0([1-8])(?![A-Z0-9-])', lambda m: 'ELITE_0'+m[1], encounter)
    LEVELS.append(dict(id=key, region=region, name=name, kind=kind, encounter=encounter,
                       objective=objective, reward=reward, route=route))

# Shared progression rewards: no amount is implied by merely entering a region.
MAIN_REWARDS = [
    dict(id='M1', name='死人来信', trigger='S01-T1接约预支；S04夺匣并确认原信', gold=160, iron=8, seals='T01×3', gear='无固定武器；DR1四件自选一', detail='接约先得30币，夺匣后130；拒约不领30，夺匣后160，同一阶段总额160。自选一由军需盒领取，和普通怪掉落不同收据。'),
    dict(id='M2', name='血路破关', trigger='U1-05工匠实际离场；S10击败并抬杆，两段独立', gold=220, iron=12, seals='T03×3', gear='W02；J08教学漏领补齐', detail='救援段80币/铁4；抬杆段140币/铁8+主装备。未先救人可先领抬杆段，救援回访再领，不以幕号推断。'),
    dict(id='M3', name='救命者的铁锁', trigger='H03镜架稳定、完成小幅松环与实际回退', gold=180, iron=10, seals='T04×3', gear='C01/C03/C04/C05/C06/C07/C08工艺图谱', detail='发符纹8用于原配方；不从阿德里安的过场救人直接判玩家完成试验。'),
    dict(id='M4', name='断岳夺火', trigger='H08放桥后H09武备台；U1-08第一轮接触分别领取', gold=260, iron=16, seals='T05×3', gear='W03+A05；DR2四件自选一', detail='桥包180币/铁12+W03/A05/自选；接触包80币/铁4。另符纹4、C11；首次接触不要求服从核心，不伤害它也有完整包。'),
    dict(id='M5', name='沉钟惊雷', trigger='U2-03实际泄压回退；U2-06两角度原刻核验', gold=240, iron=14, seals='T06×3', gear='A11；DR3或DU2八件自选一', detail='泄压100币/铁6，档案140币/铁8+装备。另符纹4、C09/C10/C17；公开/隐瞒不影响基础奖励。'),
    dict(id='M6', name='怒潮夺宝', trigger='B10胜利后落链、三组点验、开宝匣', gold=320, iron=18, seals='T06×3', gear='W10+J05；完整护符/余烬铜芯二选一独立确认', detail='另符纹4。互斥古物不计作两件永久装备；核心装备不依赖道德选择，非人生命不拆成材料。'),
    dict(id='M7', name='黑冠陨落', trigger='散热/泄压/实际出口已核验；F09/F10拆台；F13胜利后F14开主箱', gold=440, iron=24, seals='T07×3', gear='W06；J07若检修箱漏领则同一收据补齐', detail='准备段160币/铁8、锻造芯2/符纹4、C02/C12；开库段280币/铁16、符纹4。T08只在侧格唯一1张，不放主箱；安全条件与双台分别检查。'),
    dict(id='M8', name='天火归途', trigger='U1-08实际执行所选终局操作并撤出危险区', gold=240, iron=8, seals='无新符，避免终局刷唯一卷', gear='六地区域池任选一件尚未拥有物；破晓远征外观记录', detail='四种结局同等价值，不绑定最高数值装备。回返不刷新敌群；原固定物和自选物分别写收据。'),
]

SIDE_REWARDS = [
    dict(id='Q1', name='铁誓无名碑', places='S12→U1-06→F05', trigger='完成原名/存疑记录并交付证词；不要求支持某个立场', gold=140, iron=6, choice='DR1-01 / DR2-02 / DU1-03 三选一', benefit='洛恩签完整经历时，F05旧卫可听证；不删除全部城防。'),
    dict(id='Q2', name='猎域断链', places='S05/S19→B15→F07', trigger='确认猎人和古兽去向，完成路线处置', gold=160, iron=6, choice='DR1-04 / DR2-04 / DR3-01 三选一', benefit='删去栖居坐标后核验通路会导致研究侧室被军方抢先占领；仍能推进。'),
    dict(id='Q3', name='断航归来', places='S18→B03/B14→B18', trigger='比对取消信、潮痕和双方付款凭据，提交所选证据版本', gold=180, iron=8, choice='DR3-02 / DR3-03 / DR4-01 三选一', benefit='完整证据可争取艾莉丝在F07一次接应；她不会变成永久跟班。'),
    dict(id='Q4', name='撕开假星图', places='U1-07→U2-06→F06', trigger='完成可复查演示或明确封存现有证据', gold=180, iron=8, choice='DU1-04 / DU2-02 / DU2-03 三选一', benefit='共同署名改善测绘合作；维持单独署名保成果但人物分路。'),
    dict(id='Q5', name='向光而行', places='U1-02/03→E03→S01-T6', trigger='完成两处高差测绘，交给未参与者试走并完成回返', gold=140, iron=6, choice='DR1-02 / DU1-02 / DU2-01 三选一', benefit='撤离者能按公开安全图自行走出；不自动从地表开E03。'),
    dict(id='Q6', name='影船旧债', places='B04/B14→B09', trigger='壶面校光、进入真实船体，核对退款原件与装载副页', gold=160, iron=6, choice='DR3-04 / DU2-04 / DR4-04 三选一', benefit='艾莉丝明确归还与收藏的边界；可保留经营或离店学舞，回报等值。'),
]

# Reuse the existing complete 40+8 spec instead of re-authoring its mechanics.
LEGACY_SOURCES = {
    'W01':'初始','W02':'M2 / S10抬杆','W03':'M4 / H09放桥后武备台','W04':'C01 / M3学图',
    'W05':'C02 / M7准备段学图','W06':'M7 / F14主箱','W07':'初始','W08':'S08固定隐匣',
    'W09':'C03 / M3学图','W10':'M6 / B10宝匣','W11':'初始','W12':'B08旧堂侧龛',
    'W13':'C04 / M3学图','W14':'F11可选侧龛','W15':'洛恩二幕专售64币','W16':'C05 / M3学图',
    'A01':'S09军营武备箱','A02':'S11哨塔眺望袋','A03':'B08灯座暗格','A04':'C06 / M3学图',
    'A05':'M4 / H09武备台','A06':'S05树根宝囊','A07':'艾莉丝三幕专售80币','A08':'C07 / M3学图',
    'A09':'S18旧兵袋','A10':'夜祈首幕专售40币','A11':'U2-06 / M5同一收据','A12':'C08 / M3学图',
    'A13':'洛恩首幕专售32币','A14':'S20路标背囊','A15':'U2-07碑文暗格','A16':'C09 / M5学图',
    'J01':'B04炭纹小匣','J02':'H13干涸石槽，保留旧唯一收据','J03':'弥菈首幕专售28币','J04':'C10 / M5保底，U2-04可提前学图',
    'J05':'M6 / B10宝匣附囊','J06':'瑟维恩二幕专售56币','J07':'F17或F14补领，共同唯一收据','J08':'S01-T3教学，M2补漏同一收据',
    'T01':'初始6+C13；M1另3','T02':'S07固定3+C14','T03':'M2 / S10固定3+C15',
    'T04':'M3包3+C16；H07旧石柜另3','T05':'M4包3+C11','T06':'U2-05旧箱3；M5/M6各另3；C17',
    'T07':'M7包3+C12','T08':'F14侧格唯一1，无配方',
}
LEGACY=[]
CONSUMABLES=[]
for line in (ROOT/'docs/interactions/equipment-and-crafting.md').read_text(encoding='utf-8').splitlines():
    if not re.match(r'^\| [WAJT]\d{2} \|',line):
        continue
    key, label, tier, effect, set_name, source=[c.strip() for c in line.split('|')[1:-1]]
    name=label.split('，')[0]
    name={'A01':'铁誓护额','A12':'破晓护腕','A16':'破晓战靴'}.get(key,name)
    entry=dict(id=key,name=name,legacyName=label.split('，')[0],tierAndSlot=tier,effect=effect,set=set_name,
               source=LEGACY_SOURCES[key],legacySource=source,sourceDocument='docs/interactions/equipment-and-crafting.md')
    (CONSUMABLES if key.startswith('T') else LEGACY).append(entry)
LEGENDS=[
    dict(id='L01',name='风暴王的遗嘱',tierAndSlot='单手剑 / 传奇',effect='直接近战22%留下7s雷痕；R引爆近处雷痕并连锁最多两敌',source='S08旧隐匣18% / 原隘口监守25%传奇池；结果写档'),
    dict(id='L02',name='阿斯特拉的回信',tierAndSlot='双手弓 / 传奇',effect='箭矢折返，每航段同一目标至多命中一次；走位改变回程',source='S08旧隐匣18% / 原隘口监守25%传奇池；结果写档'),
]

EXTRA_RULES = {
    'ordinary': '每个真实普通敌首次击败固定铁1与金币3/4/5/6（按R1/R2/R3/R4；U1为4、U2为5）；另20%装备触发，触发后按所在池权重取1件。鸣震甲虫两只合计按1次资源及装备事件。',
    'pity': '同一地区连续5次合格事件未出装备，第6次强制出1件；出装后清零。未发现且不能进入的区域不提前计数。已败、复演、召物、投降者不计。所有结果写档，读档不重掷。',
    'pool': '六池各4件，权重30/30/20/20，总100；精良/稀有/史诗由物品自身决定。普通池不混入固定剧情物、商人独家物、传奇L01/L02、T08或精英奖；旧传奇检定独立，不重置/推进新区域保底。',
    'duplicates': '永久物每ID同时最多1件。自然抽到已拥有或仍待领的物品时，首次确定为铁2+金币8/12/16/20（U1=12、U2=16），不重抽、不额外推进保底。剧情自选只列未拥有未待领，池已空则同额兑换。自然抽到重复也视作一次出装事件并清零保底。',
    'outpost': '每个标据点包的独立遭遇事件完成后金币40/55/70/90（U1=55，U2=70）+铁3+当地池1件。交涉/潜入/停机用同一清算收据：未被击败的该组敌人的首次资源与预定掉落在被封存的军需箱结算，并记该实例奖励已处理，之后击败不能再领。',
    'elite': '八个V_E01—08事件完成：固定DE同编号1件+当地池1件+金币80/100/120/160（U1=110、U2=130）+铁5；击杀、缴械解职、停机三类实际完成同一事务，不要求杀人拿最高回报。主线图/机关知识在战斗前可取得。',
    'peaceful': '可选精英与据点成功交涉/停机采用同一事件键，不新增额外奖励箱。主线四场原必败战仍需完成，普通路边敌绕过不自动发奖。',
    'capacity': '永久装备仍按现有9槽；弓和双手长杖不能持副手。符T01—07每种12/合计48（含T08），T08上限1；铁99/金币9999/符纹40/芯8沿用完整设计容量。固定包拆成物品和材料数量余量，能收多少扣多少；自选确认前校验容量，溢出留原安全锚点，不吞装备。',
    'budget': '主线金币2060、铁110、符纹28、锻造芯2；六支线金币960、铁40；非主线调查/据点/小怪另算，不能冒充保底。10件旧合成永久物首造需铁56/符纹15/芯1，主线净余54/13/1。7种旧制符首批另耗铁26，仍余28铁；新掉落物不设额外制造成本。旧商人6件共300币，能负担不代表库存刷新。',
    'replay': '主世界已败不刷新；显式隔离复演沿用每完整场铁2，不掉装备、不给金币、不重置地区保底，不复制主线首领和已败随从。丰富掉落来自完整世界探索，不用读档或复活凑数量。',
    'migration': '使用新contentVersion=campaign-v6-design；发布接入前必须设计存档迁移。可信旧奖保留原物，新增金币只补新旧应得差额；无法证实完成条件的旧档不猜奖。新事件用独立receipt并引用旧唯一装备receipt，不直接覆盖SaveSnapshotV1。此目录数据不被运行时导入。',
    'combatCaps': '单体同一附加效果按effectId仅最强一份；移动加成总≤15%，物理减伤总≤35%，专注自然恢复≤8/s。新增直接伤害增幅合计≤20%，同一附伤不递归触发；Boss削韧100→失衡0.6s/8s，失衡后共享2s保护，地形失衡不相加。基础生命120，换装不回当前血/专注。',
}

# Link concepts to the authored content, never to SpriteFrame/animation resources.
for region in REGIONS:
    rid=region['id']
    for i,mob in enumerate(m for m in MOBS if m['region']==rid):
        mob['art']=dict(file=region['plate'], position=f'middle row, left-to-right {i+1}', spriteReady=False)
    for i,boss in enumerate(b for b in BOSSES if b['region']==rid):
        boss['art']=dict(file=region['plate'],position='top left' if i==0 else 'top right', spriteReady=False)
    selected='drops-u2-v2.png' if rid=='U2' else 'drops-'+rid.lower()+'.png'
    for i,gear in enumerate(g for g in GEAR if g['region']==rid and g['weight']):
        gear['art']=dict(file=selected,position=['top left','top right','bottom left','bottom right'][i],spriteReady=False)
for i,gear in enumerate(g for g in GEAR if not g['weight']):
    gear['art']=dict(file='elite-loot.png',position=f"{'top' if i<4 else 'bottom'} row, left-to-right {i%4+1}",spriteReady=False)

def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join('---' for _ in headers) + '|'] +
                     ['| ' + ' | '.join(str(v).replace('|', '／').replace('\n','<br>') for v in row) + ' |' for row in rows])

def validate():
    contract = (ROOT / 'docs/maps/world-geography-v3.md').read_text(encoding='utf-8')
    ids = set(re.findall(r'^\| ((?:S|H|B|F)\d{2}|U[12]-\d{2})(?:\s|\s*\|)', contract, re.M))
    expected = ids | {f'S01-T{i}' for i in range(1,7)}
    actual = {n['id'] for n in LEVELS}
    if expected != actual or len(actual) != len(LEVELS):
        raise ValueError(f'Node coverage: missing={expected-actual}, extra={actual-expected}')
    for entries in (MOBS, GEAR, BOSSES):
        assert len({e['id'] for e in entries}) == len(entries)
    assert len(MOBS) == 24 and len(GEAR) == 32 and len(BOSSES) == 12
    assert len(LEGACY)==40 and len(CONSUMABLES)==8 and len(LEGENDS)==2
    permanent=LEGACY+LEGENDS+GEAR
    assert len(permanent)==len({e['id'] for e in permanent})==74
    known_items={e['id'] for e in permanent+CONSUMABLES}
    for node in LEVELS:
        for key in re.findall(r'(?<![A-Z0-9])(?:[WAJTL]\d{2}|D(?:R[1-4]|U[12])-\d{2}|DE\d{2})(?![A-Z0-9])',node['reward']):
            assert key in known_items,(node['id'],key)
    for r in REGIONS:
        members = [g for g in GEAR if g['region'] == r['id'] and g['weight']]
        assert len(members) == 4 and sum(g['weight'] for g in members) == 100
        assert (ART/r['plate']).is_file()
    for e in MOBS+GEAR+BOSSES:
        assert (ART/e['art']['file']).is_file(), e['id']
    boss_ids = {b['id'] for b in BOSSES}
    mob_ids = {m['id'] for m in MOBS}
    for n in LEVELS:
        for ref in re.findall(r'BOSS_[A-Z0-9]+|ELITE_\d+|[RU]\d-\d+', n['encounter']):
            assert ref in mob_ids | boss_ids, (n['id'], ref)
    for b in BOSSES:
        arena = next(n for n in LEVELS if n['id'] == b['arena'])
        assert b['id'] in arena['encounter']
        if b['id'].startswith('ELITE_'):
            assert any(g['id'] == 'DE'+b['id'][-2:] for g in GEAR)
    assert sum(r['gold'] for r in MAIN_REWARDS) == 2060
    assert sum(r['iron'] for r in MAIN_REWARDS) == 110
    assert sum(r['gold'] for r in SIDE_REWARDS) == 960
    assert sum(r['iron'] for r in SIDE_REWARDS) == 40
    return dict(geographicNodes=len(ids), townInteriors=6, totalNodes=len(LEVELS), bosses=len(BOSSES), commonArchetypes=len(MOBS), newGear=len(GEAR), permanentEquipment=74, consumableTypes=8, totalItemTypes=82, regions=len(REGIONS), mainGold=2060, mainIron=110, sideGold=960, sideIron=40)

def write_catalog(summary):
    data = dict(schemaVersion=1, contentVersion='campaign-v6-design', date='2026-11-08', status='design-only; not runtime content',
                regions=REGIONS, levels=LEVELS, enemies=MOBS, bosses=BOSSES, newEquipment=GEAR,
                legacyEquipment=LEGACY, retainedLegendaries=LEGENDS, consumables=CONSUMABLES,
                mainRewards=MAIN_REWARDS, sideRewards=SIDE_REWARDS, rules=EXTRA_RULES, validation=summary)
    (ART/'campaign-design.json').write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def write_documents(summary):
    intro = ('2026-11-08 · 按用户最新要求完成的全世界内容设计。**设计与静态核对完成；新遭遇、新掉落、名称和剧情尚未接入运行版，数值未试玩。** '
             '当前游戏仍是Cocos Creator 3.8.8首章32区；`WorldData.ts`与`Equipment.ts`才是运行目录。本文不修改运行存档或伪造后章已可玩。\n\n')
    overview = '# 六区首领、怪物与装备设计 v2\n\n'+intro
    overview += ('本轮包含91个地理地点和石桥镇6个内景、24种普通敌、4场主线首领和8场可选首领。'
                 '完整设计永久装备为74种：旧固定/制造/商店40件、既有随机传奇2件、新区域掉落24件、新精英奖8件；另8种消耗符。'
                 '当前运行合计19项物品，已包含3种符和2件传奇，不能把完整目录数当成已接入数量。\n\n'
                 '- [主线、命名与人物回响](campaign-v6.md)\n- [97处逐关布置](world-levels-v2.md)\n- [奖励、掉落概率与32件新增装备](loot-catalog-v2.md)\n'
                 '- [结构化内容](../../source-art/encounters/cloud-world-v2/campaign-design.json)\n- [七张云端图及审图记录](../../source-art/encounters/cloud-world-v2/README.md)\n\n')
    overview += '## 六区节奏\n\n'+table(['区域','现名 → 本轮名','体验与视觉','普通池'],[(r['id'], r['old']+' → '+r['name'],r['theme'],r['pool']) for r in REGIONS])+'\n\n'
    overview += ('建议主线顺序：R1夺匣→U1浅层救援→R1关口→R2镜架/矿桥→U1深层接触→R3旧堂→U2档案/泄压→R3码头→R4决战→U1终局。'
                 '这是一条推荐叙事线，不把普通跨境旅行锁成线性关卡；8端口和现有地理边保持。\n\n'
                 '## 战斗共同规则\n\n'
                 '表中HP/伤害/时间均为首轮候选。英雄基础生命120；常规一组2–4敌，最多8活跃、峰值12，不把整地区敌一次激活。'
                 '最多3条主要预警、近身保留1.2m退路；所有攻击都有姿态和地面轮廓，色觉或静音下可识别。'
                 '有效窗普通0.10–0.18s，单次冲撞/双锤不重复扣血；冷却普通近战0.6–1.0s、远程按表装填。'
                 '新首领普通招式之间至少0.5s自由移动，阶段转换只排在当前动作后，不取消预警。'
                 '远程射线受墙与掩体约束；屏外敌先给1s方向提示，不在屏外瞬发。\n\n'
                 '主线四场保留既有反制；八可选场可战、交涉解除或按现场线索停机，主线记录和最低安全机关不绑可选击杀。'
                 '人类可缴械存活；机械明确齿轮、石脚与镜头，没有灵魂供能/幽魂复活。天火核心是非人生命，不是新增第13名可刷Boss。\n\n')
    for r in REGIONS:
        overview += '## '+r['id']+' '+r['name']+'\n\n'
        overview += table(['键 / 名称','职能','HP / 单击','前摇 / 锁定末段 / 后摇','预警与反制'],[(m['id']+' '+m['name'],m['role'],f"{m['hp']} / {m['damage']}",f"{m['windup']:.2f} / {m['lock']:.2f} / {m['recovery']:.2f}s",m['counter']) for m in MOBS if m['region']==r['id']])+'\n\n'
        for b in [x for x in BOSSES if x['region']==r['id']]:
            overview += '### '+b['id']+' '+b['name']+'\n\n'
            overview += f"地点 **{b['arena']}**；HP **{b['hp']}**；{'主线必经' if b['mandatory'] else '可选挑战、可替代解除'}；固定奖励 **{b['fixedLoot']}**，按 **{b['rewardEvent']}** 结算。\n\n"
            overview += '\n'.join('- '+s for s in b['moves'].split('；'))+'\n\n'
            overview += ('场地与替代：'+next(n['route'] for n in LEVELS if n['id']==b['arena'])+'。'
                         '失败回场外检查点，未败者恢复满血，已败随从不复活；胜利与开箱/机关分别记录。\n\n')
    overview += ('## 资源复用与验收\n\n'
                 '已检查Cocos 3.8.8、原生SpriteFrame/现有2D资源管线、FairyGUI 1.2.2与Python Pillow。'
                 '本轮为原创内容数据和设计文档，复用既有导出脚本、Python标准库及Pillow缩略图，不新增引擎组件、随机库、测试框架或依赖。'
                 '现成通用怪包无法一一匹配这批成年比例、机械结构与已验收角色的材质；复用七张既有云端image_gen图并新生成六张区域掉落板，共十三张选用概念板，无需重下资源或启动本地模型。\n\n'
                 '概念方向审阅仅核对缩略总览中的数量、轮廓、道具和材质分区。正式切图、透明边缘、锚点、攻击/受击/死亡动画、碰撞与移动端性能均待制作验收。'
                 '旧铁棘监守150HP是旧完整设计；本轮E04以300HP新可选战替换它，F17不叠放两个监守、不重复发旧铁2和新精英铁5。'
                 'H08与B10保持原短小头目和固定随从，新增史诗来自可选战及新池，不靠抬血量拖长主线。\n\n')
    (DOC/'encounters-and-loot-v2.md').write_text(overview,encoding='utf-8')

    world = '# 全世界逐关布置 v2\n\n'+intro
    world += ('覆盖[地理合同v3](../maps/world-geography-v3.md)全部91地点和6镇内景。稳定地点编号沿用，显示名采用[新命名](campaign-v6.md)。'
              'E01—E08开门方向、地表普通边和地层保持；表中先后是查阅顺序，不是强制游玩顺序。\n\n'
              '敌人键见[遭遇总表](encounters-and-loot-v2.md)，P_*见[掉落规则](loot-catalog-v2.md)。'
              '“P机会”按合格真实敌事件20%/六次保底结算；“据点包”是同一事件的清算盒，交涉和战斗不能领两份；'
              '表中额外固定铁/金币与敌人铁/金币分别记收据。默认不标新装备的调查节点仍有线索、空间变化或人物回响，不给所有路口硬塞Boss。\n\n')
    for r in REGIONS:
        nodes=[n for n in LEVELS if n['region']==r['id']]
        world += f"## {r['id']} {r['name']}（{len(nodes)}处）\n\n"
        world += table(['编号 / 显示名','性质 / 固定组合','玩家要做什么','奖励 / 作用','接近面与退路'],[(n['id']+' '+n['name'],n['kind']+'；'+n['encounter'],n['objective'],n['reward'],n['route']) for n in nodes])+'\n\n'
    world += ('## 关键边界核对\n\n'
              '- E01地表插销；E02上方放梯；E03地下内开；E04前厅深闸由U2-03开；E05地表井架；E06旧堂固定阶；E07地下内开；E08地宫内开且只到F16。\n'
              '- H09只在放桥后可达；B10邻岸不能偷领宝匣；F09/F10独立清算，外弩台不接受终战号令。F12仍可先到，F14战后短路领奖。\n'
              '- U1→U2仍须经R3，镜阵/剧情供能线路不变成步行连边。前期U2-01不出后期装备。\n'
              '- 旧固定W08/A01/A02/A06/A09/A14及商人物不放随机池；地点旧名到新名只改显示，不按中文名称生成存档键。\n'
              '- 每个节点由导出检查与地理合同集合比对，当前97/97无缺项。静态覆盖不等于关卡时长、难度或实机体验已通过。\n')
    (DOC/'world-levels-v2.md').write_text(world,encoding='utf-8')

    loot='# 丰厚奖励与区域掉落目录 v2\n\n'+intro
    loot+=('本轮按用户“剧情奖励丰厚、打怪装备更丰富”更新完整设计。旧文档中的“普通敌只掉铁”“主世界Boss不加装备池”和540主线金币预算被本页替代；'
           '其余物品ID、五商人账户、唯一物、互斥古物及容量约束沿用，详细冲突以本页明确条目为准。当前运行规则未被这份设计自动改写。\n\n'
           '## 掉落流程\n\n')
    for key,label in [('ordinary','普通敌'),('pity','坏运气保底'),('pool','区域池'),('duplicates','重复装备'),('outpost','据点清算'),('elite','可选首领'),('peaceful','替代解法'),('capacity','容量和双手'),('replay','隔离复演')]:
        loot+='**'+label+'：**'+EXTRA_RULES[key]+'\n\n'
    loot+=('主线Boss胜利现场先清楚展示固定核心装备；物品仍在原动作时点领取。四场主线另各给当地区域池1件，'
           '与普通敌抽取不同收据，不重置地区保底；这4件和据点/可选奖均是世界事件唯一奖励。'
           '固定物已拥有时保留原唯一领取记录，不造第二份；新增自选不会注入旧固定池。\n\n'
           '## 八段主线大包\n\n')
    loot+=table(['事件 / 名称','实际触发','金币 / 铁','装备 / 符','分账与补充'],[(m['id']+' '+m['name'],m['trigger'],f"{m['gold']} / {m['iron']}",m['gear']+'；'+m['seals'],m['detail']) for m in MAIN_REWARDS])+'\n\n'
    loot+='**资源预算：**'+EXTRA_RULES['budget']+'\n\n'
    loot+=('主线八包至少提供4主奖装备、M1/M4/M5/M8四次自选、四场主线池奖，外加A11、J07等固定物；'
           '自选可优先补流派，已拥有/待领不重复计作“新装备”。不把同一份固定A11在场景表和主线包里重复发。'
           '初始W01/W07/W11保留，剑弓杖均可零符零油推进。新单手剑/锤沿用各自标准基础动作与等级基础值，'
           '精良按L2、稀有按L3、史诗按L4（终章史诗L5）候选基线，效果见下表；正式接入再统一数值，不能仅因图中刃长提高命中半径。\n\n'
           '## 六条人物支线\n\n')
    loot+=table(['支线','完成条件 / 地点','金币 / 铁','稀有自选','真实回响'],[(q['id']+' '+q['name'],q['places']+'；'+q['trigger'],f"{q['gold']} / {q['iron']}",q['choice'],q['benefit']) for q in SIDE_REWARDS])+'\n\n'
    loot+=('支线总金币960、铁40，另每条1件自选。高价值来自玩家完成现场行动，不取决于赞同哪句台词；'
           '终局四路线价值相同，玩家不能用重复改对话和提交副本刷奖励。\n\n## 24件区域装备\n\n')
    for r in REGIONS:
        loot+=f"### {r['pool']} · {r['name']}\n\n"
        loot+=table(['设计键 / 名称','槽 / 品质 / 权重','可实际解释的特性','可见造型'],[(g['id']+' '+g['name'],g['slot']+' / '+g['grade']+' / '+str(g['weight']),g['effect'],g['visual']) for g in GEAR if g['region']==r['id'] and g['weight']])+'\n\n'
    loot+='## 八件精英固定奖\n\n'
    loot+=table(['设计键 / 名称','唯一事件 / 槽','效果','云端精英板位置'],[(g['id']+' '+g['name'],'V_E'+g['id'][-2:]+' / '+g['slot'],g['effect'],('上排' if i<4 else '下排')+'从左第'+str(i%4+1)+'件') for i,g in enumerate([x for x in GEAR if not x['weight']])])+'\n\n'
    loot+='**统一效果上限：**'+EXTRA_RULES['combatCaps']+'\n\n'
    loot+=('## 保留的42件永久物与8类符\n\n'
           '以下直接复用[既有40件完整目录](../interactions/equipment-and-crafting.md)与[两件已实现传奇](../interactions/random-legendaries.md)，只映射本轮显示名和取得位置。'
           '与上方32件合计74种永久物；符按种类计8种，张数不重复算物品种类。\n\n')
    loot+=table(['ID / 名称','槽型 / 品阶','原有特性','本轮来源'],[(g['id']+' '+g['name'],g['tierAndSlot'],g['effect'],g['source']) for g in LEGACY+LEGENDS])+'\n\n'
    loot+=table(['符 / 名称','效果','固定包 / 配方'],[(g['id']+' '+g['name'],g['effect'],g['source']) for g in CONSUMABLES])+'\n\n'
    loot+=('## 旧物保护、补领与开发接入\n\n'
           '旧商人独家J03/A13/W15/A10/J06/A07仍只由五账户售出，不能随机掉出；L01/L02只沿旧传奇来源，概率18%/25%维持原结果持久化；'
           'T08唯一藏格，不在符包、区域池或复演。其他旧配方永久学会，10件合成永久物与7符配方成本沿旧目录。'
           '把“白枝护额”显示改为“铁誓护额”、A12/A16改“破晓护腕/破晓战靴”，不创造新物品。\n\n'
           '旧A15碑文暗格统一到U2-07；B17只给线索。J02桥下干槽在H13廊路干槽实现，保留唯一旧收据；'
           'J04仍配方C10，U2-04只给图纸，不直接发成品。A11在U2-06与M5同一收据；J07在F17或F14保底同一收据；'
           'Q/M自选抽中一个区域物后，其后掉落以重复补偿结算，不复制唯一装备。\n\n'
           '**迁移：**'+EXTRA_RULES['migration']+'\n\n'
           '未来接入顺序：先稳定ID/收据与旧档差额，再普通敌持久化掉落与保底，再据点和平清算，再四主奖与八精英；'
           '最后接动画、碰撞与经济试玩。当前仅输出设计JSON，不把24种新行为硬塞进首章4种敌模板，不把概念图注册成可用动画。\n')
    (DOC/'loot-catalog-v2.md').write_text(loot,encoding='utf-8')

def main():
    summary=validate()
    write_catalog(summary)
    write_documents(summary)
    (ART/'design-validation.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))

if __name__ == '__main__':
    main()
