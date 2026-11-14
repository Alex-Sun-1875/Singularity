"""Author the pure-skill design, five-rank effects and level/attribute progression.

Design exports only. Reuses the existing campaign catalog and Python stdlib;
does not alter Cocos gameplay, install dependencies or generate bitmap artwork.
"""
from pathlib import Path
import json
import math
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'source-art/skills/pure-skills-v1'
DOC=ROOT/'docs/design'
OUT.mkdir(parents=True,exist_ok=True)

STYLES={
 'WAR':dict(name='破军战技',color='象牙金、冷银、赤金锋线',shape='刀弧→交叉刃光→立体剑阵',feel='重斩、裂地、护体、近身爆发'),
 'BOW':dict(name='逐风弓术',color='翠青、银白、星金箭芯',shape='细箭→分流箭翼→贯天星矢',feel='穿透、箭雨、连射、弱点爆发'),
 'FIR':dict(name='烈焰秘术',color='炽橙、深红、白金火核',shape='火芯→多层爆环→凤凰/陨星冠',feel='灼烧、陨星、护盾、范围爆裂'),
 'FRO':dict(name='寒霜秘术',color='冰蓝、冷白、紫蓝折光',shape='冰棱→六角晶阵→冰冠领域',feel='减速、冻结、冰甲、碎晶爆发'),
 'THU':dict(name='雷霆秘术',color='电蓝、紫白、金白核心',shape='单束电弧→分叉雷网→纵向雷狱',feel='高速命中、连锁、附雷、连续爆点'),
 'ARC':dict(name='星界秘术',color='紫晶、深靛、银白星轨',shape='光点→刻线环→透明星门/星核',feel='奥印、复制、闪跃、贯穿光束'),
 'COM':dict(name='通用技能',color='青白步光、柔金复苏',shape='残影步迹 / 合拢的生命光瓣',feel='闪避和恢复，也以技能释放'),
}

GATE_LABELS={1:'各系第1主动',2:'各系第2主动',3:'各系第3主动',4:'各系第4主动',5:'终极技能','p1':'第1被动','p2':'第2被动'}
ATTRIBUTE_LABELS=dict(strength='力量',dexterity='敏捷',intellect='智识',vitality='体魄')
GATES={
 1:[1,8,16,24,32], 2:[4,8,16,24,32], 3:[8,12,18,26,34],
 4:[12,16,22,30,36], 5:[16,20,26,32,38],
 'p1':[6,12,20,28,36], 'p2':[14,18,24,32,40],
}

SKILLS=[]
def active(key,name,weapon,shape,cd,windup,reach,radius,power,hits,break_power,evolution,mechanic='',shield=None,heal=None,targets=5):
    branch=key.split('_')[0]
    index=int(key.split('_')[1]) if branch!='COM' else 0
    ultimate=index==5
    gates=GATES[index] if branch!='COM' else ([1,8,16,24,32] if key=='COM_01' else [2,8,16,24,32])
    if isinstance(hits,int): hits=[hits]*5
    assert len(evolution)==len(power)==len(hits)==5
    levels=[]
    for i in range(5):
        r=round(radius*[1,1.05,1.12,1.20,1.30][i],2)
        reach_at_rank=round(reach*[1,1,1.06,1.10,1.15][i],2)
        # Authored growth is distinct from equipment cooldown reduction.
        cooldown=cd if ultimate or key=='COM_01' else round(cd*[1,1,0.96,0.92,0.88][i],2)
        levels.append(dict(rank=i+1,requiredCharacterLevel=gates[i],maxDamagePerTargetS=power[i],
                           authoredDamageHits=hits[i],radiusMetres=r,rangeMetres=reach_at_rank,cooldownSeconds=cooldown,
                           breakPower=round(break_power*[1,1.05,1.1,1.15,1.2][i],1),
                           shieldMaxHpPercent=shield[i] if shield else 0,healMaxHpPercent=heal[i] if heal else 0,
                           evolution=evolution[i],visualTier=i+1))
    SKILLS.append(dict(id=key,name=name,style=branch,type='ultimate' if ultimate else ('mobility' if key=='COM_01' else 'active'),
                       compatibleWeapons=weapon,targetShape=shape,windupSeconds=windup,
                       releaseCommitSeconds=windup,recoverySeconds=0.25 if not ultimate else 0.45,
                       resourceCost=0,consumableCost=0,enemyForcedDisplacement=0,maxTargets=targets,
                       ultimateCost=100 if ultimate else 0,sharedUltimateLockSeconds=45 if ultimate else 0,
                       mechanic=mechanic,ranks=levels))

active('WAR_01','断空斩','melee','前方扇形刀弧，角度随级成长',5,.18,2.4,0,[1.7,1.9,2.2,2.5,2.9],[2,2,3,3,3],15,[
 '双段短银弧，起手斩与回斩各一次。','弧刃加宽，第二刀形成清晰交叉金线。','增加第三刀终结，三击总倍率按本级上限结算。','第三刀出现半环剑印，刃缘碎光向外展开。','三刃汇成金白扇形剑阵，终结爆环；三次伤害，不按幻剑数量加伤。'],
 '破阵；可打断普通敌明示前摇并开盾2s，目标5s内不能再次被开盾；Boss只削韧，不位移。')
active('WAR_02','破军突袭','melee','自身沿地面突进后十字斩',8,.16,3.5,.8,[1.6,1.85,2.2,2.55,3.0],[1,1,2,2,2],10,[
 '前冲一道直线残光，落点一斩。','突袭尾迹分出两道金属刃线。','落点增加反向回斩，共两次伤害。','残影形成穿阵十字，落点光印扩张。','金白长锋贯穿路径，十字终结爆裂；残影不产生第三次伤害。'],
 '只移动施法者，不带动敌人；路径遇墙、未开门、坑边提前停止，无隐含无敌。')
active('WAR_03','铁誓壁垒','any','自身护盾',14,.20,0,0,[0,0,0,0,0],0,0,[
 '单层半透明盾纹，持续4s。','盾纹长出肩侧护片。','正面形成三片交错光盾，吸收值提高。','光盾闭合为留有视野的护体甲环。','王卫般的金白盾翼展开，破碎时只有视觉爆环，不反伤不强制移动。'],
 '护盾18/20/22/25/28%最大生命，持续4s；同源刷新不叠加。允许正常攻击，属于主动技能，不占用武器技隐藏键。',shield=[18,20,22,25,28],targets=1)
active('WAR_04','裂地审判','melee','指定地面圆形落刃',10,.55,4,2.0,[2.2,2.5,2.9,3.4,4.0],[1,1,2,2,2],25,[
 '武器落地，单圈短促裂光。','裂光分为四条放射纹。','追加一次延迟裂纹伤害，总倍率由本级统一拆分。','地面展开六角重刃纹，中心与外缘分层爆开。','巨刃光影落下，两次冲击形成辉金审判阵；装饰碎石不阻路。'],
 '破阵；两次伤害时主击占70%、余震30%，间隔0.45s；敌人留在原位置，地面裂纹不改变碰撞。')
active('WAR_05','破晓裁决','melee','前方大扇形三段终结',45,.65,3.5,0,[5,5.6,6.3,7.1,8],[3,3,3,3,3],40,[
 '两道银色开路斩，第三刀金色终结。','开路斩留实体感刃痕，终结有薄金环。','背后浮现三柄透明光剑，随三段斩击同拍落下。','剑翼向两侧展开，末击刻出完整旭日纹。','破晓剑冠显形，三段巨刃贯穿金白光阵；末击爆环与低频轰鸣，幻剑只作表演。'],
 '伤害比例20%/20%/60%，三击各有命中窗；释放后不无敌，不跳过Boss阶段。')

active('BOW_01','穿云箭','bow','直线贯穿箭',5,.25,10,.45,[1.6,1.8,2,2.3,2.8],1,15,[
 '一支青白长尾箭，最多穿3敌。','箭芯收紧、尾迹成双翼，穿透上限4敌。','分出两道侧翼光箭；同一目标只取最强一支，不能贴脸三倍。','三支箭各有螺旋风尾，主箭末端短促裂星。','星金主箭带六片羽刃，命中形成穿云爆点；同敌仍一次主命中。'],
 '破阵；箭支间同目标去重；贯穿后衰减20%，最低60%；墙体截断。')
active('BOW_02','星雨齐射','bow','指定圆形箭雨',9,.40,9,2.4,[1.65,1.95,2.3,2.65,3.1],[3,3,4,4,5],6,[
 '三波细箭落地，地面有稀疏风纹。','箭雨更密，三个落点节奏分明。','增加为四波，地面形成星形准心。','银青箭流交叉，外缘风带卷出明确边界。','五波星矢瀑落，最后一波形成星冠爆光；光箭数量不额外增伤。'],
 '各波平均分摊总倍率，波间0.35s；最多同时命中8敌，范围内不牵引。',targets=8)
active('BOW_03','疾风连射','bow','朝向短连射',7,.18,9,.35,[1.95,2.2,2.55,2.9,3.35],[3,3,4,4,5],8,[
 '三箭连发，白色箭尾逐根可见。','三箭带青色节拍环。','增为四箭，箭尾呈细小螺旋。','四箭之间出现收拢风翼，最后一箭更亮。','五箭形成一条银青穿梭光带，末箭有鹰翼爆点。'],
 '弹间0.10s，各箭平分本级总倍率；后续箭受墙阻挡，可以落空，不自动追踪到背后。')
