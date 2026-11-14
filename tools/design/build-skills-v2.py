"""Derive a spatially distinct ranged skill design from the preserved v1 base.

Authored data, not a combat engine. Uses stdlib and existing catalogs only.
No runtime mutations, package installs, downloads or model calls.
"""
from pathlib import Path
import copy
import json
import re

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'source-art/skills/pure-skills-v1'
OUT=ROOT/'source-art/skills/pure-skills-v2'
DOC=ROOT/'docs/design'
OUT.mkdir(parents=True,exist_ok=True)
CAT=copy.deepcopy(json.loads((BASE/'skill-catalog.json').read_text(encoding='utf-8')))
WORLD=copy.deepcopy(json.loads((BASE/'campaign-v7.json').read_text(encoding='utf-8')))
ORIGINAL_NAMES={s['id']:s['name'] for s in CAT['skills']}
ORIGINAL_GATES={s['id']:[r['requiredCharacterLevel'] for r in s['ranks']] for s in CAT['skills']}
ORIGINAL_BOW02_TIMING={k:next(s for s in CAT['skills'] if s['id']=='BOW_02')[k] for k in ['windupSeconds','releaseCommitSeconds','recoverySeconds']}
TEMPORARILY_RETIRED_SKILL_IDS=['ARC_01','ARC_02','ARC_03','ARC_04','ARC_05','ARC_P1','ARC_P2']
RETIRED_SKILL_IDS=['FRO_01','FRO_02','FRO_03','FRO_04','FRO_05','FRO_P1','FRO_P2']+TEMPORARILY_RETIRED_SKILL_IDS
SKILLS=[s for s in CAT['skills'] if s['id'] not in RETIRED_SKILL_IDS]
CAT['skills']=SKILLS
LOOKUP={s['id']:s for s in SKILLS}

def geom(kind,origin='caster',**series):
    return [dict(kind=kind,origin=origin,**{k:(v[i] if isinstance(v,list) else v) for k,v in series.items()}) for i in range(5)]

def set_skill(key,name,shape,ranges,areas,evolution,mechanic,limits=None,power=None,hits=None,mode='point',**extra):
    s=LOOKUP[key]
    s.update(name=name,targetShape=shape,targetingMode=mode,mechanic=mechanic)
    s.update(extra)
    if limits is None: limits=[None]*5
    if isinstance(hits,int): hits=[hits]*5
    for i,r in enumerate(s['ranks']):
        # Remove old circle/chain aliases before installing the explicit v2 shape.
        for k in ['arcDegrees','chainTargetLimit','damagePerSecondaryTargetS','totalCastDamageBudgetS']:
            r.pop(k,None)
        r.update(castRangeMetres=ranges[i],rangeMetres=ranges[i],geometry=areas[i],
                 radiusMetres=areas[i].get('radiusMetres',0),targetLimit=limits[i],evolution=evolution[i])
        if power is not None:r['maxDamagePerTargetS']=power[i]
        if hits is not None:r['authoredDamageHits']=hits[i]
    s['maxTargets']=max(limits) if all(x is not None for x in limits) else None
    s['offensive']=mode!='self' and (any(r['maxDamagePerTargetS']>0 for r in s['ranks']))

set_skill('WAR_01','断空剑气','前飞月牙刃气走廊',[9,10,11,12.5,14],
 geom('projectileCorridor',lengthMetres=[9,10,11,12.5,14],widthMetres=[.8,1,1.15,1.35,1.6]),[
 '两道薄月牙剑气从剑尖飞出，跨过空地命中9m内路径敌人，人物不前冲。',
 '两道细长单层银白月牙交错飞出，射程10m，稀疏金色风痕引向实际接触斩痕。',
 '三道错拍剑气飞出，射程11m；第三道只强化终结接触，不长出背后剑冠。',
 '三道细长单层月牙沿12.5m走廊斩开尘线，末击穿过多个敌人，抵达时局部银锋与金尘错层短闪。',
 '14m长线被三道锋锐银白月牙依次扫过，稀疏金色风痕保持方向，接触斩闪分层展开后快速退亮；仍沿首版薄刃轮廓。'],
 '破阵。判定随刃气弹体前行，墙体截断；剑身起手不另算一份贴身伤害。同敌每刃一次，削韧每cast一次。',mode='direction')
set_skill('WAR_02','破军交斩','远处指定十字交叉刃线',[9,10,11,12,14],
 geom('crossStrips','aimPoint',lengthMetres=[3.5,4,4.5,5,6],widthMetres=[.8,.9,1,1.2,1.4],anglesDegrees=[[-35,35]]*5),[
 '选9m内敌群，两条短刃线在远处交叉，角色留在原地。','10m选点，交叉刃线加长，交点出现短重斩火星。',
 '11m选点，交叉两击错拍0.18s，交点不叠成四份伤害。','12m选点，双刃从交叉区域两侧切入，范围边缘可辨。',
 '14m远端形成6m长交叉切口，末斩爆出向外的金属尘屑，没有施法者脚下光圈。'],
 '替代原突袭；不移动施法者或敌人。交叉条带的并集为命中区；1—2级单段全伤，3—5级两段各50%，重叠区每段只一次。')
set_skill('WAR_03','铁誓壁垒','自身定向护盾，唯一战技自保',[0]*5,
 geom('selfShield'),[
 '前臂与胸前形成短小钢色护层。','护层增加两片低亮金属板形轮廓。','受击时局部盾面亮起，其他部分保持透明。',
 '盾面出现清晰有方向的刃缘，不绕身旋转。','开放式护甲投影贴住前臂和身体，结束时落下碎片，不做巨大圆冠。'],
 '保留v1护盾18/20/22/25/28%最大生命4s与装备联动。它是自保例外，不能代替战技的远程主输出。',limits=[1]*5,mode='self')
set_skill('WAR_04','裂地审判','远端落刃与纵向地裂',[10,11,12,13,14],
 geom('impactAndStrip','aimPoint',radiusMetres=[1.8,2,2.3,2.6,3],lengthMetres=[3,3.5,4,4.5,5],widthMetres=[1.3,1.5,1.7,2,2.3]),[
 '在10m内指定位置落下一道重刃，落点和角色分离。','11m选点，重刃落点向前开出短裂线。',
 '12m选点，主落刃后0.30s沿前方条带追加地裂余震。','13m选点，地裂更宽，中心和条带内的敌人都有接触反馈。',
 '14m远端落刃砸开5m纵向裂带，主爆70%、余震30%；裂带不改变地形碰撞。'],
 '破阵。主击圆盘与前向条带分两段：1—2级只主击，3—5级主击70%/余震30%；各段都按实际范围判定，装饰碎石不判伤。')
set_skill('WAR_05','千锋裁决','远距三拍巨刃走廊',[14,15,16,17,18],
 geom('sweptCorridor',lengthMetres=[14,15,16,17,18],widthMetres=[2.4,2.8,3.2,3.8,4.4]),[
 '三道细长单层银白月牙飞向14m长走廊，施法者与首个敌人保持远距。','15m走廊内三拍定向切割，稀疏金色风痕与实际接触银闪分明。',
 '16m走廊加宽，第三刃仍保留薄而锐利的单层轮廓，纵向接触尘线短促展开。','17m走廊被三道薄银月牙错拍穿过，末击的局部银锋/金尘层次在远端收束。',
 '18m×4.4m走廊内三拍千锋切线接力，银白锐边、稀疏金风痕与末击短促接触爆发更清楚，随后快速退亮；不堆厚重多层巨刃。'],
 '20%/20%/60%三拍，判定随各刃前进，不在角色身边瞬间结算整条伤害。每敌每拍一次。',mode='direction')

set_skill('BOW_01','穿云箭','直线实体贯穿箭',[12,13.5,15,16.5,18],
 geom('projectileCorridor',lengthMetres=[12,13.5,15,16.5,18],widthMetres=[.35,.4,.45,.5,.55]),[
 '一支带尾羽的实体主箭直飞12m，穿2敌。','射程13.5m，穿3敌；尾迹仍细，不长光翼。',
 '15m长箭道穿4敌，箭尖接触闪光与飞行轨迹分开。','16.5m穿5敌，每处穿刺留下短促局部反馈。',
 '18m穿6敌，仍是清晰木箭杆、金属箭头与真实尾羽，极细中性短风迹不超过约一支箭杆长。'],
 '破阵。释放时锁定直线，穿透后衰减20%，最低60%。L02只把后续目标伤害下限提高到70%，不回射、不增加弹体或改变方向。',limits=[2,3,4,5,6],mode='direction')