active('BOW_04','猎王印','bow','指向单体印记',12,.22,10,0,[.4,.5,.6,.75,.9],1,0,[
 '目标脚下出现开口菱形准星，持续8s。','准星多一层鹰羽线。','附加一次0.4s弱点闪光提示；下一弓术命中弱点反馈更强。','菱形变四翼猎印，目标轮廓短暂描边。','星冠猎印锁定弱点，首次后续直接命中产生醒目破星闪光，非额外伤害。'],
 '8s内自己对目标的直接技能增伤8/9/10/11/12%，纳入40%增伤总上限；同类印记只取最强。',targets=1)
active('BOW_05','天穹贯星箭','bow','巨型贯穿直线',45,.75,12,.9,[4.6,5.2,5.9,6.7,7.6],1,35,[
 '拉满弓后放出一支巨大青白星箭。','星箭有双层羽翼尾流。','箭芯化为贯穿光梭，命中爆出六角星纹。','弓后展开透明天弓，星箭穿过三道同心光环。','完整天弓冠架和星矢一同释放，整条路径分层爆星，伤害每敌只结一次。'],
 '最多穿6敌；目标每次施放仅一次主命中，不根据大箭停留帧数多次判伤。',targets=6)

active('FIR_01','赤焰枪','any','直线火枪弹',5,.25,8,.5,[1.5,1.75,2.05,2.4,2.8],1,8,[
 '掌心聚成单颗白芯焰枪，短火尾。','焰枪外侧包一层橙红旋流。','枪头呈三瓣火冠，命中碎成短促火花。','双层焰翼夹住白芯，命中有清晰环爆。','凤凰喙形枪芒拖出羽焰，命中形成三层不同速度的爆环。'],
 '命中附3s燃烧，每秒0.15S；等级只提高直接伤害，燃烧受统一持续规则约束。')
active('FIR_02','焚星坠落','any','指定圆形陨星',9,.55,8,2.4,[2.1,2.45,2.85,3.45,4.2],[1,1,2,2,2],20,[
 '一颗小型赤星砸落，形成一次圆爆。','陨星多一道旋转火环，落点有四条火纹。','主陨星后0.45s追加次爆，总倍率按75%/25%分配。','陨星包裹碎晶火冠，落地两层冲击环错时展开。','凤凰陨星从高处压落，白金爆核、赤橙火冠、六瓣冲击环依次爆开；仅两次判伤。'],
 '破阵；地面预示0.55s；召来的陨星是法术，不是可拾取/可摆放物体；不改变地形碰撞。')
active('FIR_03','焰心护盾','any','自身火焰护盾及终止爆光',14,.22,0,0,[0,0,0,0,0],0,0,[
 '火芯绕身一周，薄焰盾持续4s。','两条焰带交错旋转。','肩后展开短火羽，盾面呈熔金裂纹。','三道火翼包成开放的凤凰躯壳。','完整凤凰护翼张开再收拢，结束时大片羽光碎散，只有视觉爆裂。'],
 '护盾15/18/21/24/27%最大生命；持续4s，无反伤，不借爆光偷偷判伤。',shield=[15,18,21,24,27],targets=1)
active('FIR_04','凤凰掠影','any','自身沿地面位移并留下法术焰迹',11,.18,3.5,.65,[.6,.8,1.05,1.3,1.6],[3,3,3,4,4],6,[
 '前掠一道火尾，尾迹持续3s。','尾迹出现左右两片短焰翼。','掠行形成凤凰肩影，末端一朵火花。','焰尾分出羽骨图案，路径边缘更清晰。','凤凰光影从身后掠过，沿路依次羽焰绽放；总伤害按本级次数分摊。'],
 '只移动自身，焰迹的首个伤害延迟0.3s；没有场景点燃和物品连爆；同一次焰迹不与自身重叠叠伤。')
active('FIR_05','天火降临','any','指定大圆形持续爆发',45,.65,9,3.2,[5,5.7,6.5,7.4,8.4],[5,5,5,5,5],35,[
 '天火柱落地，先爆发再有四次余焰脉冲。','火柱有两层旋转冠环。','火柱短暂显出凤凰翼，余焰呈六瓣花。','巨大凤凰火冠在空中合拢，五次脉冲层次清楚。','天火凤凰压向地面，白金爆核与赤色星环扩散，末拍凤凰升翼；五次伤害，不全屏白闪。'],
 '主爆占40%，后四拍各15%，间隔0.5s；敌人可离开落区，不吸附。',targets=8)

active('FRO_01','寒晶刺','any','直线冰晶',5,.23,8,.45,[1.4,1.65,1.95,2.3,2.7],1,8,[
 '一根窄冰刺，命中碎晶。','冰刺出现双棱折射边。','三棱冰冠包住主刺，留下短冷雾。','透明晶翼分出三道亮边。','冰冠长刺在命中点开出六角晶花，仍只一次直接伤害。'],
 '施加寒缓25%持续3s，精英半时长；Boss仅减移动速度10%，不延长其攻击时序。')
active('FRO_02','冰霜新星','any','自身向外展开的冰晶圆环',10,.30,0,2.8,[1.3,1.55,1.9,2.3,2.8],1,20,[
 '一圈薄冰片从脚下展开。','冰片形成清晰六角边。','两层错时晶环展开，判伤仍一次。','地面六芒晶阵完整展开，边缘冰刃竖起。','冰冠爆环沿地展开，透明晶塔瞬间开花后碎散；不是障碍物，不改变敌人位置。'],
 '破阵；普通敌冻结1s、精英0.5s，Boss改为削韧；共享8s重复控制保护，不随等级无限延长。')
active('FRO_03','霜甲结界','any','自身冰甲护盾',14,.22,0,0,[0,0,0,0,0],0,0,[
 '胸前冰甲纹，持续4s。','肩侧长出两片透明冰甲。','护盾化为六片错位晶甲。','背后有短冰冠，脚下浮出薄晶环。','冰王冠形护甲围身，破碎时大块透明晶片飞散，人物轮廓保留。'],
 '护盾18/21/24/27/30%最大生命；持续4s；护盾吸收不令敌方硬直或位移。',shield=[18,21,24,27,30],targets=1)
active('FRO_04','冰河之刃','any','前方地面连续冰刃',9,.38,7,1,[1.95,2.25,2.65,3.1,3.7],[3,3,4,4,5],15,[
 '三道冰刃沿直线依次出现。','冰刃增厚并有镜面高光。','增加第四道冰刃，线路边缘出现冰纹。','双侧晶翼夹住主刃，形成冰河通道。','五道冠刃向前绽放，末端晶冠爆开；总倍率按五击分配。'],
 '各击间隔0.15s，寒缓25%/3s；地面晶体不新增碰撞，不产生搬运或堵路玩法。')
active('FRO_05','永冬降临','any','指定大圆形冰晶领域',45,.65,9,3.4,[4.8,5.5,6.3,7.2,8.2],[4,4,4,4,4],40,[
 '冰阵落地，四次晶爆。','四拍冰阵各有不同方向的晶片。','中央冰冠升起，外圈六角纹完整。','天穹冰花在上方展开，四次折光晶爆分层落下。','巨型冰冠与六瓣冰轮同时绽开，末拍碎成满场星晶；边缘快速透明化，不盖敌方预警。'],
 '四击均分；首击普通敌冻结1.5s、精英0.75s，Boss不冻结；后续晶爆不反复延长控制。',targets=8)

active('THU_01','雷矛','any','直线电矛',5,.20,9,.4,[1.6,1.85,2.15,2.55,3.0],1,18,[
 '一束细电矛，命中有短促分叉。','电矛包住第二层金白电芯。','命中呈三叉闪星，分叉只作视觉。','四条细雷绕住主矛，末端裂成雷纹花。','龙脊形雷矛贯穿而出，命中爆出紫白雷冠，仍一次主命中。'],
 '破阵；不自动穿越墙体，不把每条电弧当独立伤害。')
active('THU_02','连锁雷击','any','单体起跳的可达连锁',8,.25,8,0,[2.6,3.0,3.5,4.1,4.8],[4,4,4,5,5],10,[
 '一道主雷跳向最多4个不同目标。','主雷更粗，接点有双闪星。','每个接点出现清晰电冠，连锁路线可辨。','上限增至5目标，雷网有高低两层电弧。','五点雷网化为雷龙骨架，所有接点同时爆星；同一目标不会被回跳。'],
 '首目标取本级直接伤害上限，后续每跳为首目标70%；空位伤害不补给已有目标，不回跳，每段检查遮挡。')
active('THU_03','雷霆战印','any','自身三次基础攻击附雷',12,.20,0,0,[.9,1.05,1.2,1.4,1.65],3,0,[
 '掌中一枚闪电印，6s内三次基础攻击各附一次雷伤。','武器上多一圈细雷纹。','三枚雷片绕腕，每触发一次熄灭一枚。','闪电印扩成胸前小雷冠，触发点有短电花。','雷冠与武器电翼联动，三次触发有渐强爆点，仍只三份附雷。'],
 '本级总倍率平均分配给三次基础攻击，附雷是次级事件，不再连锁或触发装备；不自动追加施放次数。',targets=1)