set_skill('BOW_02','分裂箭','一支主箭首击后从命中点分出限额子箭',[12,13.5,15,16.5,18],
 geom('impactSplitProjectiles','primaryImpact',radiusMetres=[3,4,5,6,7],primaryProjectileCount=1,childProjectileLimit=[1,2,3,4,5],totalTargetLimit=[2,3,4,5,6]),[
 '0.4s前摇后发出一支主箭，12m内首击后从命中点分出最多1支子箭，选3m内另一敌人，合计最多2敌。',
 '13.5m主箭首击后，从冻结命中点分出最多2支子箭，分别飞向4m内不同敌人，合计最多3敌。',
 '15m投送、5m首击半径，主箭首击后最多3支子箭沿分开的平滑弹道飞向不同初始瞄点，合计最多4敌。',
 '16.5m投送、6m首击半径，首击后最多4支子箭分开飞行，薄绿白尾迹与小穿刺闪保持清楚，合计最多5敌。',
 '18m投送、7m首击半径，主箭首击后最多5支子箭从同一命中点分开，固定平滑弹道连接不同初始目标，合计最多6敌；不加羽翼绸带。'],
 '沿用v1原前摇0.4s、释放承诺0.4s、后摇0.25s。发射时只有1支主箭；首个有效敌人接触后主箭结束，冻结命中点、3/4/5/6/7m半径和候选，按中心距/稳定ID选最多1/2/3/4/5名不同额外敌人。每个目标分配1支独立projectileId子箭，主目标已占总2/3/4/5/6名额中的1名。子箭出生时冻结目标初始瞄点和平滑弹道弧线，不在途中追踪或重定向；只对自己被分配的敌人判伤，同cast同敌一次，子箭不能再分裂。子箭保留原75/75/80/85/90%后续倍率与原削韧值，数量不足、目标死亡/移开或被墙截断均不补位或转移伤害；遇墙立即关伤害盒，首击未生效不产生子箭。',
 limits=[2,3,4,5,6],hits=1,mode='direction',**ORIGINAL_BOW02_TIMING)
set_skill('BOW_03','疾风连射','远程同向连续实体箭',[12,13.5,15,16.5,18],
 geom('projectileCorridor',lengthMetres=[12,13.5,15,16.5,18],widthMetres=[.3,.32,.35,.38,.4]),[
 '三箭快速连发至12m。','13.5m连射，三条尾迹分明。','15m四箭连射，末箭接触更重。',
 '16.5m四箭沿同向窄道穿梭，只有小范围穿刺闪。','18m五箭密集连射，形成细长箭路，保持实体羽箭而非大光束。'],
 '保留3/3/4/4/5弹，各弹平分总倍率，间隔0.10s；每枚箭只命中首个碰到的敌人。前敌先死时后箭可命中其他敌，整cast不同目标上限不超过弹数，不静默丢掉合法接触。',limits=[3,3,4,4,5],mode='direction')
set_skill('BOW_04','猎王印','远处单体弱点标记',[14,15,16,17,18],
 geom('singleTarget','selectedTarget'),[
 '14m内目标肩部亮一枚短猎痕。','15m弱点猎痕加一条箭刻。','16m首次后续命中产生局部护甲粉尘。',
 '17m猎痕在护甲接缝处短亮，仍不包住角色。','18m弱点出现五条精细箭刻，后续命中在接触点爆出短促破甲闪。'],
 '8s内自己对目标直接技能增伤8/9/10/11/12%，使用hunterMark；标记不因命中被消费，同类刷新不叠层。',limits=[1]*5,mode='single')
set_skill('BOW_05','万箭齐发','远处选区内的离散箭列',[14,15,16,17,18],
 geom('targetVolley','aimPoint',widthMetres=[5,6,7,8.5,10],depthMetres=[4,4.5,5,5.5,6]),[
 '对14m内远端小队释放三拍箭列，每个目标有自己的箭路。','15m选区加宽，箭列分左右两组落向敌人。',
 '16m选区内多条冻结直线错层交织，实际命中点逐个可见。','17m选区扩为8.5m宽，第三拍仍沿释放时直线射向初始位置，敌人移动可躲开。',
 '18m远处10m宽敌阵被三拍箭列覆盖，所有攻击保持细长离散弹道；没有巨型天弓、星环或爆炸圆盘。'],
 '释放时选区内可见可达敌人的位置只用于确定各枚箭的初始直线方向；起点与各条直线在释放时固定，后续不追踪。三拍伤害20%/30%/50%，箭数是释放时分配目标数×3；目标移动出箭路可躲开。实际箭碰到首个合法敌人或墙即结束，每敌每拍最多一次，不补射墙后、不按装饰箭数加伤。',hits=3)

set_skill('FIR_01','赤焰枪','远距火弹及小接触爆核',[12,13.5,15,16.5,18],
 geom('projectileWithImpactDisk','projectileImpact',radiusMetres=[.45,.6,.75,.9,1.1]),[
 '白芯焰枪射向12m目标，接触爆出紧凑火花。','13.5m火弹外壳卷动，接触爆核略宽。',
 '15m火枪命中0.75m邻域，能看见地面接触。','16.5m投送，橙红火核在接触处向低处翻卷。',
 '18m焰枪击中远方，在1.1m邻域爆出短促实心火团，不悬空摆凤凰。'],
 '接触后小圆盘内有效敌同受直接伤，附基础3s燃烧0.15S/s；余烬掌握实际增加施加时长，最长4s。墙会截断并在可达墙前爆开。')
set_skill('FIR_02','焚星坠落','远处火核下坠后的球状爆燃',[12,13.5,15,16.5,18],
 geom('filledImpactDisk','aimPoint',radiusMetres=[2.8,3.2,3.6,4,4.5]),[
 '密实火核落向12m外选点，短压缩后翻卷成球状爆燃，2.8m命中半径内中心与边缘都受击。','13.5m选点、3.2m半径，炽亮火核下坠更清楚，球状火焰膨胀后迅速退成余烬。',
 '15m选点、3.6m半径，主火团翻卷爆燃后0.30s同范围二次内燃，焦痕短留。',
 '16.5m选点、4m半径，密实火核短压缩后轰然膨开，火团外壳翻卷，接触火星快速散落。',
 '18m投送、4.5m半径，沉重火核下坠、短压缩、球状翻卷爆燃与错拍二次内燃形成爆发，余烬和短焦痕迅速退去。'],
 '破阵。1—2级一次主爆；3—5级75%主爆+25%次爆。全圆盘所有可达合法敌人都判定，不保留旧5目标上限；主爆内部与边缘等伤，不把空心光环当命中区。爆后快速降低不透明度，预警置顶。')
set_skill('FIR_03','焰心护盾','自身短护盾',[0]*5,geom('selfShield'),[
 '薄焰贴住前臂与肩部，持续4s。','两片低亮火羽贴身护住要害。','受击位置局部爆出炽点，护盾其余部分透明。',
 '护体火羽增加到四片，不遮脚部。','受击时凤凰羽纹一闪即收，不出现环绕全身的巨大光冠。'],
 '保留15/18/21/24/27%最大生命护盾4s；自保例外，不判附近敌人伤害。',limits=[1]*5,mode='self')
set_skill('FIR_04','炎墙封路','远处指定线段火域',[12,13.5,15,16.5,18],
 geom('placedStrip','aimPoint',lengthMetres=[4,5,6,7.5,9],widthMetres=[1.2,1.35,1.5,1.7,2]),[
 '在12m外放出4m长连续低火墙，人物不冲过去。','13.5m选点，5m火域填满条带。',
 '15m选点，6m火墙形成高低交错的火舌，脚部区域连续燃烧。','16.5m选点，7.5m火域横切敌阵，末端短促迸出焰浪。',
 '18m选点，9m长、2m宽火域沿战线燃烧，保持条形而非圆盘。'],
 '施放前可旋转线段，持续3s，3/3/3/4/4拍均分本级总倍率。它是法术地面区，不新增实体墙，不挡路、不点燃物品。替代原自身掠影。')
set_skill('FIR_05','焚天火海','远端宽矩形滚动火浪',[14,15,16,17,18],
 geom('filledWaveRectangle','aimPoint',widthMetres=[7,8,9,10.5,12],depthMetres=[4,5,6,7,8]),[
 '14m外一道宽7m厚重火焰锋面横过敌群，主爆后四拍余焰。','15m选点，宽8m火焰锋面连续翻卷，矩形内部都有真实接触。',
 '16m选点，9m宽厚重横向锋面从近缘推进到远缘，多敌按前缘抵达先后受击。',
 '17m选点，10.5m宽火焰锋面分层翻卷，四拍余焰低位短燃后退亮。',
 '18m外12m×8m区域被一道厚重横向火焰锋面扫过，连续火体与四拍余焰构成爆发，不画地面重复枝纹或蛇纹。'],
 '主爆40%+四拍各15%；所有合法区域内敌人均可受击，不设5/8个隐藏目标截断。初始波前0.30s内扫完，后续场3s可走离；不是推着敌人移动。')

set_skill('THU_01','贯雷长矛','远程瞬发直线电弧',[14,15.5,17,18.5,20],
 geom('instantCorridor',lengthMetres=[14,15.5,17,18.5,20],widthMetres=[.65,.8,.95,1.1,1.3]),[
 '14m直线雷矛瞬间接触路径前2敌。','15.5m电矛穿3敌，雷裂短促明亮。','17m穿4敌，主干粗、侧枝细，方向清楚。',
 '18.5m穿5敌，路径出现局部接点爆闪。','20m贯雷长线击穿前6敌，不画竖直雷柱或长时间激光。'],
 '破阵。释放点锁直线，按距离取路径前2/3/4/5/6个可达敌，每敌一次；墙截断，装饰分叉不增加伤害。',limits=[2,3,4,5,6],mode='direction')
set_skill('THU_02','连锁雷弧','首命中中心固定半径与固定总数量',[12,13.5,15,16.5,18],
 geom('boundedArcGraph','primaryImpact',radiusMetres=[3,4,5,6.5,8],totalTargetLimit=[2,3,4,6,8]),[
 '首目标命中后，只连接其3m内1名额外敌人，总2目标。','4m连接半径、总3目标，主干分成两条短雷弧。',
 '5m连接半径、总4目标，主干和三支侧弧横跨敌阵。','6.5m连接半径、总6目标，宽幅雷网连接更多不同敌人。',
 '8m连接半径、总8目标，首命中周围16m跨度内形成大范围分叉雷弧；不得向圈外继续招募目标。'],
 '数量含首目标。中心在首次命中瞬间冻结；候选必须同场同层、敌对存活、位于中心半径内并有合法无遮挡连接；按中心距离、稳定ID排序。主目标全伤，额外目标各70%；每cast每敌一次，不回跳、不补空位、不因主目标死亡移动中心。技能雷弧不是装备额外链。',
 limits=[2,3,4,6,8],power=[1.6,1.85,2.2,2.65,3.2],hits=1,mode='single')
set_skill('THU_03','雷霆战印','自身三次基础攻击附雷',[0]*5,geom('selfBuff'),[
 '一条细雷纹附在武器上。','两道雷纹在武器接触时短亮。','三枚小电片表示剩余三次附雷。','武器边缘形成短电叉，命中才放大。',
 '武器上细密雷纹在三次基础命中时依次爆闪，不包成全身雷冠。'],
 '保留6s内三次基础附雷，三份均分本级总倍率；附雷不再次连锁或刷蓄能，施法本身不打附近敌人。',limits=[1]*5,mode='self')
set_skill('THU_04','扇雷横扫','远处选点内的扇面分叉',[12,13.5,15,16.5,18],
 geom('boundedArcFan','aimPoint',radiusMetres=[4,4.5,5,6,7],angleDegrees=[70,80,90,100,110],totalTargetLimit=[3,4,5,6,8]),[
 '12m外选点，4m/70°扇面内连接最多3敌。','13.5m投送，4.5m/80°分叉面连接4敌。',
 '15m投送，5m/90°宽面雷弧连接5敌。','16.5m投送，6m/100°横向电叉连接6敌。',
 '18m外7m/110°宽面最多连接8敌，一次扇雷横扫，角色不冲进敌群。'],
 '以远处选点为扇面起点、按施法朝向展开；固定几何内按稳定排序冻结目标集合，数量不足不回跳。两拍各50%，同一目标每拍一次；每拍重验存活敌对、同场同层、固定扇面与无遮挡连接，失效者本拍跳过且不补位。替代原自身电冲。',limits=[3,4,5,6,8],hits=2)
set_skill('THU_05','万钧雷潮','远端固定范围内的大型限额雷网',[14,15,16,17,18],
 geom('boundedPulseGraph','aimPoint',radiusMetres=[4,5,6,7.5,9],totalTargetLimit=[4,6,8,10,12]),[
 '14m外4m范围连接最多4敌，三拍电弧爆发。','15m外5m范围连接6敌，横向电网展开。',
 '16m外6m范围连接8敌，粗主干与多处接点同步爆闪。','17m外7.5m范围最多10敌，三拍宽雷网快速爬满目标区。',
 '18m外9m范围最多12敌，大片不规则雷弧在敌人之间横向贯通，三拍雷裂收尾；没有雷柱、九角冠或圆笼。'],
 '释放时冻结中心，首拍冻结目标集合，三拍间隔0.25s，每敌每拍最多一次；三拍均分总倍率。每拍重验存活敌对、同场同层、固定范围与无遮挡连接，走出范围或被遮挡者本拍跳过；死亡者退出，不招募新目标补位，不把每条电边都算伤害。',limits=[4,6,8,10,12],hits=3)

# Common skills remain base utilities. They do not masquerade as remote attacks.
for key in ['COM_01','COM_02']:
    s=LOOKUP[key]
    s['targetingMode']='self'
    s['offensive']=False
    for rank in s['ranks']:
        rank['castRangeMetres']=rank['rangeMetres']
        rank['geometry']=dict(kind='selfRelocation' if key=='COM_01' else 'selfHeal',origin='self')
        rank['targetLimit']=1

# Precise graph rules, not implicit or recursively multiplying lightning edges.
for key in ['THU_02','THU_04','THU_05']:
    s=LOOKUP[key]
    s['graphPolicy']=dict(countIncludesPrimary=key=='THU_02',freezeCenterAt='firstValidImpact' if key=='THU_02' else 'release',
                         freezeTargetsAt={'THU_02':'firstValidImpact','THU_04':'release','THU_05':'firstPulse'}[key],
                         candidateFilter='hostile,alive,sameScene,sameConnectedLayer,insideFixedEnvelope,unoccluded',
                         ordering=['distanceToFrozenCenter','stableEntityId'],recruitOutsideEnvelope=False,
                         selectionUnique=True,selectionTargetRevisit=False,maxHitsPerTargetPerPulse=1,
                         hitLedgerKey=['castId','targetId','pulseIndex'],recruitAfterFirstPulse=False,
                         revalidatePerPulse=True,
                         perPulseFilter='hostile,alive,sameScene,sameConnectedLayer,insideFrozenGeometry,unoccludedLegalConnection',
                         invalidTargetPulsePolicy='skip this pulse without replacement; dead targets exit',
                         missingTargetDamageRedistributed=False)
    for rank in s['ranks']:
        rank['chainTargetLimit']=rank['targetLimit']
        rank['connectionRadiusMetres']=rank['geometry']['radiusMetres']
        if key=='THU_02':
            rank['damagePerSecondaryTargetS']=round(rank['maxDamagePerTargetS']*.7,4)
            rank['totalCastDamageBudgetS']=round(rank['maxDamagePerTargetS']+rank['damagePerSecondaryTargetS']*(rank['targetLimit']-1),4)
for rank,fraction in zip(LOOKUP['BOW_02']['ranks'],[.75,.75,.8,.85,.9]):
    rank['followUpDamageFraction']=fraction
LOOKUP['BOW_02']['projectilePolicy']=dict(
    primaryProjectileCount=1,primaryEndsAt='firstValidHostileImpact',splitTrigger='firstValidPrimaryImpactOnly',
    freezeCenterAndSelectionAt='firstValidPrimaryImpact',childLimitFromRank='geometry.childProjectileLimit',
    totalCountIncludesPrimary=True,selectionOrdering=['distanceToFrozenImpactCenter','stableEntityId'],
    candidateFilter='hostile,alive,sameScene,sameConnectedLayer,insideFrozenImpactRadius,legalUnoccludedBallisticPath,notPreviouslyHit',
    excludePrimaryTarget=True,selectionUnique=True,distinctProjectileIds=True,
    oneChildPerSelectedTarget=True,damageOnlyAssignedTarget=True,childGenerationDepthLimit=1,
    childPath='fixedBallisticPath',freezeChildAimPointAndPathAt='firstValidPrimaryImpact',
    noMidflightRetarget=True,homing=False,childMaySplit=False,recruitAfterSplit=False,
    childTravelEndsAt='frozen initial aim point or earlier collision',ignorePrimaryColliderOnSpawn=True,
    nonAssignedHostileContact='end child without damage or reassignment',
    revalidateAtEveryContact=True,
    childContactFilter='assignedTarget,hostile,alive,sameScene,sameConnectedLayer,insideFrozenImpactRadius,unoccludedSweptTravelSegment,notPreviouslyHit',
    hitLedgerKey=['castId','targetId'],uniqueTargetsPerCast=True,
    wallHitEndsProjectile=True,missingTargetDamageRedistributed=False,
    damageDisabledBefore=['assignedTargetHit','wallHit','frozenPathEnd','targetInvalid','cancelOrDespawn'],
    terminalVisualFlightDealsDamage=False)
LOOKUP['BOW_03']['maxTargetsPerProjectile']=1
LOOKUP['BOW_03']['targetLimitScope']='perCastDistinctTargets, bounded by projectile count'
for key in ['BOW_01','BOW_03']:
    LOOKUP[key]['projectilePolicy']=dict(freezeDirectionAt='release',homing=False,mayChangeFlightDirection=False,
                                       wallHitEndsProjectile=True,returnFlight=False)
LOOKUP['BOW_05']['volleyPolicy']=dict(
    freezeOriginAndAimPositionsAt='release',launchOrigin='releaseCasterPosition',
    initialDirection='straight ray from release origin to allocated release aim position',
    homing=False,mayChangeFlightDirection=False,pulseCount=3,damageFractions=[.2,.3,.5],
    actualProjectileCount='allocatedReleaseTargetCount * 3',
    wallHitEndsProjectile=True,firstValidHostileHitEndsProjectile=True,
    hitLedgerKey=['castId','targetId','pulseIndex'],maxHitsPerTargetPerPulse=1,
    movingOutOfArrowPathDodges=True,reassignAfterRelease=False,missingTargetDamageRedistributed=False)
for key,text in {
 'FIR_02':'远处火核与短压缩给出爆点提示；走出固定圆盘可避主爆，走离或用合法遮挡可避后续次爆。',
 'FIR_05':'横向火焰锋面方向可读；侧移离开矩形或尽快走出余焰，遮挡后区域不判伤。',
 'BOW_02':'首箭命中后才分裂；子箭路径在出生时固定，目标移动离开可躲开，墙体截断载荷；不足名额不补打主目标，子箭不递归分裂。',
}.items():LOOKUP[key]['counterplay']=text