active('THU_04','闪雷穿行','any','自身位移路径电斩',10,.16,3.5,.8,[1.1,1.35,1.7,2.1,2.6],[1,1,2,2,2],10,[
 '沿地穿出一道电线，终点一次电斩。','电线变双轨，终点出现星闪。','终点增加第二次短雷，0.25s间隔。','移动残影由三片雷羽组成。','雷翼残影贯穿整条路径，终点两次雷冠爆开；不带动任何敌人。'],
 '只移动自身，遇阻提前停止；二段伤害各50%；没有额外无敌或墙后瞬移。')
active('THU_05','九霄雷狱','any','指定大圆形三拍落雷',45,.55,9,3.2,[5.1,5.8,6.6,7.5,8.6],3,40,[
 '三次落雷，每拍都有落点细纹。','雷柱有分叉外壳，接地点爆出短电环。','上方出现三角雷印，三拍依序落下。','雷印扩成九角冠，地面三层雷环交错。','天穹雷冠与三条巨雷贯地，接点爆出放射雷树；三拍伤害，各拍只一次。'],
 '三击平均分配，命中时点0.55/1.30/2.05s；雷网不定身不牵引，Boss可以移动离场。',targets=8)

active('ARC_01','奥术飞弹','any','朝向软追踪飞弹',5,.22,8,.35,[1.5,1.75,2.1,2.5,3.0],[3,3,4,4,5],6,[
 '三枚紫白飞弹，逐枚发出。','飞弹多一圈星轨，核心更清晰。','增至四枚，轨迹有细小折线星点。','四弹形成环绕发射阵。','五枚星核从完整小星门射出，命中化成星花；仍按五枚分摊总伤害。'],
 '发出后仅在原朝向±25°内轻微追踪可见目标，逐段检查遮挡；每弹平分本级总倍率。')
active('ARC_02','裂界印记','any','指向单体奥印',9,.22,8,0,[.4,.5,.65,.8,1.0],1,15,[
 '一个紫色三角奥印，持续6s。','三角外增加一圈碎星线。','奥印成为三层错位星框。','目标脚下展开小星门，触发时镜片式碎光。','奥印展开为完整透明星核，下一技能命中时星核内爆，保留目标轮廓。'],
 '破阵；下一次非终极直接技能命中清印，追加0.6/0.7/0.8/0.95/1.1S奥术次级伤害，不能自触发，不递归。',targets=1)
active('ARC_03','灵能回响','any','重现已记录伤害技能的形状',12,.30,8,0,[0,0,0,0,0],0,0,[
 '用紫色半透明轮廓重现上一个合法技能30%直接伤害。','回响有两层星线轮廓，系数34%。','完整短星门映出原技能，系数38%。','双重星框接力，系数43%。','镜门张开，星色技能从门内重演，系数48%；装饰分身不各自攻击。'],
 '只复制上一个非终极伤害技能的直接伤害模板，先将原模板总倍率截到2.4S，再乘本级30/34/38/43/48%；用当前朝向重新瞄准；不复制控制/护盾/治疗/位移/附魔/装备被动，不记录自己或次级事件。')
active('ARC_04','星门闪跃','any','自身直线闪跃',11,.12,4,0,[0,0,0,0,0],0,0,[
 '从小型紫环穿到前方可达点。','起点和终点各多一圈薄星轨。','两扇小星门有短暂相连光线。','星门展开六片透明折光翼。','完整星门与星尘残影同时绽开，终点金白星环快速散去。'],
 '自身移动，不穿实体墙/未开门/坑；0.12–0.26s只免直接伤害，持续区照常；无回溯生命或冷却。',targets=1)
active('ARC_05','星界崩解','any','朝向贯穿光束',45,.70,10,1.0,[5,5.7,6.5,7.4,8.5],5,35,[
 '窄星门放出五段紫白光束。','光束外出现双螺旋星线。','星门展开三层刻线环，光束有透明外壳。','大星门显现完整银轨，五拍星爆有节奏展开。','巨型星核门开启，紫白贯天光束夹着银色星轨喷发，末拍星环崩解；仍五次判伤。'],
 '五击均分，间隔0.3s；引导期间移动倍率0.45、转向≤45°/s；受重击打断后余下段停止，已释放不返还蓄能。',targets=8)

active('COM_01','疾影步','any','自身短距闪避',2.5,0,2.8,0,[0]*5,0,0,[
 '一步青白残影，距离2.8m。','两层细残影，距离2.8m。','残影有短星线，距离2.97m。','前后残影相接，距离3.08m。','银青翼影瞬间展开，距离3.22m；视觉升级不增加无敌时间。'],
 '固定独立闪避位；总动作0.34s，0.06–0.20s免直接近战/弹体，不免持续地面伤害。遇墙停，不移动敌人。',targets=1)
active('COM_02','灵泉复苏','any','自身分三拍治疗',24,.35,0,0,[0]*5,0,0,[
 '三瓣柔金生命光，3s总恢复24%最大生命。','光瓣合成小型生命环，恢复27%。','双层叶状光阵环绕，恢复30%。','生命环分出四片透明光翼，恢复33%。','金白复苏花完全绽放，三拍柔光灌注，恢复36%；不会全屏闪白。'],
 '治疗分三次等额，每秒一次；可移动施法，满生命不提交冷却；不超量转盾，不受伤害增幅/暴击影响。',heal=[24,27,30,33,36],targets=1)

# A chain hits distinct targets, not four/five times on one target.
for skill in SKILLS:
    if skill['id']=='THU_02':
        for rank,primary in zip(skill['ranks'],[1.6,1.85,2.2,2.65,3.2]):
            rank['chainTargetLimit']=rank['authoredDamageHits']
            rank['maxDamagePerTargetS']=primary
            rank['damagePerSecondaryTargetS']=round(primary*.7,4)
            rank['totalCastDamageBudgetS']=round(primary+rank['damagePerSecondaryTargetS']*(rank['chainTargetLimit']-1),4)
            rank['authoredDamageHits']=1
    if skill['id'] in ('WAR_01','WAR_05'):
        for rank,angle in zip(skill['ranks'],[110,120,130,140,150] if skill['id']=='WAR_01' else [120,130,140,150,160]):
            rank['arcDegrees']=angle
    if skill['id']=='ARC_03':
        for rank,coefficient in zip(skill['ranks'],[.30,.34,.38,.43,.48]):
            rank['copyCoefficient']=coefficient
            rank['copiedTemplateCapS']=2.4
    if skill['id']=='BOW_04':
        for rank,bonus in zip(skill['ranks'],[8,9,10,11,12]):
            rank['markedDirectSkillBonusPercent']=bonus
    if skill['id']=='ARC_02':
        for rank,bonus in zip(skill['ranks'],[.6,.7,.8,.95,1.1]):
            rank['conditionalSecondaryDamageS']=bonus

PASSIVE_ROWS='''
WAR_P1|战艺精通|战技直接伤害+4/5/6/7/8%，计入增伤总上限。|兵刃每次起手出现一圈短银纹，随等级增加为五段刻线，不遮刃缘。
WAR_P2|铁誓不屈|持有自身护盾时受到直接物理伤害-3/4/5/6/7%，计入减伤上限。|护盾受击时出现从一枚到五枚短盾纹，0.15s后消退。
BOW_P1|鹰眼|距离超过5m的弓术直接伤害+4/5/6/7/8%。|瞄准时从一圈细点到五片短羽准星，不增加实际判定。
BOW_P2|逐风猎手|弓术命中后移动速度+3/4/5/6/7%，2s，CD5s；不增加闪避无敌窗。|脚踝从单风线逐步成长为小型四翼风纹，离开加速即消失。
FIR_P1|余烬掌握|自身燃烧最长持续3/3.25/3.5/3.75/4s，同源刷新不叠伤。|燃烧轮廓从火星到羽焰，不给目标铺不透明火团。
FIR_P2|薪火余辉|被自身直接火技能击败的真实敌人，向附近最多2敌施0.06/0.07/0.08/0.09/0.10S每秒燃烧3s，CD6s；不递归传播、不产生蓄能。|死亡爆点从三火星到一朵六瓣小火花，传火路径只短亮一次。
FRO_P1|寒锋|对寒缓目标的直接技能伤害+4/5/6/7/8%，计入增伤上限。|命中寒缓敌时出现从一道到五道细冰裂线，0.2s淡出。
FRO_P2|凝霜守护|自身冰系护盾结束时，若曾吸收实际伤害，回复最大生命2/2.5/3/3.5/4%，CD10s；不因换装和取消触发。|冰甲散成小晶蝶，逐级增加层次，治疗只一次。
THU_P1|奔雷|连续移动1.5s后下次直接雷技能伤害+4/5/6/7/8%，一次，CD6s。|准备完成后武器上出现由一点到五点电星的短提示。
THU_P2|雷冠庇护|一次雷技能命中至少3个不同真实敌人，获得4/5/6/7/8%最大生命护盾3s，CD10s。|薄雷环由单层变三层冠环，不与技能主爆争亮度。
ARC_P1|星轨校准|非终极法术的装备前摇修正后再缩短2/3/4/5/6%，总前摇缩短不超过15%，不缩敌方预警。|手边一到五片微型星页同步转动，释放时迅速消失。
ARC_P2|星核屏障|6s内三个不同主动技能直接命中，得4/5/6/7/8%最大生命护盾3s，CD10s；回响/次级事件不计数。|三次命中依次点亮星核边，三级后形成三角门，五级完整小星环。
'''
for line in PASSIVE_ROWS.strip().splitlines():
    key,name,effect,vfx=line.split('|')
    gate=GATES['p1' if key.endswith('1') else 'p2']
    values=re.search(r'\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?){4}',effect).group()
    SKILLS.append(dict(id=key,name=name,style=key.split('_')[0],type='passive',effect=effect,visual=vfx,
                       resourceCost=0,consumableCost=0,enemyForcedDisplacement=0,
                       ranks=[dict(rank=i+1,requiredCharacterLevel=gate[i],visualTier=i+1,
                                   primaryValue=float(values.split('/')[i]),effect=effect.replace(values,values.split('/')[i])) for i in range(5)]))