PASSIVE_VISUALS={
 'WAR_P1':'技能发射口与飞刃接触处由一到五条金属细纹增强，不在人物背后造剑冠。',
 'WAR_P2':'盾面局部受击裂纹从一条增至五条，甲片仍贴住身体。',
 'BOW_P1':'目标护甲弱点从一处细亮点成长为五条箭刻，不围成光环。',
 'BOW_P2':'加速时脚边只有低亮中性短尘迹，成长以短促节拍更清楚表现，不给箭体增加发光拖尾。',
 'FIR_P1':'敌人身上的低位燃烧从稀疏火星变为连续短焰，不升成遮人火柱。',
 'FIR_P2':'击败后的接触爆点由三点火花成长为扁平火舌，传播只有两条短焰线。',
 'THU_P1':'武器触点的电叉由单叉变多叉，只有命中时显亮。',
 'THU_P2':'真实连接到三名敌人后，肩前出现由一到五道短雷痕，不包圆。',
}
for key,visual in PASSIVE_VISUALS.items():LOOKUP[key]['visual']=visual
LOOKUP['FIR_P1']['effect']='自身施加的基础3s燃烧额外延长0.2/0.4/0.6/0.8/1.0s；与J01同类延长取最大，最后不超过4s。'
for rank,bonus in zip(LOOKUP['FIR_P1']['ranks'],[.2,.4,.6,.8,1]):
    rank.update(primaryValue=bonus,burnDurationBonusSeconds=bonus,
                effect=f'自身基础3s燃烧延长{bonus}s；与J01取最大，最后≤4s。')
LOOKUP['THU_P2']['procCounter']='distinctValidEnemyIdsPerCast, not graphEdges or pulses'

STYLES={
 'WAR':dict(name='破军战技',color='细长单层银白月牙、稀疏金色风痕与接触金尘',shape='远距飞刃与长走廊',timing='飞行抵达→连续切口→远端重斩',silhouette='bladeCorridor'),
 'BOW':dict(name='逐风弓术',color='真实木箭杆/金属箭头；分裂箭用薄绿白尾迹',shape='直线箭与首击后从命中点分出的限额子箭',timing='主箭飞行→首击→子箭固定分开弹道→小穿刺闪',silhouette='impactSplitArrows'),
 'FIR':dict(name='烈焰秘术',color='炽橙、深红、密实短白芯火核',shape='下坠火核、球状爆燃与横向火焰锋面',timing='火核下坠→短压缩→翻卷爆燃→余烬',silhouette='volumetricFireburst'),
 'THU':dict(name='雷霆秘术',color='电蓝白主干、细紫叉电',shape='固定半径、限额横向雷弧网',timing='主干命中→多点分叉→同步接触闪',silhouette='boundedGraph'),
 'COM':dict(name='通用技能',color='青白步迹、柔金复苏',shape='自身移动或恢复',timing='独立生效',silhouette='utility'),
}
SPECTACLE={
 'WAR':'沿用最初combat-war.png的细长单层锐利银白月牙与稀疏金风痕；方向性短尾衬出速度。真实抵达目标时金属斩裂、银锋断闪、定向金尘分层迸开并迅速退亮，等级越高接触组织越清楚；不加厚或堆多层巨刃，主角与目标保持远距。',
 'BOW':'穿云箭、疾风连射、万箭齐发保持释放直线；分裂箭沿最初combat-bow.png细淡首击分支，主箭命中后子箭才从命中点分开，固定平滑弹道与真实数量不变。强化各子箭尖锐穿刺闪、短粉尘与尾迹断点的强节拍，逐级更清楚而不放大成羽翼、绸带或光带。',
 'FIR':'强化厚实体积：白金瞬核短压缩后红橙火体翻卷，真实接触处的压力亮面/火屑/余爆材质分层展开再迅速退亮；余爆只是同一已声明接触的表现层，不新增伤害拍数。横向火焰锋面仍按原矩形，余烬/焦痕短留，不画重复枝纹铺毯或蛇纹。',
 'THU':'保留combat-thu.png认可的横向电弧形，主干/有限侧枝与既定目标人数不变；各真实触点增加电芯短闪、细散电与短局部爆闪的层次，随等级更清楚后快速退亮，不新增选敌或把横弧堆成巨型光团。',
 'COM':'保持清楚的步迹与恢复光瓣，作为主攻爆发之间的低亮功能层。',
}
VFX_OVERRIDES={
 'BOW_01':('projectile','唯一主箭是木箭杆、金属箭头与真实尾羽，沿释放直线快速贯穿；极细中性风迹最多约箭杆长，接触只有小穿刺闪和粉尘。L02仅强化后续穿透伤害，不回射或多画箭体。'),
 'BOW_02':('firstImpactAndChildProjectiles','先只有一支木杆金属主箭；首击后才从同一命中点分出1/2/3/4/5支真实子箭，沿各自冻结的平滑弹道分开飞向不同初始瞄点。薄绿白尾迹、小穿刺闪恢复最初观感，不加羽翼绸带，不画单箭一路绕行或提前出现子箭。'),
 'BOW_03':('independentProjectiles','3/3/4/4/5枚真实木杆金属箭快速连射，每枚独立箭头和尾羽可同时在途；极细中性风迹最多约箭杆长，命中只给小穿刺闪和粉尘，不分裂。'),
 'BOW_04':('selectedTarget','低亮中性猎痕贴在远处护甲接缝，逐级增加细小箭刻；后续真实命中只有小穿刺闪与护甲粉尘，施加印记本身不生成实体箭或发光拖尾。'),
 'BOW_05':('targetVolley','远处选区内三拍真实木杆金属箭列，每条箭路从释放起点沿冻结直线飞往初始瞄点；敌人移动可躲开。实际箭头和尾羽清楚，极细中性短风迹最多约箭杆长，接触仅小穿刺闪与粉尘。'),
 'FIR_02':('aimPoint','密实炽橙白芯火核从上方下坠，接触前短压缩，随后球状火体翻卷爆燃；中心与边缘真实受击，余烬和焦痕短留，不沿地面画重复枝纹或铺毯。'),
 'FIR_05':('authoredRectangle','远端矩形内一道厚重横向火焰锋面向前扫过，主爆后四拍余焰低位翻卷；火体连续、接触强而短，不画蛇纹或重复地面枝纹。'),
 'WAR_03':('caster','钢银盾片和低亮金边贴住自身前臂、胸前；受击处局部金属重闪，碎片低位消散；覆盖自身防护位置，不画远端剑气、落刃或爆炸。'),
 'FIR_03':('caster','炽橙白金薄焰与短凤凰羽纹贴住自身肩臂，受击处局部火星爆闪后快速透明；覆盖自身护盾，不在远处画爆燃面，也不暗示附近敌人受伤。'),
 'THU_03':('casterWeaponAndActualBasicHit','紫白细雷纹贴住自身武器，三枚小电片依次熄灭；只有三次真实基础命中处放大短电叉，不在施法时画远端雷网或自身伤害圈。'),
 'COM_01':('casterAndOwnEndpoint','青白短步迹沿自身真实移动路径消散，起终点保持脚部锚点；不画远端敌人接触或攻击爆炸。'),
 'COM_02':('caster','柔金复苏光瓣贴住自身胸侧与脚边，恢复节拍短亮后透明；不画远端目标命中或攻击爆炸。'),
}
for style,spec in SPECTACLE.items():STYLES[style]['spectacle']=spec
for skill in SKILLS:
    if skill['type']!='passive':
        for rank in skill['ranks']:
            rank['vfxAnchor'],rank['vfxDirection']=VFX_OVERRIDES.get(skill['id'],('authoredGeometry',SPECTACLE[skill['style']]))
            rank['peakDurationSeconds']=[.08,.09,.10,.12,.14][rank['rank']-1]
            rank['visualEvolutionDoesNotChangeHitBudget']=True
VFX_GROWTH=[
 '初阶先清楚显示主轮廓、材质内外差和方向短尾，实际接触短促可辨。',
 '强化主副材质的分界与边缘细节，短尾前后层次更清楚，接触分出亮面和细碎片。',
 '细化流动/折光/金属表面的内部层次，方向短尾有节奏，接触前后层分明。',
 '加强抵达目标时的局部材质张开、定向碎片与短压缩层，爆发后立刻降低亮度。',
 '完整表现清楚主形、精细材质、方向短尾和同一次接触的层次爆发，快速退亮让出预警。',
]
VFX_MATERIAL={
 'WAR':'首版单层锐利银白薄月牙，稀疏金风痕/方向短尾；真实接触金属斩裂、银闪与定向金尘分层，不加厚或堆多层巨刃。',
 'BOW':'原真实箭体与细淡首击分裂不变；金属箭尖、每支子箭穿刺闪/短粉尘/尾迹断点形成强节拍，不长羽翼光带。',
 'FIR':'厚实体积、白金瞬核、红橙内外翻卷和真实接触余爆/火屑分层；只加强已有接触表现，不增加伤害拍数。',
 'THU':'认可横弧的主干/有限侧枝不变；真实触点的电芯短闪/细散电/局部爆闪分层，人数与选敌不变。',
 'COM':'自身步迹/恢复光瓣内部明暗与边缘层次更清楚，保持功能位置与低遮挡。',
}
for skill in SKILLS:
    for rank in skill['ranks']:
        own_event=skill['type']=='passive' or skill.get('targetingMode')=='self'
        rank['vfxLayers']=dict(
            growth=VFX_GROWTH[rank['rank']-1],material=VFX_MATERIAL[skill['style']],
            direction='沿已声明的真实弹道/波前给短方向尾迹，不扩范围、不改变轨迹或弹体数。' if not own_event else '沿原自身/武器/被动触发锚点给短局部方向纹，不生成远处进攻表现。',
            contact='只在同一次真实命中内部组织材质亮面、少量定向碎片和短接触层；不增加击次。' if not own_event else '仅在已声明的自身恢复/护盾受击/位移起终点/实际基础命中/被动事件位置分层，施法不额外攻击。',
            fade='峰值后快速退亮和透明，敌方预警始终清楚；装饰层不改变S/CD/目标上限/等级门槛。')
ALIASES={old:LOOKUP[key]['name'] for key,old in ORIGINAL_NAMES.items() if key in LOOKUP and old!=LOOKUP[key]['name']}
def rename(text):
    for old,new in sorted(ALIASES.items(),key=lambda p:len(p[0]),reverse=True):text=text.replace(old,new)
    return text.replace('四系法术','火雷两系法术')

CAT['progression']['attributes']['intellect']=rename(CAT['progression']['attributes']['intellect'])
CAT['retiredSpellToSkill'].update(T01='FIR_01',T02='BOW_04',T03='THU_01',T05='THU_04',T08='THU_05')

CAT.update(schemaVersion=2,contentVersion='pure-skills-v2-ranged-differentiated',styles=STYLES,
           previousBase='source-art/skills/pure-skills-v1/skill-catalog.json',skillNameAliases=ALIASES,
           status='concept-revision-awaiting-user-review',conceptReviewStatus='pending-user-review',
           retiredSkillIds=RETIRED_SKILL_IDS,retiredStyleIds=['FRO','ARC'],
           temporarilyRetiredSkillIds=TEMPORARILY_RETIRED_SKILL_IDS,temporarilyRetiredStyleIds=['ARC'],
           retirementPolicy='FRO removed and ARC temporarily withdrawn; all 14 IDs are history only with no selectable skills or active unlocks. Preserved catalogs and images remain history.',
           bodyScaleChanged=False,runtimeImplemented=False)
CAT['rules'].update(dict(
    nativeSkillSegments='declared arrow contacts, bounded first-impact split children and lightning pulses; not equipment procs',
    aimNeverAutoApproaches=True,
    targetRangeAlias='ranks.rangeMetres is compatibility alias of castRangeMetres; geometry is the only AOE authority',
    noHiddenAreaTargetLimit='filled fire area checks all valid targets; performance may not discard sixth/eighth actor',
    playerStyles=['WAR','BOW','FIR','THU'],straightBowSkillIds=['BOW_01','BOW_03','BOW_05'],
    splitBowSkillId='BOW_02',splitChildPathsFrozenAtFirstImpact=True,
    graphicNotRangeProof='concept images illustrate separation, exact metre values come from data',
    graphCountRule='THU_02/04/05 use fixed rank-specific radius and fixed total target count, no recruitment outside envelope'))

EXTRA_ITEM_EFFECTS={
 'W04':'破军交斩直接命中2敌后，下一断空剑气伤害+8%，4s内一次，CD8s。',
 'W06':'直接主动技能命中自己的猎王印目标时得8护盾3s，CD10s，每cast一次；不消费或刷新猎王印，不触发额外攻击。',
 'W09':'穿云箭命中施加牵制：移速-25%/3s，CD8s；Boss仅移速-10%，不改变出招时序；这是箭术减速，不施加冰系寒缓。',
 'W12':'焚星坠落主爆附基础3s燃烧0.15S/s，受余烬掌握/J01时长修正，最终≤4s。',
 'W13':'贯雷长矛首个实际命中若为自己的猎王印目标，额外削韧4，CD4s，Boss额外2，每cast一次；不增加目标或电弧。',
 'W14':'贯雷长矛主命中追加0.35S雷伤，CD8s；不增加连锁雷弧目标上限或连接半径。',
 'W16':'火焰、雷霆两系法术直接伤害+5%，非终极冷却缩短4%，受统一上限约束。',
 'A08':'雷系直接命中自己的猎王印目标后，当前剩余时间最长的非终极技能冷却-0.5s，CD8s，每cast一次；不消费猎王印。',
 'J01':'自身燃烧实际施加时长额外+1s；与余烬掌握同类延长取最大，最终≤4s。',
 'J02':'对自己猎王印目标的直接技能伤害+6%，计入统一增伤上限。',
 'J03':'直接主动命中自己的hunterMark目标，终极蓄能额外+2，CD3s，同cast一次；不消费印记。',
 'J05':'直接雷技能命中自己的燃烧目标，清燃烧并追加0.35S雷伤，CD8s；次级事件不再触发。',
 'L02':'仅穿云箭BOW_01第二个及以后目标的穿透伤害下限由60%提高到70%，每敌每cast一次，受统一上限；不回射、不改变方向、不增加弹体，不作用于分裂箭。',
 'DR2-03':'赤焰枪首个实际接触对普通盾卫额外削韧4，Boss+2，CD6s，每cast一次；接触爆核不重复触发。',
 'DR4-03':'断空剑气打开普通盾后，下一破军交斩削韧+4，3s内一次，CD6s；Boss+2。',
 'DU1-04':'每第三次法术施放实际直接命中，追加4雷伤，CD3s；不是每枚弹或电边计一次，次级事件不再触发。',
 'DU2-03':'直接技能命中自己的猎王印目标，终极蓄能额外+2，CD4s，同次施放一次，仍受每cast蓄能奖励上限。',
 'DU2-04':'穿云箭命中自己的猎王印目标，追加4雷伤，CD4s，同cast一次；不复制或刷新印记，次级事件不再触发。',
 'DE08':'非终极火/雷技能每次施放首次直接命中自己的猎王印目标时，该次命中伤害+8%，CD10s，计入统一增伤上限；只修正已有命中，不生成技能或额外载荷。',
}
for key,effect in list(CAT['equipmentEffects'].items()):CAT['equipmentEffects'][key]=rename(effect)
CAT['equipmentEffects'].update(EXTRA_ITEM_EFFECTS)
CAT['compatibilityAdaptations']=[
 dict(id='W09',reason='保留原减速比例/时长/CD，改为箭术牵制，不提供玩家冰法载荷'),
 dict(id='W06',reason='旧秘印消费改直接主动命中自己的猎王印；保留8护盾/3s/10s CD，标记不消费，每cast一次'),
 dict(id='W13',reason='退役法术联动改贯雷长矛首个命中为自己的猎王印目标；保留4/2削韧与4s CD'),
 dict(id='W16',reason='玩家法术只保留火/雷两系；原5%/4%数值不变'),
 dict(id='A08',reason='退役印记联动改雷技能命中自己猎王印；保留0.5s冷却返还与8s CD，单cast一次'),
 dict(id='J02',reason='原寒缓增伤改自己猎王印增伤；保留6%'),
 dict(id='J03',reason='删除退役印记分支，只读取hunterMark；保留+2/3s和单cast上限'),
 dict(id='J05',reason='条件和0.35S/8s不变，附伤改雷伤且不递归'),
 dict(id='DR2-03',reason='退役飞弹触发改赤焰枪首个接触；保留4/2削韧与6s CD，不按爆核重复'),
 dict(id='DU1-04',reason='原附伤改4雷伤，原三次实际法术施放/3s CD/单次计数不变'),
 dict(id='DU2-03',reason='退役印记目标改自己猎王印；保留+2/4s及单cast上限'),
 dict(id='DU2-04',reason='目标改自己猎王印，附伤改4雷伤；保留4s CD，不复制印记或递归'),
 dict(id='DE08',reason='原回响装备改非终极火雷首次直接命中自己猎王印+8%；加10s CD且仅修正已有命中，不产生新技能'),
 dict(id='T01',replacementSkillId='FIR_01',reason='旧符迁移赤焰枪，仍按现有角色门槛'),
 dict(id='T02',replacementSkillId='BOW_04',reason='旧印记符迁移猎王印；角色等级不足仍锁定'),
 dict(id='T03',replacementSkillId='THU_01',reason='旧符迁移贯雷长矛，不恢复暂退职业或复制机制'),
 dict(id='T05',replacementSkillId='THU_04',reason='旧符迁移改现有扇雷横扫，仍按其角色等级门槛解锁，不恢复退役冰技能'),
 dict(id='T08',replacementSkillId='THU_05',reason='终誓外观与旧符迁移万钧雷潮；仍按终极等级门槛，不提前解锁'),
 dict(id='L02',reason='取消回程50%额外命中，保守改穿云箭后续伤害最低60%→70%；无回射或额外弹体'),
]

def rewrite_strings(value):
    if isinstance(value,str):return rename(value)
    if isinstance(value,list):return [rewrite_strings(v) for v in value]
    if isinstance(value,dict):return {k:rewrite_strings(v) for k,v in value.items()}
    return value
WORLD=rewrite_strings(WORLD)
WORLD.update(contentVersion='campaign-v8-ranged-skills-design',skillCatalog='source-art/skills/pure-skills-v2/skill-catalog.json',
             status='concept-revision-awaiting-user-review; not runtime content',conceptReviewStatus='pending-user-review',
             retiredSkillIds=RETIRED_SKILL_IDS,temporarilyRetiredSkillIds=TEMPORARILY_RETIRED_SKILL_IDS,playerStyleIds=['WAR','BOW','FIR','THU'],
             compatibilityAdaptations=copy.deepcopy(CAT['compatibilityAdaptations']))
WORLD['validation'].update(skills=30,skillRankRecords=150)
for item in WORLD['legacyEquipment']+WORLD['retainedLegendaries']+WORLD['newEquipment']:
    item['effect']=CAT['equipmentEffects'][item['id']]