def xp_next(level):
    return 100+35*(level-1)+5*(level-1)**2 if level<40 else 0

def xp_to(level):
    return sum(xp_next(i) for i in range(1,level))

LEVEL_TABLE=[dict(level=i,xpToNext=xp_next(i),cumulativeXp=xp_to(i),baseMaxHp=120+5*(i-1),
                  baseSkillPowerS=round(24+1.5*(i-1),1),freeAttributePointsEarned=3*(i-1)) for i in range(1,41)]

PROGRESSION=dict(maxLevel=40,startingAttributes=dict(strength=10,dexterity=10,intellect=10,vitality=10),
                perLevel=dict(maxHp=5,baseSkillPower=1.5,freeAttributePoints=3),attributeCap=80,
                attributes=dict(strength='每点高于10：近战普攻/战技伤害+0.8%',
                                dexterity='每点高于10：弓普攻/弓术伤害+0.8%，所有直接攻击暴击率+0.12个百分点',
                                intellect='每点高于10：杖普攻/四系法术直接伤害+0.8%',
                                vitality='每点高于10：最大生命+4'),
                baseCritChance=.05,critChanceCap=.30,critMultiplier=1.5,
                xpTable=LEVEL_TABLE,skillRankGates=GATES,
                mainQuestTargetLevels=dict(M1=4,M2=10,M3=14,M4=20,M5=24,M6=30,M7=39,M8=40))

MIGRATION={'T01':'ARC_01','T02':'ARC_02','T03':'ARC_03','T04':'WAR_03','T05':'FRO_02','T06':'THU_02','T07':'FIR_05','T08':'ARC_05'}

# Every retained/new item gets an explicit current tooltip. Source IDs stay stable.
ITEM_EFFECT_ROWS='''
W01|可靠基础攻击；不绑定隐藏武器技。
W02|每第三次战技直接命中追加4火伤，CD2s；不产生场景燃烧。
W03|破阵技能对普通盾卫削韧+4、Boss+2，每次施放一次，CD3s。
W04|破军突袭命中2敌后，下一断空斩直接伤害+8%，4s内一次，CD8s。
W05|裂地审判终结段伤害+10%，计入增伤上限；没有额外施放键。
W06|主动技能直接命中带印记敌人，清除自己的奥印并得8护盾/3s，CD10s；若奥印同时触发，只清一次。
W07|穿云箭对首个普通盾卫的削韧+4，每次施放一次。
W08|弓术直接命中后移动速度+8%，2s，CD4s。
W09|穿云箭命中施寒缓25%/3s，CD8s；Boss仅减移动10%。
W10|疾风连射首个命中追加一次0.25S雷伤，可跳最近1敌；CD8s，次级事件不再连锁。
W11|免费杖基础弹；技能通过独立技能槽释放。
W12|焚星坠落主爆命中施3s燃烧，每秒0.15S，同源刷新不叠。
W13|寒晶刺命中寒缓敌额外削韧4，CD4s，Boss额外2。
W14|雷矛主命中追加一次0.35S雷伤，CD8s；次级伤害不递归。
W15|铁誓壁垒的护盾吸收量相对+12%；不覆盖技能键，不增加持续格挡操作。
W16|四系法术直接伤害+5%，非终极冷却缩短4%，受统一上限约束。
A01|最大生命+4。
A02|对超过5m目标的直接技能伤害+6%。
A03|火抗+10%。
A04|自己受到寒缓持续时间-20%，不是免疫。
A05|最大生命+15。
A06|疾影步后首次承受物理伤害-10%，2s内一次，CD8s。
A07|受到实际火伤后得5护盾，CD8s，不抵扣该次伤害。
A08|冰系直接命中寒缓目标后，当前剩余时间最长的非终极技能冷却-0.5s，CD8s。
A09|精确疾影步避开直接攻击后，下次战技削韧+4，4s内一次，CD6s。
A10|弓术技能前摇缩短8%；所有来源前摇缩短总计不超过15%，不缩射程或伤害窗。
A11|两个不同法术直接命中后，下次直接技能伤害+6%，4s内一次，CD6s。
A12|打开新宝箱后显示附近4m已可达线索轮廓3s，不自动领取。
A13|铁誓壁垒生效后3s受到物理伤害-6%，计入减伤上限。
A14|连续移动1.5s后移速+5%，停下1s失效。
A15|普通法术前摇/后摇的移动倍率至少0.65；不改变引导终极、瞬移或无敌时间。
A16|疾影步距离+8%，沿途仍检查墙、门与坑边。
J01|自身燃烧最长持续+1s，所有来源最长4s，不叠同源伤害。
J02|对寒缓目标的直接技能伤害+6%。
J03|主动技能命中带印记目标，终极蓄能额外+2，CD3s；同次施放只一次。
J04|非终极技能冷却缩短5%，受20%装备冷却缩减上限约束。
J05|直接雷技能命中自己的燃烧目标，清燃烧并追加0.35S奥术，CD8s；次级事件不再触发。
J06|冰抗+10%，雷抗-5%。
J07|6s内两个不同主动技能直接命中同敌，得6护盾3s，CD10s。
J08|最大生命+6；脱战显示最近已发现检查点方向。
L01|直接近战22%留下雷痕7s；下次断空斩引爆最多2痕，每痕0.3S雷伤，不递归连锁。
L02|穿云箭折返一次，回程每敌至多一次50%原伤；同次施放只生成一条回程。
DR1-01|最大生命+6。
DR1-02|受到物理伤害-4%，计入减伤上限。
DR1-03|破阵技能命中后，下次直接战技伤害+8%，3s内一次，CD6s。
DR1-04|命中超过5m目标，终极蓄能额外+2，CD4s，同次施放一次。
DR2-01|疾影步冷却缩短6%，计入20%装备缩减上限。
DR2-02|最大生命+8。
DR2-03|奥术飞弹首个命中对普通盾卫额外削韧4，Boss+2，CD6s。
DR2-04|疾影步后下次穿云箭直接伤害+8%，3s内一次，CD8s。
DR3-01|火抗+6%。
DR3-02|最大生命+8。
DR3-03|战技直接命中自己的燃烧目标，终极蓄能额外+2，CD3s。
DR3-04|直接雷伤后下次主攻击伤害+6%，4s内一次，CD8s。
DR4-01|最大生命+10。
DR4-02|受到物理伤害-5%，计入减伤上限。
DR4-03|断空斩打开普通敌护盾后，下一破军突袭削韧+4，3s内一次，CD6s；Boss仅+2。
DR4-04|生命首次低于35%获得8护盾4s，CD20s。
DU1-01|火抗+6%。
DU1-02|最大生命+8。
DU1-03|战技直接命中机械敌额外削韧2，Boss+1，CD3s。
DU1-04|每第三次法术施放实际直接命中，追加4奥术，CD3s；不是每枚弹计一次。
DU2-01|冰抗+6%。
DU2-02|普通法术前摇缩短4%，所有来源总缩短不超过15%。
DU2-03|直接技能命中寒缓敌，终极蓄能额外+2，CD4s，同次施放一次。
DU2-04|穿云箭命中带印记目标，追加4奥术，CD4s，不复制印记。
DE01|破阵技能成功打断明示起手后，下次直接技能伤害+10%，3s内一次，CD8s；Boss仅在明示可打断窗触发。
DE02|弓术命中后移动速度+8%，2s，CD5s。
DE03|灵泉复苏治疗量相对+8%，其前摇/后摇移动倍率为1.0；不增加治疗段数。
DE04|疾影步后下次战技削韧+3，3s内一次，CD8s；Boss+1.5。
DE05|裂地审判对机械敌额外削韧6，Boss+3，CD6s。
DE06|每第三次战技直接命中得4护盾3s，CD8s。
DE07|铁誓壁垒结束且曾吸收实际伤害，下一次基础攻击伤害+12%，4s内一次；取消和换装不触发。
DE08|灵能回响的复制系数增加8个百分点，最高56%；仍先截原模板总倍率至2.4S，不复制自身。
'''
ITEM_EFFECTS=dict(line.split('|',1) for line in ITEM_EFFECT_ROWS.strip().splitlines())