for mob in WORLD['enemies']:
    mob['hitReactionDoesNotMoveEnemy']=True
    mob['damagedAwarenessRangeMetres']=20
    if any(word in mob['role'] for word in ['远程','控场','支援']):mob['recommendedCounterRangeMetres']=[14,18]
for node in WORLD['levels']:
    node['reward']=node['reward'].replace(ORIGINAL_NAMES['ARC_05']+'·终誓外观',LOOKUP['THU_05']['name']+'·终誓外观')
    if node['encounter']!='无':
        node['rangedLayoutReview']='not implemented; verify visible 12–18m firing lanes, cover and legal exits'
for boss in WORLD['bosses']:
    boss['recommendedArenaClearMetres']=[36,26] if boss['mandatory'] else [30,24]
    boss['rangedResponse']='ranged threat or visible approach; never teleport to negate range or require player to melee'
WORLD['rules'].update(dict(
    lightningSelection='fixed radius and total target cap per rank, primary counts in THU_02; no unbounded chain',
    elementalArea='all eligible targets in declared fire shape are checked; graphical boundary never substitutes for geometry',
    rangedIntegration='current runtime still has 4.5m preview clamp and mobile orthoHeight=3; v2 is not applied to gameplay',
    nativeVsProc='arrow contacts, bounded first-impact split children and lightning graph are authored skill damage; 2-item proc budget applies only to equipment',
    playerStyleRemoval='FRO removed and ARC temporarily withdrawn; both are history only. Cold enemies/environment and defensive cold resistance do not require a player ice profession',
    arenaReview='old 12×10/14×12m boss arenas require layout expansion or alternate legal firing lanes before ranged gameplay acceptance'))

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+
                     ['| '+' | '.join(str(v).replace('|','／').replace('\n','<br>') for v in row)+' |' for row in rows])

def geometry_text(g):
    labels={'radiusMetres':'半径','lengthMetres':'长度','widthMetres':'宽','depthMetres':'深','laneWidthMetres':'单带宽','spanMetres':'跨距','distanceMetres':'自身距离'}
    pieces=[labels[k]+str(v)+'m' for k,v in g.items() if k in labels]
    if 'angleDegrees' in g:pieces.append('扇角'+str(g['angleDegrees'])+'°')
    if 'projectileCount' in g:pieces.append(str(g['projectileCount'])+'实体弹体')
    if 'primaryProjectileCount' in g:pieces.append(str(g['primaryProjectileCount'])+'支主箭')
    if 'childProjectileLimit' in g:pieces.append('首击后子箭≤'+str(g['childProjectileLimit']))
    if 'totalTargetLimit' in g:pieces.append('总目标≤'+str(g['totalTargetLimit']))
    if 'payloadsPerTarget' in g:pieces.append('每目标'+str(g['payloadsPerTarget'])+'枚载荷')
    if 'anglesDegrees' in g:pieces.append('方向'+str(g['anglesDegrees']))
    return '；'.join(pieces) or g['kind']

def export():
    assert len(SKILLS)==30 and sum(len(s['ranks']) for s in SKILLS)==150
    assert not set(RETIRED_SKILL_IDS)&set(LOOKUP) and not {'FRO','ARC'}&set(STYLES)
    assert all(key in LOOKUP for key in CAT['retiredSpellToSkill'].values())
    for s in SKILLS:
        assert ORIGINAL_GATES[s['id']]==[r['requiredCharacterLevel'] for r in s['ranks']]
        assert s['consumableCost']==s['resourceCost']==s['enemyForcedDisplacement']==0
        assert len(s['ranks'])==5
    for key in ['THU_02','THU_04','THU_05']:
        s=LOOKUP[key]
        assert all(a['connectionRadiusMetres']<b['connectionRadiusMetres'] and a['targetLimit']<b['targetLimit'] for a,b in zip(s['ranks'],s['ranks'][1:]))
    assert [r['targetLimit'] for r in LOOKUP['THU_02']['ranks']]==[2,3,4,6,8]
    assert [r['connectionRadiusMetres'] for r in LOOKUP['THU_02']['ranks']]==[3,4,5,6.5,8]
    assert [r['geometry']['radiusMetres'] for r in LOOKUP['BOW_02']['ranks']]==[3,4,5,6,7]
    assert [r['geometry']['childProjectileLimit'] for r in LOOKUP['BOW_02']['ranks']]==[1,2,3,4,5]
    assert [r['targetLimit'] for r in LOOKUP['BOW_02']['ranks']]==[2,3,4,5,6]
    assert all(r['geometry']['kind']=='impactSplitProjectiles' and r['geometry']['primaryProjectileCount']==1 for r in LOOKUP['BOW_02']['ranks'])
    assert all(LOOKUP['BOW_02'][k]==v for k,v in ORIGINAL_BOW02_TIMING.items())
    for style in ['WAR','BOW','FIR','THU']:
        damage=[s for s in SKILLS if s['style']==style and s.get('offensive')]
        assert len(damage)>=3
        assert all(s['ranks'][0]['castRangeMetres']>=9 for s in damage)
    assert len(CAT['equipmentEffects'])==74 and len(WORLD['levels'])==97 and len(WORLD['bosses'])==12
    for file,data in [('skill-catalog.json',CAT),('campaign-v8.json',WORLD)]:
        (OUT/file).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def docs():
    intro=('2026-11-08。按最新反馈修订：奥术职业暂时撤下，冰系继续退出；当前只保留战技、弓术、火焰、雷霆四系。战技沿首版细长单层银白月牙，分裂箭沿首版首击后限额子箭，火雷保留现有真实范围与限额规则。四系加强材质、方向短尾、抵达目标的接触层次和快速退亮，自保/治疗仍保持自身锚点。**本轮设计待用户审阅，尚未验收、尚未接入运行版。** '
           '当前30技能、150条进阶记录，保留角色门槛与人物1—40级属性数值。14个历史技能ID中奥术7个标记暂退役，冰系7个继续退役，既有历史图片与目录文件保留。\n\n')
    main='# 四系远距技能重设计 v2\n\n'+intro
    main+=('战技是远距细长单层飞刃与金属斩裂接触；弓术区分直线箭与首击后限额子箭的穿刺节拍；火是厚实体积火核、红橙翻卷与短余爆；雷是认可的横向电弧、固定限额与分层触点爆闪。保留技能的判定、S/CD、门槛与数量不变。\n\n'
           '- [人物升级与角色等级门槛](character-progression-v1.md)\n- [固定电弧、分裂箭、范围规则](skill-spatial-v2.md)\n'
           '- [差异化与远距方向](skill-differentiation-brief-v2.md)\n- [逐级特效](skill-vfx-v2.md)\n'
           '- [概念图与审核记录](../../source-art/skills/pure-skills-v2/README.md)\n- [74装备联动](equipment-skills-v4.md)\n'
           '- [镜头、瞄准、远程反应的接入门槛](ranged-combat-integration-v2.md)\n- [原作参考与原创转化](skill-reference-bg3-v2.md)\n'
           '- [补充候选变式](skill-original-extensions-v2.md)\n\n')
    main+=table(['流派','空间身份','命中节奏'],[(v['name'],v['shape'],v['timing']) for k,v in STYLES.items() if k!='COM'])+'\n\n'
    main+=('普通攻击仍按武器；技能**不自动跑近目标**。战技三个主输出为9—14m飞行/落刃，终极18m走廊；法术主要12—18m选点，'
           '雷矛最长20m。施法距离与作用半径分开，不把“18m选点＋4.5m半径”说成18m半径。防护、附魔和自身闪跃是明确自保例外，'
           '每系主输出无需先贴身。四主动+一终极+两被动，固定疾影步；普通技只用CD，终极100蓄能/45s共享锁。\n\n'
           '## 电弧的五级硬规则\n\n')
    main+=table(['技能级','角色门槛','施法距离','连接半径','总目标上限（含首目标）'],[(r['rank'],r['requiredCharacterLevel'],str(r['castRangeMetres'])+'m',str(r['connectionRadiusMetres'])+'m',r['targetLimit']) for r in LOOKUP['THU_02']['ranks']])+'\n\n'
    main+=('中心在首次有效命中时固定，所有额外敌人必须在此半径内。额外目标各70%伤害，同敌一次，不回跳，空位不补成单体连打；'
           '分叉不能越连越远。雷系终极也明确用4→12目标、4→9m半径成长，不靠无限细电丝冒充范围。\n\n## 30技能与150条进阶记录\n\n')
    for style,meta in STYLES.items():
        main+='### '+meta['name']+'\n\n'
        for s in [x for x in SKILLS if x['style']==style and x['type']!='passive']:
            main+='#### '+s['id']+' '+s['name']+'\n\n'+s['targetShape']+'。'+s['mechanic']+'\n\n'
            if s.get('counterplay'):main+='反制与反馈：'+s['counterplay']+'\n\n'
            main+=table(['技能级 / 角色级','施法距离','真实命中形状 / 数量','单敌直接上限 / 段数 / CD'],[(f"{r['rank']} / Lv{r['requiredCharacterLevel']}",str(r['castRangeMetres'])+'m',geometry_text(r['geometry'])+'；'+('全部合法目标' if r['targetLimit'] is None else '上限'+str(r['targetLimit'])),f"{r['maxDamagePerTargetS']}S / {r['authoredDamageHits']} / {r['cooldownSeconds']}s") for r in s['ranks']])+'\n\n'
        for s in [x for x in SKILLS if x['style']==style and x['type']=='passive']:
            main+='**'+s['id']+' '+s['name']+'：**'+s['effect']+' 角色门槛：'+'/'.join(str(r['requiredCharacterLevel']) for r in s['ranks'])+'。\n\n'
    main+=('S、力量/敏捷/智识/体魄、伤害/控制/次级事件/冷却/保存规则沿用人物稿与v1未冲突处；本页的新形状和距离优先。'
           '同一技能原生连穿接触/电弧/波段是声明的直接段，不受“最多2项装备次级触发”删减；装备触发仍不能递归。'
           '当前没有复制技能或退役职业解锁；旧符迁移只指向现有技能并校验其原角色门槛，历史ID不参加施法。\n')
    (DOC/'combat-skills-v2.md').write_text(main,encoding='utf-8')

    spatial='# 远距选点、首击分裂箭与固定电弧 v2\n\n'+intro
    spatial+=('## 距离是三件事\n\n'
              '1. `castRangeMetres`：角色到选点/首目标的合法距离。\n'
              '2. `geometry`：从角色、选点或首命中中心展开的命中形状；半径、长度、宽度、分支数量分别保存。\n'
              '3. 镜头/瞄准视野：需要同时看见角色和远端目标。现有代码的4.5m常量不能继续用于技能。\n\n'
              '点选形状的最大外缘可能是“施法距离+半径/条带长度”，不能只测中心是否可见。所有世界检测同层、可达、有遮挡约束；'
              '相邻投影不代表穿墙合法。预瞄显示真实并集和空隙，装饰火焰/晶体/电叉不扩判定。\n\n'
              '## 连锁雷弧：固定半径、固定数量\n\n')
    spatial+=table(['级','角色级','首目标施法距','固定半径','总目标','额外最多'],[(r['rank'],r['requiredCharacterLevel'],r['castRangeMetres'],r['connectionRadiusMetres'],r['targetLimit'],r['targetLimit']-1) for r in LOOKUP['THU_02']['ranks']])+'\n\n'
    spatial+=('首次命中敌人后冻结中心坐标，先筛半径，再筛存活敌对、同场同层、无遮挡合法连边。排序固定为距中心、稳定实体ID，'
              '取剩余名额；首目标已占一名。几条边连到同一敌人也只给该目标一次技能伤害。中心不随敌人移动，主目标被击败也不换中心。'
              '候选列表只建一次；半径外敌人不因靠近某个已连接敌而被继续招募；多段终极也不在后拍补人。'
              '每次声明脉冲判伤前都重验存活敌对、同场同层、冻结几何与合法无遮挡连接；已选目标走出范围或被遮挡则本拍跳过，死亡者退出，空位不补。'
              '目标选择集合全cast去重，伤害以castId+targetId+pulseIndex去重；单拍不重复，声明的第二/三拍仍可命中同一已选敌人。主目标未被有效命中就不产生分叉，射线先遇墙不得绕墙取敌。\n\n'
              '**例：**1级首目标A，3m内有B/C/D，只取距离最近1人，实际共2人；即使B附近还有E，E不加入。'
              '5级半径8m、总8人：只在A的8m圈内取最多7名额外敌人。若圈内只有2名，就实际打3名，不将其余5份伤害灌回A。\n\n'
              '## 首击分裂箭与电弧连接分开\n\n'
              '分裂箭恢复最初combat-bow.png的结构：先发1支主箭，12/13.5/15/16.5/18m内首次有效命中后主箭结束，从该命中点才生成最多1/2/3/4/5支独立子箭。'
              '首击时固定中心、3/4/5/6/7m半径和目标名单，按中心距/稳定ID选不同敌人，主目标占1名，合计最多2/3/4/5/6敌。子箭出生时冻结目标初始点及分开的平滑弹道弧线；薄绿白尾迹保持最初观感，不加羽翼绸带。'
              '每支子箭只对自己的分配目标判伤，同cast同敌一次、最多一层子代；无递归、途中追踪、重定向、补位或伤害转移。目标移动离开冻结路径可躲，墙拦截路径，首击未生效不生成子箭。'
              '恢复v1原前摇/释放承诺0.4s、后摇0.25s；保留原S/CD/角色门槛、75/75/80/85/90%后续倍率与削韧值。\n\n'
              '穿云箭是更快出手的窄直线贯穿；L02取消回程，保守改为第二及以后目标穿透伤害下限60%→70%，无回射、方向改变或额外弹体。'
              '疾风连射是同向多箭；万箭齐发释放时冻结各初始瞄点和直线方向，三拍各沿原直线射出，目标移动可躲开，不追踪或补打。'
              '雷弧是接点连接；分裂箭是真实子箭各自飞行。穿云箭/疾风连射/万箭齐发保持原直线、短中性风迹；分裂箭用薄绿白分开尾迹和小穿刺闪，均不按装饰增加伤害。原生分裂子箭与贯穿接触不占装备次级预算。\n\n'
              '## 火系范围必须实际打满\n\n'
              '焚星坠落选点12→18m、半径2.8→4.5m；1—2级主爆，3—5级主爆75%＋0.30s后25%次爆。'
              '主爆从中心到外缘同一倍率，没有只烧边框的空心命中环；第6、第8个合法区域目标不能被旧maxTargets=5静默丢掉。'
              '墙体挡住的子区域不判伤，目标可走离次爆；火核下坠和短压缩属于前摇表现，落点接触后的主爆0.20s内完成，不追加一份下坠伤害。'
              '球状火体翻卷后只短留余烬/焦痕，地面圆盘是实际判伤的投影，不画重复枝纹铺毯。炎墙封路保留4→9m线段持续场；焚天火海保留7→12m宽矩形，表现为一道厚重横向火焰锋面与四拍余焰。\n\n'
              '## 命中实例与等级\n\n'
              'castId+目标ID+声明段序号去重；每cast技能蓄能只按一次直接成功，不按贯穿接触/电边/装饰数量发能量。'
              '释放瞬间固定技能等级与几何快照，途中升级不改变已飞出载荷；角色等级不达门槛则接收/释放两次校验都拒绝越级。'
              '分裂子箭/雷网/次爆不能通过退出、换槽或重载重新生成；存档不重播瞬时命中。退役14个技能仅作历史，不进入装备触发或旧符解锁；所有当前旧符映射都指向四系现存技能。\n')
    (DOC/'skill-spatial-v2.md').write_text(spatial,encoding='utf-8')

    vfx='# 四种不同打法的技能表现 v2\n\n'+intro
    vfx+=('四系主剪影分别是首版细长单层银白月牙、首击后分开的细淡绿白子箭、厚实火核/红橙翻卷爆燃、认可的横向限额电弧。'
          '战技加强金属斩裂与方向短尾而不堆厚刃；子箭强化真实穿刺节拍而不长羽翼光带；火加强白金瞬核/红橙翻卷/短接触余爆；雷只加强已有触点分层爆闪。'
          '本轮方向待审，现有概念图与历史材质需逐张重新核对，不能视为已通过美术验收。\n\n')
    vfx+=table(['系别','形状','节拍','颜色只作辅助'],[(v['name'],v['shape'],v['timing'],v['color']) for k,v in STYLES.items() if k!='COM'])+'\n\n'
    vfx+='## 逐级材质与接触分层\n\n'+table(['技能级','表现方向'],[(i+1,direction) for i,direction in enumerate(VFX_GROWTH)])+'\n\n'
    vfx+=('所有150阶记录有独立vfxLayers：材质、方向短尾、同一次真实接触的层次和快速退亮分别说明。'
          '自保/治疗/位移仍在自身与原声明事件锚点，不能借表现升级变成远处进攻；被动只响应原触发事件。\n\n')
    for style,meta in STYLES.items():
        vfx+='## '+meta['name']+'\n\n'
        vfx+=meta['spectacle']+'\n\n'
        vfx+=table(['技能','特效锚点与弹体表现'],[(s['name'],s['ranks'][0]['vfxDirection']) for s in SKILLS if s['style']==style and s['type']!='passive'])+'\n\n'
        vfx+=table(['技能','1级','2级','3级','4级','5级'],[(s['name'],*[r['evolution'] for r in s['ranks']]) for s in SKILLS if s['style']==style and s['type']!='passive'])+'\n\n'
        for s in [x for x in SKILLS if x['style']==style and x['type']=='passive']:
            vfx+='**'+s['name']+'：**'+s['visual']+'\n\n'
    vfx+=('## 新图与实现的验收\n\n'
          '施法者在画面左前，目标群在右后，二者之间有明显空地；图中至少同时存在命中者与范围外未命中者。'
          '米制值以数据为准，静态构图不假装实测距离。剑气要跨空地飞到敌阵；分裂箭先显示1支主箭首击，再从命中点出现声明数量的独立子箭，不画单箭依次绕行或提前分支；'
          '子箭薄绿白尾迹沿冻结平滑弹道分开，其余直线箭保留短中性风迹；雷只在各实际接点分层短闪；火核先下坠再厚实翻卷爆燃。'
          '四系概念转灰缩图后仍可辨认主形状，不能只靠四种颜色区分。\n\n'
          '每个接触点有独立短音/局部闪光，远处也能看出谁被击中。低位残留快速退透明，敌方预警绘制层置顶；'
          '1—5级成长沿原分裂名额/半径、直线穿透、范围和声明段数，材质/方向/接触层次逐级清楚；装饰数量不变成额外伤害。'
          '降档先去远处装饰碎片，不删合法接触/目标/波段，也不把高阶压成低阶主形状。\n\n'
          '图像、来源、真实尺寸、提示词与独立概念审阅在[新素材目录](../../source-art/skills/pure-skills-v2/README.md)。'
          '当前30×5级生产资产、动画、透明边缘、镜头内遮挡和手机帧率仍未制作验收；冰系与暂退奥术的旧图仅保留历史，不代表当前可选职业。\n')
    (DOC/'skill-vfx-v2.md').write_text(vfx,encoding='utf-8')

    equip='# 远距技能的74件装备联动 v4\n\n'+intro
    equip+=('物品ID、数量、来源和经济沿用当前74永久目录；本轮把退役职业联动适配到猎王印、火雷直接命中或原破阵事件，分裂箭/限额电弧不变。'
            '没有新增战斗消耗品或等级绕过。\n\n')
    equip+=table(['物品','当前效果','来源'],[(i['id']+' '+i['name'],i['effect'],i.get('source','当地池' if i.get('weight') else '对应可选首领固定奖')) for i in WORLD['legacyEquipment']+WORLD['retainedLegendaries']+WORLD['newEquipment']])+'\n\n'
    equip+=('原生分裂子箭、直线贯穿、电网不计为装备次级触发；但它们仍共享每cast目标去重与蓄能。'
            '装备附伤每cast最多2项，不能再次生成完整技能；L02只抬穿云箭后续伤害下限，不回射；DE08只修正非终极火雷对自己猎王印目标的首次直接命中，不产生新技能。'
            'W06只响应直接主动命中自己的hunterMark，标记不消费或刷新。余烬掌握/J01实际延长燃烧施加时长，'
            '同类取最大，最终4s，不再只抬一个不会生效的上限。\n\n'
            '旧T类型只作为永久技能迁移审计；T08外观映射更新为万钧雷潮·终誓。所有角色等级门槛保留，外观不提前启用5级范围或连接人数。\n')
    equip+='\n## 退役职业与旧联动适配记录\n\n'+table(['ID','适配原因'],[(x['id'],x['reason']) for x in CAT['compatibilityAdaptations']])+'\n\nA04/J06/DU2-01的寒冷防护用于敌人与环境，保留原值；不解锁玩家冰职业。奥术暂退，旧技能和图片仅保留历史。\n'
    (DOC/'equipment-skills-v4.md').write_text(equip,encoding='utf-8')

    world='# 远距技能的97地点战斗适配 v4\n\n'+intro
    world+=('地理节点、端口方向、敌人固定等级和旧奖励不因技能射程自动改写；本页列远距布局复核要求，不冒称原场景已扩大。'
            '旧12×10/14×12m决战场不足以展示18m远距交战，需要后续实景扩展/重排并验收合法射线、掩体和退路。\n\n')
    for region in WORLD['regions']:
        world+='## '+region['id']+' '+region['name']+'\n\n'
        world+=table(['节点','等级 / 敌阵','目标与奖励','远距适配'],[(n['id']+' '+n['name'],str(n['recommendedLevel'])+'；'+n['encounter'],n['objective']+'；'+n['reward'],n.get('rangedLayoutReview','安全/剧情点不添加战斗')+'；'+n['route']) for n in WORLD['levels'] if n['region']==region['id']])+'\n\n'
    world+='## 12场首领\n\n'+table(['首领 / 级 / HP','布局候选','远距应对'],[(b['name']+f" / Lv{b['level']} / {b['hp']}",str(b['recommendedArenaClearMetres'])+'m有效战斗空间候选',b['rangedResponse']) for b in WORLD['bosses']])+'\n\n'
    world+=('受远程命中的敌人即按事件察觉，沿可达路径接近或进入明示远程反击；不因旧7m自然察觉就站着挨18m技能。'
            '不得瞬移贴脸、突然无敌或强迫玩家近战；远程敌建议14—18m回击但先给可见方向/瞄准，屏外不得瞬发。'
            '战斗远距、室内遮挡、Boss接近速度与镜头必须一起试玩，不能用数据射程代替可玩验证。\n')
    (DOC/'world-combat-v4.md').write_text(world,encoding='utf-8')