MOB_REPLACEMENTS={
 'R1-1':('灰披刀兵','举棍亮扇；侧移或用破阵技能打断起手，圆盾不提供重盾减伤'),
 'R1-2':('铁板盾卫','抬盾亮直线；侧绕或用任一流派破阵技能开盾2s'),
 'R3-2':('赤焰术士','举手聚成赤焰印，1.20s后指定落区爆炎；直接12基准伤与3s法术余焰，不投物品'),
 'R3-4':('钩刃战士','钩刃后收亮直线；横移或破阵打断，命中仅伤害与短受击，不带动角色'),
}

BOSS_LEVELS={'BOSS_R1':10,'BOSS_R2':18,'BOSS_R3':28,'BOSS_R4':38,
             'ELITE_01':8,'ELITE_02':17,'ELITE_03':27,'ELITE_04':36,
             'ELITE_05':19,'ELITE_06':16,'ELITE_07':24,'ELITE_08':27}

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join('---' for _ in headers)+'|']+
                     ['| '+' | '.join(str(v).replace('|','／').replace('\n','<br>') for v in row)+' |' for row in rows])

def gate_text(skill):
    return '/'.join(str(r['requiredCharacterLevel']) for r in skill['ranks'])

def make_catalog():
    catalog=dict(schemaVersion=1,contentVersion='pure-skills-v1',date='2026-11-08',status='design-only',
                 progression=PROGRESSION,styles=STYLES,skills=SKILLS,
                 equipmentEffects=ITEM_EFFECTS,retiredSpellToSkill=MIGRATION,
                 loadout=dict(active=4,ultimate=1,passive=2,fixedMobility='COM_01'),
                 rules=dict(ordinaryCost='cooldown only',ultimate='100 battle charge and shared 45s lock',
                            prohibitedActions=['inventory combat consumables','manual enemy shove','enemy forced displacement','environment explosive chain'],
                            normalChargePerDirectCast=6,basicChargePerDirectAction=4,chargeBonusCapPerCast=2,
                            playerLevelDoesNotBypassSkillGate=True,lateLearnedSkillRank='highest legal rank for current character level',
                            attributeDamageFormula='1 + 0.008 * (relevantAttribute - 10)',
                            passiveSlots=[dict(requiredCharacterLevel=6,slot=1),dict(requiredCharacterLevel=14,slot=2)],
                            effectRankFrozenAtRelease=True))
    assert len(SKILLS)==44 and len({s['id'] for s in SKILLS})==44
    assert len(ITEM_EFFECTS)==74
    for s in SKILLS:
        assert len(s['ranks'])==5 and s['consumableCost']==0 and s['enemyForcedDisplacement']==0
        assert all(a['requiredCharacterLevel']<b['requiredCharacterLevel'] for a,b in zip(s['ranks'],s['ranks'][1:]))
        assert max(r['requiredCharacterLevel'] for r in s['ranks'])<=40
    (OUT/'skill-catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return catalog

def build_campaign(catalog):
    source=ROOT/'source-art/encounters/cloud-world-v2/campaign-design.json'
    data=json.loads(source.read_text(encoding='utf-8'))
    assert len(data['legacyEquipment']+data['retainedLegendaries']+data['newEquipment'])==74
    data['contentVersion']='campaign-v7-pure-skills-design'
    data['skillCatalog']='source-art/skills/pure-skills-v1/skill-catalog.json'
    data['retiredCombatConsumables']=data.pop('consumables')
    data['consumables']=[]
    for item in data['legacyEquipment']+data['retainedLegendaries']+data['newEquipment']:
        item['previousDesignEffect']=item['effect']
        item['effect']=ITEM_EFFECTS[item['id']]
    region_levels={'R1':(1,10),'R2':(11,20),'R3':(21,30),'R4':(31,40),'U1':(5,20),'U2':(6,30)}
    for r in data['regions']:
        r['recommendedLevels']=list(region_levels[r['id']])
        if r['id']=='R3': r['theme']='海青、煤黑、琥珀；码头战士与赤焰秘术、古代钟卫'
    def clean(text):
        for a,b in [('推断','破阵打断'),('受推1.35m','受技能削韧'),('受推0.50m','受技能削韧'),('推断抬盾','破阵打断抬盾'),
                    ('推断起手','破阵打断起手'),('推断前摇','破阵打断前摇'),('推0.6m','短受击'),('推移0.6m','短受击'),
                    ('推断号声','破阵打断号声'),('最多两种同时警示','最多两种同时警示'),
                    ('黑油屠夫','焚潮统领'),('黑油投手','赤焰术士'),('投油','释放爆炎印'),('举壶','聚焰'),
                    ('油区','法术余焰区'),('无油','基础技能'),('火油','旧补给（战斗用法已退役）')]:
            text=text.replace(a,b)
        return text
    for mob in data['enemies']:
        mob['counter']=clean(mob['counter'])
        if mob['id'] in MOB_REPLACEMENTS:
            mob['name'],mob['counter']=MOB_REPLACEMENTS[mob['id']]
        mob['damageIsLevelOneBase']=True
        mob['enemyForcedDisplacement']=0
    for boss in data['bosses']:
        boss['baseHp']=boss['hp']
        boss['level']=BOSS_LEVELS[boss['id']]
        boss['hp']=math.floor(boss['baseHp']*(1+.14*(boss['level']-1))+.5)
        boss['name']=clean(boss['name'])
        boss['moves']=clean(boss['moves'])
        boss['moves']=re.sub(r'撞墩失衡[0-9.]+s','冲锋结束原地露出1.50s破绽',boss['moves'])
        boss['moves']=boss['moves'].replace('架盾受技能削韧、失衡0.25s','破阵技能削韧、原地短硬直0.25s')
        boss['damageIsLevelOneBase']=True
        boss['enemyForcedDisplacement']=0
        boss['fixedLoot']=boss['fixedLoot'].replace('W02+T03×3','W02+首领经验')
        if boss['id']=='BOSS_R3':
            boss['moves']='爆炎印：1.20/0.35s聚焰，直接12基准伤与3s法术余焰；裂焰斩：0.90/0.30s扇形18基准伤，后摇1.20s；两近战一弩手固定随从，起手可被破阵技能打断，不投掷物品'
        if boss['id']=='BOSS_R2':
            boss['moves']='盾锋突击：0.75/0.25s直线16基准伤，后摇0.85s；两岩脊弩哨错开瞄准；所有流派破阵技能都能削韧或开普通盾，不要求近身互动动作'
    boss_by_node={b['arena']:b for b in data['bosses']}
    node_edits={
      'S07':dict(reward='技能档案经验+220；P_R1机会'),
      'S10':dict(reward='M2包、W02；首领经验与角色等级成长',route='场外检查点，闪避盾冲后直接攻击1.50s破绽，不需要碰撞场景道具'),
      'H07':dict(reward='旧石柜改永久技能档案经验+450；P_R2机会'),
      'H08':dict(objective='清桥头组，以破阵技能破盾，战后操作放桥机关'),
      'B08':dict(reward='M5线索；固定W12+A03'),
      'B10':dict(objective='以战技或法术破解焚潮统领与固定随从，胜利后同台点验',reward='M6包；W10+J05；完整护符/余烬铜芯改技能外观二选一',route='侧步或疾影步离开爆炎印，预警不被特效遮盖；不依赖清场道具'),
      'B11':dict(route='剧情机关失败可回退；战斗只用技能'),
      'B09':dict(route='侧檐与干路可避法术落区，关键记录不会被毁'),
      'B12':dict(name='分潮水渠',objective='核对水渠与接应道路，沿干路击败赤焰术士',reward='铁3+金币25；P_R3机会',route='水渠是地理和剧情设施，不承担战斗灭火或必需反制'),
      'U2-05':dict(reward='永久技能档案经验+900；P_U2机会'),
      'F14':dict(reward='M7包：W06+J07保底；侧格为星界崩解·终誓外观，独立一次'),
      'S01-T3':dict(objective='识别锤痕、装备制作；查看技能和免费重配属性'),
    }
    for node in data['levels']:
        for field in ('encounter','objective','reward','route'): node[field]=clean(node[field])
        node.update(node_edits.get(node['id'],{}))
        low,high=region_levels[node['region']]
        if node['id'].startswith('U1-'):
            low,high=(5,10) if int(node['id'][-2:])<=5 else (16,20)
        if node['id']=='U2-01': low,high=6,8
        node['recommendedLevel']=[low,high]
        node['encounterLevel']=boss_by_node[node['id']]['level'] if node['id'] in boss_by_node else (low+high)//2
        node['encounterLevel']={'S04':2,'S07':4,'S08':5,'S09':7,'S11':7,'S12':8,'S14':8,'S15':7,'S18':3,'S19':5,'S20':8,'H03':13}.get(node['id'],node['encounterLevel'])
        if node['id']=='U2-01': node['encounterLevel']=0
    previous_target=1
    for reward in data['mainRewards']:
        rid=reward['id']
        target=PROGRESSION['mainQuestTargetLevels'][rid]
        reward['experience']=xp_to(target)-xp_to(previous_target)
        reward['minimumLevelAfterMainPackets']=target
        reward.pop('seals',None)
        reward['skillReward']='满足角色等级时永久学习与进阶；技能效果严格按角色等级门槛开放'
        reward['detail']=clean(reward['detail'])
        reward['detail']=re.sub(r'、?C1[1-7]','',reward['detail'])
        reward['gear']=clean(reward['gear'])
        if rid=='M7':
            reward['experienceBeforeFinalBoss']=xp_to(38)-xp_to(previous_target)
            reward['experienceAfterFinalBoss']=xp_to(39)-xp_to(38)
        if rid=='M2':
            reward['experienceBeforeGateBoss']=xp_to(8)-xp_to(previous_target)
            reward['experienceAfterGateBoss']=xp_to(10)-xp_to(8)
        reward['detail']=reward['detail'].replace('C09/C10/','C09/C10').replace('C02/','C02')
        if rid=='M7': reward['detail']=reward['detail'].replace('T08只在侧格唯一1张，不放主箱','侧格只提供终誓技能外观，不放主箱')
        reward['detail']=reward['detail'].replace('、；','；').replace('。、','。')
        if rid=='M6':
            reward['gear']='W10+J05；守誓护符/余烬铜芯二选一，对应壁垒/焚星技能外观'
            reward['detail']='另符纹4；二选一古物仅解锁对应外观，不改变技能伤害或角色等级门槛。'
        previous_target=target
    xp_events={
       'M1':[(4,'S04夺匣并确认原信')],
       'M2':[(8,'U1-05工匠实际离场'),(10,'S10击败并抬杆')],
       'M3':[(14,'H03散热试验实际回退')],
       'M4':[(18,'H09放桥后领取武备台'),(20,'U1-08第一次可中止接触')],
       'M5':[(22,'U2-03泄压试验回退'),(24,'U2-06两角度核验原刻')],
       'M6':[(30,'B10胜利后落链、三组点验并开匣')],
       'M7':[(34,'F04或F07核验至少一条实际安全出口'),(36,'首个外弩台拆销，东西顺序自由'),
              (38,'两个外弩台都拆销'),(39,'F14战后开主箱')],
       'M8':[(40,'U1-08实际执行终局并离场')],
    }
    previous_level=1
    for reward in data['mainRewards']:
        reward['experienceEvents']=[]
        for index,(target,trigger) in enumerate(xp_events[reward['id']]):
            reward['experienceEvents'].append(dict(id=reward['id']+'_XP_'+str(index+1),trigger=trigger,
                                                  experience=xp_to(target)-xp_to(previous_level),minimumMainOnlyLevel=target))
            previous_level=target
        assert sum(e['experience'] for e in reward['experienceEvents'])==reward['experience']
    for quest,level in zip(data['sideRewards'],[12,18,23,26,10,27]):
        quest['recommendedLevel']=level
        quest['experience']=math.floor(xp_next(level)*.75+.5)
    for boss in data['bosses']:
        boss['moves']=boss['moves'].replace('钉甲盾推','钉甲突击')
        boss['firstClearExperience']=(20+8*(boss['level']-1))*(8 if boss['mandatory'] else 3)
    # T entries are not obtainable goods in the current design.
    for item in data['legacyEquipment']:
        if item['id']=='W06': item['source']='M7 / F14主箱；侧格只提供终誓技能外观'
    data['progression']=PROGRESSION
    data['rules'].update(dict(
        capacity='永久装备74种、9槽；当前战斗消耗品0种。普通技能只结算冷却，终极只结算蓄能；制造仅保留10种永久装备配方，材料不用于战斗施法。',
        budget='原主线金币2060、铁110、符纹28、锻造芯2保持；10种永久装备首造需56/15/1，余54/13/1。退役7类制符配方，不再计其铁26成本。',
        combatCaps='装备增伤加算≤40%、装备冷却缩减≤20%、移速增益≤20%、物理减伤≤40%、前摇总缩短≤15%；护盾总量≤35%最大生命。属性伤害倍率单独计算。',
        levelRules='敌人固定地区/实例等级，不随玩家自动升降；生命=基准HP×(1+0.14×(等级-1))，伤害=基准伤害×(1+0.045×(等级-1))。',
        skillOnly='没有战斗背包耗材、手动敌人位移动作或场景爆炸连锁；敌人也不对玩家施加强制位移。',
        migration='T01—08旧物仅作为审计记录，合法拥有或已学制作记录映射永久技能；技能可记为已学但角色等级不足时锁定施放/进阶。数量不兑换多份技能；技能旧版技能冷却和新终极锁迁移不得刷新。'))
    data['rules']['pool']=data['rules']['pool'].replace('T08或','')
    data['validation'].update(consumableTypes=0,totalItemTypes=74,skills=44,skillRankRecords=220,characterMaxLevel=40)
    (OUT/'campaign-v7.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return data

def write_docs(catalog,data):
    intro='2026-11-08。按用户最新要求：纯技能战斗、炫酷爆发、五级形态变化、角色升级加属性，并以角色等级解锁技能和效果。**本轮为完整设计，尚未接入运行版；数值为待试玩候选。**\n\n'
    main='# 纯技能与五级成长设计 v1\n\n'+intro
    main+=('主循环为 **普攻 → 主动连招 → 闪避 → 终极爆发**。四个普通主动位、一个终极位、两个被动位，疾影步独立固定。'
           '普通技能只看冷却；没有蓝耗或背包张数，终极需要100蓄能和共享45s锁。'
           '每个技能都写有1—5级效果，学习与强化分别受角色等级门槛限制；取得技能记录不等于越级可用。\n\n'
           '- [人物1—40级、属性与经验](character-progression-v1.md)\n- [炫酷特效与逐级表现](skill-vfx-v1.md)\n'
           '- [97地点与首领技能反制](world-combat-v3.md)\n- [74装备与纯技能联动](equipment-skills-v3.md)\n'
           '- [44技能/220级记录JSON](../../source-art/skills/pure-skills-v1/skill-catalog.json)\n\n')
    main+='## 六个流派\n\n'+table(['流派','核心体验','满级视觉语言'],[(v['name'],v['feel'],v['shape']) for k,v in STYLES.items() if k!='COM'])+'\n\n'
    main+=('战技要求近战，弓术要求弓；四系法术与防护/通用技能可由任何主手释放。法杖、法器强化法术，但不把换武器变成学习法术的门票。'
           '铁誓壁垒不要求副手盾；副手盾只强化对应技能。安全整备处免费调整属性与配技能，战斗中不换装、不通过换槽刷新冷却。\n\n'
           '## 等级门槛\n\n')
    main+=table(['技能类型','1级 / 2级 / 3级 / 4级 / 5级所需角色等级'],[(GATE_LABELS[k],'/'.join(map(str,v))) for k,v in GATES.items()])+'\n\n'
    main+=('技能达到门槛后在技能页确认学习/进阶，'
           '无需金币或消耗书；允许“一键进阶已满足条件”，但不自动变更当前槽位。新学技能可升到本人的最高合法等级，不重新从1级刷熟练度。'
           '锁定卡同时写“尚未达到角色等级”和下一级的形态/机制预览；外观先得到也不能提前启用高级效果。\n\n'
           '## 伤害与爽感共同规则\n\n'
           '**S=24+1.5×（角色等级−1）**，代表技能威力。表中倍率是一次施放对同一目标的最高直接伤害总和，'
           '不是每条装饰光线都乘一遍。多段默认均分，特殊段权重由技能写明。'
           '最终伤害=本级S×技能倍率×对应属性倍率×（1+装备/状态加算增伤）×抗性，末尾四舍五入；治疗/护盾不吃伤害增幅或暴击。'
           '普通直接攻击每动作判一次暴击，整次技能的合法段共享结果，基础5%、上限30%、倍率1.5；持续伤和次级事件不暴击。'
           '若战技同时被元素装备附魔，主体仍按力量、次级固定附伤不再吃智识，避免同一次伤害连乘两种属性。\n\n'
           '每个技能释放有唯一castId，命中按castId+目标+声明段序号去重；次级装备事件每cast最多2项，不再触发装备/蓄能/复制。'
           '普通主动实际直接命中得6蓄能、基础攻击每动作命中得4；装备每cast额外最多2。多敌、多弹、持续区、治疗/护盾、虚拟靶和回响均不刷蓄能。'
           '已发出的终极不会返还蓄能；切槽、升级、读档和休整不清45s锁。首次达到16级开放一次100蓄能体验奖励，只能领一次。\n\n'
           '破阵标签：普通敌明示起手可打断、普通盾可开盾2s，目标有5s重复保护；Boss只累计韧槽，不被搬动。'
           'Boss韧槽100，满槽在允许窗口原地失衡0.8s，之后8s保护；单次施放最多贡献表中一次削韧，不按段数乘。'
           '冻结普通/精英按技能表，Boss改削韧，冻结共享8s保护。所有角色均无被攻击强制位移，位移技能只移动自己。\n\n'
           '## 全技能目录\n\n')
    for style,meta in STYLES.items():
        main+='### '+meta['name']+'\n\n'
        for s in [x for x in SKILLS if x['style']==style and x['type']!='passive']:
            main+='#### '+s['id']+' '+s['name']+'\n\n'
            main+=f"{'终极' if s['type']=='ultimate' else '普通主动' if s['type']=='active' else '固定闪避'}；兼容 **{dict(melee='近战武器',bow='弓',any='任意武器')[s['compatibleWeapons']]}**；{s['targetShape']}；前摇{ s['windupSeconds']}s；后摇{s['recoverySeconds']}s。\n\n"
            main+=table(['技能级 / 角色门槛','伤害上限 / 段数','范围 / 冷却','本级形态与效果'],[(f"{r['rank']}级 / Lv{r['requiredCharacterLevel']}",f"{r['maxDamagePerTargetS']}S / {r['authoredDamageHits']}段"+(f"；盾{r['shieldMaxHpPercent']}%HP" if r['shieldMaxHpPercent'] else '')+(f"；治疗{r['healMaxHpPercent']}%HP" if r['healMaxHpPercent'] else ''),f"射程{r['rangeMetres']}m / 半径{r['radiusMetres']}m / CD{r['cooldownSeconds']}s",r['evolution']) for r in s['ranks']])+'\n\n'
            main+=s['mechanic']+'\n\n'
        passives=[s for s in SKILLS if s['style']==style and s['type']=='passive']
        if passives:
            main+=table(['被动 / 门槛','五级效果'],[(s['id']+' '+s['name']+'；'+gate_text(s),s['effect']) for s in passives])+'\n\n'
    main+=('## 六套可直接试玩的配法\n\n'+table(['定位','四主动 / 终极 / 被动','连招与观感'],[
        ('破军近战','断空斩、破军突袭、铁誓壁垒、裂地审判 / 破晓裁决 / 战艺精通、铁誓不屈','壁垒接近→突袭→断空开盾→裂地余震→裁决收尾'),
        ('逐风射手','穿云箭、星雨齐射、疾风连射、猎王印 / 天穹贯星箭 / 鹰眼、逐风猎手','印记→穿云开盾→箭雨封落点→连射；终极取直线多敌'),
        ('爆炎法师','赤焰枪、焚星坠落、焰心护盾、凤凰掠影 / 天火降临 / 余烬掌握、薪火余辉','枪点燃→陨星次爆→掠影换位→天火压落，火焰来自技能'),
        ('寒霜控场','寒晶刺、冰霜新星、霜甲结界、冰河之刃 / 永冬降临 / 寒锋、凝霜守护','刺减速→新星定住普通敌→冰河多击；Boss用削韧换输出窗'),
        ('雷霆速攻','雷矛、连锁雷击、雷霆战印、闪雷穿行 / 九霄雷狱 / 奔雷、雷冠庇护','战印→穿行换线→雷矛开盾→连锁群爆→三拍雷狱'),
        ('星界混搭','奥术飞弹、裂界印记、灵能回响、星门闪跃 / 星界崩解 / 星轨校准、星核屏障','奥印→飞弹触发→回响复现→闪跃换线→光束五拍')])+'\n\n'
        '这些是全部技能可用后的样例，低等级面板只开放已满足门槛的格子。单技能与普攻仍能推进，不能用未解锁技能当新手必备解法。'
        '缺治疗时可用灵泉复苏替换任意普通主动；不同流派可混搭，互斥的武器要求仍要校验。\n\n'
        '## 输入、取消与失败\n\n'
        '键鼠建议：左键普攻，Q/E/R/F四主动，T终极，空格疾影步，G交互；旧的道具按键退出战斗栏。'
        '手机保留普攻大键、四主动、一个终极及独立闪避；按住可瞄准技能显示真实范围，拖至取消区或pointer cancel取消。'
        '预瞄可取消；释放前取消/被打断不启动技能CD，统一0.35s重试间隔；释放点提交冷却/终极蓄能，释放后取消后摇不退还。'
        '同帧输入优先死亡/暂停→疾影步→终极→四主动槽顺序→普攻→交互，不积压多条技能。'
        '技能门槛、装备兼容、目标可达与CD在接收和释放点各复核一次；未解锁只提示所需角色等级，不自动换技能。'
        '暂停/后台冻结游戏时间，清预瞄与缓冲；重载按已保存剩余CD与终极锁恢复，不重发技能。\n')
    (DOC/'combat-skills-v1.md').write_text(main,encoding='utf-8')

    prog='# 角色升级、属性与技能门槛 v1\n\n'+intro
    prog+=('角色上限40级，与装备L1—L5、技能1—5级分别保存和展示。每升一级自动最大生命+5、基础技能威力S+1.5，并得3点自由属性；'
           '初始生命120、S24，力量/敏捷/智识/体魄各10，单属性上限80。\n\n')
    prog+=table(['属性','每分配一点的实际收益'],[(ATTRIBUTE_LABELS[k],v) for k,v in PROGRESSION['attributes'].items()])+'\n\n'
    prog+=('最大生命=120+5×（角色等级−1）+4×（体魄−10）+装备固定生命。'
           '近战、弓、法术属性倍率分别为1+0.008×（对应属性−10）；不把三个攻击属性相乘。'
           '敏捷额外暴击与装备加算，最终≤30%；暴击一次动作只判一次。\n\n'
           '例：Lv20有57点自由属性，基础生命215、S52.5。可把力量40、体魄37，获得323生命与近战倍率1.24；'
           '若改智识40、体魄37，生命相同，1.24应用法术。安全整备处免费重配，返还已花点数再分配，不复制点数；'
           '实际升级带来的固定5生命同额加入当前生命；体魄加点、换装和属性重配只改变上限，当前生命最多截到新上限，不因增加体魄补血，避免来回重配治疗。\n\n'
           '## 技能的等级锁\n\n')
    prog+=table(['类型','一至五级要求'],[(GATE_LABELS[k],'/'.join('Lv'+str(x) for x in v)) for k,v in GATES.items()])+'\n\n'
    prog+=('技能等级与形态一体提交：不能1级技能带5级段数、范围或视觉终式。技能已学记录与可用等级分开，'
           '旧档获得对应传承也必须达到角色等级；角色降级的损坏数据不静默保留越级效果。'
           '普通一阶技能1级开放，各系第二技4级、第三技8级、第四技12级、终极16级；'
           '第一被动6级、第二被动14级；被动槽6级开放第一格、14级开放第二格。'
           '疾影步1级，灵泉复苏2级，二者在1/8/16/24/32附近成长（复苏首阶2级）。\n\n'
           '## 经验与世界成长\n\n'
           '升下一级经验=100+35×（当前级−1）+5×（当前级−1）²，40级封顶。'
           '主线八包独立给固定经验，按不击杀可选敌/不做支线也足以到40级的下限配置。'
           'M2救援段分配到8级，关口战后到10级；M7在终战前分配足够经验达到38级，允许终极第五阶在最终战使用；战后到39，M8收束到40。'
           '和平解除据点与对应击杀路径用同一事件经验收据，不能再清同组敌补领经验。\n\n')
    prog+=table(['主线包','固定经验','只计主线包最低等级','分段实际触发'],[(q['id'],q['experience'],q['minimumLevelAfterMainPackets'],'；'.join(e['trigger']+f"：{e['experience']}XP→Lv{e['minimumMainOnlyLevel']}" for e in q['experienceEvents'])) for q in data['mainRewards']])+'\n\n'
    prog+=('普通真实敌经验=20+8×（敌等级−1），八可选精英首领×3、四主线首领×8；召物/靶子/已败/虚拟复演不发经验。'
           '主线固定经验与首领首次经验分别记账，前者预算不借用后者；六人物支线各给其推荐等级下一次升级经验的75%，一次固定结算，'
           '不随拖到高等级领取而涨价。溢出经验连续升级，每级各发3点；40级后不把多余经验兑换成无限金币。\n\n'
           '地区建议：R1 1—10、R2 11—20、R3 21—30、R4 31—40；U1浅层5—10/深层16—20，U2前厅6—8/深层24—30。'
           '怪物固定等级不追随玩家；回访可碾压，但已败敌仍不复活。低级越区看见等级警示可退，不凭进入高图区越级解锁技能。'
           '敌生命=基准HP×[1+0.14×（敌等级−1）]，敌伤害=基准伤害×[1+0.045×（敌等级−1）]。'
           '这是首轮配表，尚未证明实战难度；角色和怪物成长一并试玩，不能拿旧360血Boss证明高等级平衡。'
           '装备L1—L5仍影响原普攻基线，技能S不再重复乘旧装备等级系数；装备特性独立计入，避免把等级成长乘两遍。\n\n'
           '## 1—40级完整经验与基础属性表\n\n')
    prog+=table(['等级','下级经验','累计经验','基础最大生命','S','累计自由点'],[(r['level'],r['xpToNext'],r['cumulativeXp'],r['baseMaxHp'],r['baseSkillPowerS'],r['freeAttributePointsEarned']) for r in LEVEL_TABLE])+'\n\n'
    prog+=('## 保存与旧档\n\n'
           '新增角色等级、累计经验、已分配四维、剩余点、技能已学/等级、槽位、全局终极锁和一次解锁赠能收据。'
           '分配点必须满足“起始10+已分配、单项≤80、已分配总数+剩余=3×（等级−1）”。升级奖励按XP账本去重，不能重载重复发点。'
           '旧档没有等级不能凭装备稀有度猜人物等级；依据可信已完成主线事件补固定经验并由同一曲线重算，其余仍给1级和保留旧装备。'
           '旧战斗耗材的合法拥有/制作历史只转换永久技能记录，不乘数量；未到等级仍锁定，T08映射星界崩解并留终誓外观。'
           '等级、技能门槛和旧档迁移是后续运行接入项，当前JSON是设计数据，不改现有SaveSnapshotV1。\n')
    (DOC/'character-progression-v1.md').write_text(prog,encoding='utf-8')

    vfx='# 技能特效与五级爆发表现 v1\n\n'+intro
    vfx+=('目标是升级后第一眼就看出更强：刃/弹/晶体结构、攻击段数、轨迹组织、范围边界、终结形态逐级变化。'
          '不能只把同一球体放大或换颜色。概念图是形态参考，不代表已完成序列帧、判定或引擎特效。\n\n')
    vfx+=table(['技能级','构图与材质','命中节奏','声画强度'],[
      (1,'单一核心形状，保留本人动作','一层主爆点','清脆主音，短残留'),
      (2,'增加第二层轨迹/刃缘，材质更锐','主爆点加细碎片','多一层高频细节'),
      (3,'展开有方向的阵纹，出现声明的新段数','主击与次击明确错拍','中低频加厚，0.03s命中停顿'),
      (4,'光翼/冠架/星门初成，外壳和核心分离','收束→爆发→快速退亮','0.04s停顿，局部冲击环'),
      (5,'完整签名构型：剑冠、天弓、凤凰、冰冠、雷狱、星核','主爆核0.08—0.16s，外环0.3—0.6s，尾部0.8—1.2s','有重量的低频终结，0.045s停顿，镜头可关闭')])+'\n\n'
    vfx+='## 各技能五级表现\n\n'
    for branch,meta in STYLES.items():
        vfx+='### '+meta['name']+' · '+meta['color']+'\n\n'
        vfx+=table(['技能','1级','2级','3级','4级','5级'],[(s['id']+' '+s['name'],*[r['evolution'] for r in s['ranks']]) for s in SKILLS if s['style']==branch and s['type']!='passive'])+'\n\n'
        for s in [x for x in SKILLS if x['style']==branch and x['type']=='passive']:
            vfx+='**'+s['name']+'：**'+s['visual']+'\n\n'
    vfx+=('## 实际战斗必须保留的信息\n\n'
          '技能落点/范围实线边界按真实本级数据绘制；敌方预警绘制层高于我方装饰尾迹，不能被凤凰或大光束完全盖住。'
          '以高亮细核和透明外壳做爆炸感，不整屏纯白、不持续泛光；角色脚圈和前方撤离方向始终可读。'
          '普通命中停顿只影响动画表现，不冻结输入或延迟敌人判定；同一0.15s最多一份停顿，三连击不重复叠停。'
          '每次施放只有一个主光效与主低频，附属爆环按节拍降亮；同帧多个技能以当前玩家和终极主爆为优先，不把所有粒子音效叠满。\n\n'
          '## 技术接入与降档\n\n'
          '复用现有Cocos 3.8.8的SpriteFrame图集、ParticleSystem、Burst、Line与现有Effects生命周期，不安装新特效库或下载引擎。'
          '每个技能发startup/release/hit/tick/end事件，携带skillId、rank、castId、世界朝向和实际边界。'
          '先接1级完整时序，再接3级新增段数与5级构型；升级只在下一次施放生效，不能中途改变已飞出技能等级。'
          '建议首轮最多3个大主效果、12条实体轨迹、48条装饰线、350个装饰粒子；这是待测预算，不是已测帧率。'
          '降档先减少远处碎片/体积雾/装饰线/残留，保留本级签名形状、命中节拍、实际判定边界与敌方预警，不能删掉合法伤害或压成1级外观。'
          '所有效果由对象池和区域根节点管理，暂停清瞬时尾迹，切区销毁，恢复不重播命中；后台不推进冷却和粒子预警。\n\n'
          '## 资产与验收\n\n'
          '[技能目录](../../source-art/skills/pure-skills-v1/skill-catalog.json)保存每级门槛/判定/形态；[图像记录](../../source-art/skills/pure-skills-v1/README.md)保存云端概念板提示词与独立审图。'
          '正式验收要看1/3/5级在同一镜头的真实释放、命中、取消、死亡与销毁，区分装饰粒子数和实际伤害段数；不能把概念图的爆炸感当作实机已经接入。\n')
    (DOC/'skill-vfx-v1.md').write_text(vfx,encoding='utf-8')

    world='# 纯技能关卡与首领反制 v3\n\n'+intro
    world+=('本页取代旧逐关表中的战斗道具/强制位移反制；97地点、地理端口和主线机关保留。剧情放桥、开门、镜架试验不变成额外战斗键。'
            '敌人等级固定，表中等级建议不是空气墙。首领招式数值是1级基准伤，按角色成长页的敌等级公式放大；HP已展示该固定等级实值。\n\n')
    for r in data['regions']:
        world+='## '+r['id']+' '+r['name']+'\n\n'
        world+=table(['地点','等级建议 / 固定敌级','敌阵 / 目标','奖励 / 反制'],[(n['id']+' '+n['name'],str(n['recommendedLevel'])+('；敌Lv'+str(n['encounterLevel']) if n['encounter']!='无' else '；无固定敌'),n['encounter']+'；'+n['objective'],n['reward']+'；'+n['route']) for n in data['levels'] if n['region']==r['id']])+'\n\n'
    world+='## 12场首领技能窗口\n\n'
    world+=table(['首领 / 固定级 / HP','招式与破绽','技能反制'],[(b['name']+f" / Lv{b['level']} / {b['hp']}",b['moves'],'侧移或疾影步避开明确落区→破阵技能积韧→后摇输出；各流派均有破阵，不要求特定装备') for b in data['bosses']])+'\n\n'
    world+=('原R3赤焰术士与焚潮统领的投掷造型已退出当前战斗设计，需要后续重画施法动作；旧图保留来源，不冒充技能动作通过。'
            '灰披队长与阿德里安的冲锋结束就给原地攻击窗，不靠撞场景物体触发。'
            '8可选首领仍允许交涉或停机，同一奖励事件；战斗完成和机关/开箱分别写入。\n')
    (DOC/'world-combat-v3.md').write_text(world,encoding='utf-8')

    eq='# 74件装备与纯技能联动 v3\n\n'+intro
    eq+=('本页取代旧装备特性中的消耗战斗道具、张数、旧专注开支和位移动作；装备ID、74永久种类、六区池权重及商人来源保持。'
         '普通主动只看冷却，终极使用蓄能。旧8种战斗耗材退役为永久技能记录，不再掉落/制造/售卖。\n\n')
    eq+=table(['装备','纯技能当前效果','来源'],[(i['id']+' '+i['name'],i['effect'],i.get('source','所在区域池' if i.get('weight') else '对应精英唯一奖')) for i in data['legacyEquipment']+data['retainedLegendaries']+data['newEquipment']])+'\n\n'
    eq+='## 旧符类型转永久技能\n\n'+table(['旧审计键','对应技能','当前规则'],[(old,skill,'已学记录不乘旧数量；达到角色门槛才可用，不能越级') for old,skill in MIGRATION.items()])+'\n\n'
    eq+=('旧C11—17制符配方不再制造战斗物品，旧已解锁记录保留作迁移依据；T08侧格改星界崩解·终誓外观，独立领取。'
         '卖店清理未售库存，已买物不直接销毁：先转永久已学记录并提交旧类型迁移收据；无可信来源的数据不猜奖。'
         '技能冷却、等级和终极锁不因出售装备/重配属性重置。\n\n'
         '## 主线大包与等级成长\n\n')
    eq+=table(['主线','金币/铁/经验','装备与技能'],[(q['id']+' '+q['name'],f"{q['gold']}/{q['iron']}/{q['experience']}",q['gear']+'；'+q['skillReward']) for q in data['mainRewards']])+'\n\n'
    eq+=('金币2060、铁110、符纹28、锻造芯2的主线基础预算保留，六支线金币960/铁40保留。'
         '10永久装备首造耗铁56/符纹15/芯1，余54/13/1；不再预留制符成本。'
         '普通敌20%区域池掉装、连续5次失败第6次保底、同档不重掷、重复补偿和据点同事件清算继续沿用，'
         '但不把技能当可堆叠掉落装备。普通技能满足人物门槛即可学，金币不足不会断主线技能；奖励丰厚来自装备、经验和角色效果成长。\n')
    (DOC/'equipment-skills-v3.md').write_text(eq,encoding='utf-8')

def main():
    catalog=make_catalog()
    data=build_campaign(catalog)
    write_docs(catalog,data)
    report=dict(skillCount=44,ordinaryActives=25,ultimates=6,fixedMobility=1,passives=12,
                rankRecords=220,maxCharacterLevel=40,attributePointsAt40=117,equipmentEffects=74,
                campaignNodes=len(data['levels']),bosses=len(data['bosses']),currentCombatConsumables=0,
                mandatoryQuestExperience=sum(q['experience'] for q in data['mainRewards']),experienceTo40=xp_to(40),
                runtimeImplemented=False)
    assert report['mandatoryQuestExperience']==report['experienceTo40']
    assert {i['id'] for i in data['legacyEquipment']+data['retainedLegendaries']+data['newEquipment']}==set(ITEM_EFFECTS)
    (OUT/'design-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False))

if __name__=='__main__': main()