def integration_doc():
    text='''# 远距技能的镜头与瞄准接入门槛 v2

2026-11-08。此页是**尚未实现的接入要求**，用于避免“射程写18m，实际仍只能打脚边”。技能数据和概念图已重设计，不能据此宣称运行版已变远程。

## 已核实当前源码

- [ChapterGame.ts](../../src/cocos/assets/scripts/app/ChapterGame.ts) 的 `previewTarget()` 把距离固定夹在1.2—4.5m；默认无手动目标时取人物前方3m。它是旧投掷预览逻辑，不能直接承担新技能。
- 同文件 `configureLighting()` 手机镜头固定 `orthoHeight=3`，桌面约4.3/4.4；滚轮范围2.9—6.2。`positionCamera()`仍跟随人物，没有读取远程技能和敌群包围盒。
- 当前四系纯技能30项、150条进阶记录尚未注册到运行版；冰系及暂退奥术的14个历史技能不注册或列入解锁选项。因此本轮不把这些常量局部改大就冒充完整接入，也不让旧道具因此获得18m射程。

## 后续接入需要一起做到

1. 每次瞄准读取选中技能及冻结等级的 `castRangeMetres`、`targetingMode`、`geometry`。角色位置、目标位置、真实形状和遮挡结果分别保存，拒绝共用4.5m常量。
2. 远距战斗初始镜头候选正交半高6.8—7.5m，长射程瞄准可平滑拉远到8.5—10.5m；以角色+目标形状包围盒与安全边适配，不能只看中心点。数值为候选，不是已测视野。
3. 镜头可沿瞄准方向前移，优先同时容纳本人、远处目标和形状外缘；人物仍按原世界尺度，844×390下建议人物可见高度至少32px，不通过改人物比例造假。若超过预算，应调整战场布局/瞄准构图，而非静默缩成近身技能。
4. 拖拽瞄准将目标锚定在世界坐标，镜头移动不反过来重算出另一个目标；目标只响应手指相对拖拽或新指令，避免镜头与准星追逐振荡。预瞄稳定后才接受松手释放，取消/失焦不发射。
5. 技能目标超距时只显示超距与可达边界，不自动跑近。手机左右手移动/瞄准同时存在，HUD位置不随镜头改变。敌方预警和目标轮廓持续可读。
6. 低墙/门/不同层阻挡按世界检测执行。不能凭镜头看见隔壁房间就穿墙施法；室内仍允许技能有远程定义，但合法射线可被建筑截断。
7. 敌人受到远程技能立即按合法世界事件察觉；远程单位能在对应距离有明示回击，近战沿导航接近，不瞬移、不为否定远程而突然全免伤。
8. 12场首领的清晰射线、侧路和有效空间一起复查。建议主线36×26m、可选30×24m战斗空间作为起点；这些是布局候选，现有地图/碰撞没有在本轮扩大。

## 需要看到的运行证据

同一角色等级分别用断空剑气、分裂箭、焚星坠落、连锁雷弧，证明角色站位不靠近也能命中远方；记录选点距、形状边界、每敌命中、被墙截断、取消、切后台、旧档和手机镜头。电弧检查圈外敌不被递归招募、每拍复核固定范围/同层/无遮挡、上限内不足不补打；分裂箭检查先1支主箭、首击后才出现1—5支独立子箭，固定首击半径/不同目标/冻结平滑弹道，子箭无追踪、递归或补位，遇墙先关伤害；万箭齐发检查移动出冻结直线可躲开；L02检查无回程/额外弹体；火检查内部第6—8敌仍命中；四系升级表现检查仅增加材质/方向短尾/真实接触层次，判伤次数不变。旧档读取退役FRO或ARC ID仅作历史，不产生失效施法或越级解锁；旧符当前迁移只指向现存四系。

复用既有Cocos 3.8.8相机、SpriteFrame、Line、ParticleSystem与Effects对象池，先接正确几何和事件，再接炫酷表现。当前没有新增引擎、依赖或测试脚手架，也没有发布/重建游戏。
'''
    (DOC/'ranged-combat-integration-v2.md').write_text(text,encoding='utf-8')

def main():
    export();docs();integration_doc()
    report=dict(skillCount=30,rankRecords=150,mainStyleCount=4,levelGatesPreserved=True,equipmentCount=74,nodeCount=97,bossCount=12,
                lightningRadius=[3,4,5,6.5,8],lightningTotalTargets=[2,3,4,6,8],primaryIncluded=True,
                noCircleRecruitment=True,fireHiddenTargetCapRemoved=True,arrowPrimaryProjectileCount=1,
                arrowChildProjectileLimits=[1,2,3,4,5],arrowSplitRadiusMetres=[3,4,5,6,7],distinctChildProjectileIds=True,
                firstImpactSplitOnly=True,childPath='fixedBallisticPath',noMidflightRetarget=True,recursiveArrowSplit=False,
                retiredSkillIds=RETIRED_SKILL_IDS,temporarilyRetiredSkillIds=TEMPORARILY_RETIRED_SKILL_IDS,
                iceStyleSelectable=False,arcStyleSelectable=False,straightBowSkillIds=['BOW_01','BOW_03','BOW_05'],
                bow02WindupSeconds=ORIGINAL_BOW02_TIMING['windupSeconds'],bow02TargetLimits=[2,3,4,5,6],
                L02ReturnFlight=False,conceptReviewStatus='pending-user-review',
                styleSilhouettes=[STYLES[k]['silhouette'] for k in ['WAR','BOW','FIR','THU']],
                currentRuntimeAimClampMetres=4.5,runtimeImplemented=False)
    (OUT/'design-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__':main()
