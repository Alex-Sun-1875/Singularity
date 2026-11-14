"""Prepare 36 enemy move profiles from campaign-v8, without touching runtime.

Only --install writes EnemyCombat.ts; use after the current Creator build ends.
Existing state/telegraph/projectile/zone primitives are reused by the adapter.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source-art/skills/pure-skills-v2/campaign-v8.json'
OUTPUT=ROOT/'source-art/encounters/cloud-world-v2/combat-runtime-v1'

TYPES='''export type EnemyDamageElement='physical'|'fire'|'lightning'|'arcane';
export interface EnemyGeometry {
 kind:'fan'|'rectangle'|'circle'|'ring'|'line'|'none';origin:'caster'|'lockedTarget'|'arenaPoint';
 radiusMetres?:number;innerRadiusMetres?:number;angleDegrees?:number;gapAngleDegrees?:number;gapDirectionDegrees?:number;
 widthMetres?:number;lengthMetres?:number;offsetX?:number;offsetZ?:number;arenaPoint?:{x:number;z:number};onlyBelowHp?:number;
}
export type EnemyStatusDef={kind:'slow';percent:number;seconds:number}|{kind:'burn';baseDamagePerSecond:number;seconds:number};
export interface EnemyAttackableAnchor {kind:'stake'|'mirrorFrame'|'chainLock';placement:'casterFront'|'zoneEnd'|'zoneCenter';offsetMetres?:number;hp:number;radius:number;directHitsOnly:true;reward:false;expiresWithZone?:true;expiresWithStep?:true;interruptOwner?:true}
export interface EnemyProjectileDef {kind:'crossbow'|'spell';speed:number;range:number;radius:number;count:number;spreadDegrees:number;element:EnemyDamageElement;status?:EnemyStatusDef;collidesWithWalls:true;homing:false}
export interface EnemyZoneDef {duration:number;tickInterval:number;tickBaseDamage:number;element:EnemyDamageElement;maxTicks:number;maxActivePerOwner:number;status?:EnemyStatusDef;attackableAnchor?:EnemyAttackableAnchor;hitOncePerTarget?:boolean;blocksMovement:false}
export interface EnemySelfMove {mode:'charge'|'visibleReposition';distance:number;duration:number;collisionStops:true;collisionStaggerSeconds?:number}
export interface EnemySupportDef {effect:'nextWindupReduction'|'rallyApproach';radius:number;maxAffected:number;hasteSeconds?:number;minWindup?:number;duration:number;excludeSelf:true;affectsExistingOnly:true}
export interface EnemyAttackStep {
 id:string;windup:number;lock:number;active:number;baseDamage:number;element:EnemyDamageElement;geometry:EnemyGeometry[];
 maxHitsPerTarget:1;requiresLineOfSight:true;requiresSameLayer:true;targetTracking:'untilFinalLock';
 projectile?:EnemyProjectileDef;zone?:EnemyZoneDef;selfMove?:EnemySelfMove;support?:EnemySupportDef;attackableAnchor?:EnemyAttackableAnchor;
}
export interface EnemyAttackDef {
 id:string;label:string;legacyKind:'swing'|'charge'|'shot'|'short';pose:'attack_sword'|'attack_bow'|'spell'|'interact';
 minRange:number;maxRange:number;steps:EnemyAttackStep[];recovery:number;interruptible:boolean;cooldown?:number;requiresLivingAllies?:boolean;
}
export interface EnemyCombatProfile {
 id:string;name:string;route:'legacy'|'profile';body:'human'|'machine'|'beast';hurtRadius?:number;solidBody?:boolean;recoveryDamageMultiplier?:number;movement:{speed:number;turnRate:number;preferredRange:number;awarenessRange:number;damagedAwarenessRange:number;stationary?:true;facingPoint?:{x:number;z:number}};
 defense?:{guardArcDegrees:number;frontalDamageMultiplier:number;breakOpenSeconds:number};
 attackSlotCost:number;cycle:string[];attacks:Record<string,EnemyAttackDef>;
 halfHealth?:{threshold:number;once:boolean;queuedAttackId?:string;followUpAfter?:Record<string,string>};
 policy:{playerForcedDisplacement:0;hitReactionMovesEnemy:boolean;teleport:false;spawnReinforcements:false;idleBetweenMoves:number;offscreenTellSeconds:number};
 source:{catalog:string;catalogSha256:string;description:string;adapterTuning:string[]};
}
'''

def shape(kind:str,origin='caster',**kw):return dict(kind=kind,origin=origin,**kw)
def fan(radius=1.4,angle=80,**kw):return shape('fan',radiusMetres=radius,angleDegrees=angle,**kw)
def rect(length=2.4,width=.8,**kw):return shape('rectangle',lengthMetres=length,widthMetres=width,**kw)
def circle(radius=1.2,origin='lockedTarget',**kw):return shape('circle',origin,radiusMetres=radius,**kw)
def ring(outer=2.8,inner=.9,gap=0,**kw):return shape('ring',radiusMetres=outer,innerRadiusMetres=inner,gapAngleDegrees=gap,gapDirectionDegrees=180,**kw)
def line(length=16,width=.65,**kw):return shape('line',lengthMetres=length,widthMetres=width,**kw)
def projectile(kind='crossbow',speed=8,range=18):return dict(kind=kind,speed=speed,range=range,radius=.4,collidesWithWalls=True,homing=False)
def step(id,windup,lock,damage,geometry,active=.16,element='physical',**kw):
    return dict(id=id,windup=windup,lock=lock,active=active,baseDamage=damage,element=element,geometry=geometry if isinstance(geometry,list) else [geometry],maxHitsPerTarget=1,requiresLineOfSight=True,requiresSameLayer=True,targetTracking='untilFinalLock',**kw)
def move(id,label,steps,recovery,kind='swing',pose='attack_sword',min_range=0,max_range=2.5,**kw):
    return dict(id=id,label=label,legacyKind=kind,pose=pose,minRange=min_range,maxRange=max_range,steps=steps,recovery=recovery,interruptible=True,**kw)
def self_move(distance,duration,mode='charge',stagger=None):
    result=dict(mode=mode,distance=distance,speed=distance/duration,collisionStops=True)
    if stagger is not None:result['blockedStaggerSeconds']=stagger
    return result
def zone(duration,damage=0,tick=1,max_active=2,**kw):return dict(duration=duration,tickSeconds=tick,baseTickDamage=damage,maxActivePerOwner=max_active,blocksMovement=False,**kw)

def prepare():
    catalog=json.loads(SOURCE.read_text('utf-8'));source_hash=hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    profiles={}
    def profile(record,moves,cycle=None,body=None,speed=1.7,turn=3.2,preferred=1.4,defense=False,half=None,tuning=None,stationary=False,facing_point=None):
        id=record['id'];machine=body=='machine' or (body is None and ('机械'in record.get('role','') or id in ['ELITE_05','ELITE_06','ELITE_07','ELITE_08']))
        ranged=preferred>=8;boss='arena'in record
        data=dict(id=id,name=record['name'],body='machine'if machine else'human',movement=dict(speed=speed,turnRate=turn,preferredRange=preferred,awarenessRange=18 if ranged else 12,damagedAwarenessRange=30),attackSlotCost=2 if boss else 1,cycle=cycle or [m['id']for m in moves],attacks={m['id']:m for m in moves},policy=dict(playerForcedDisplacement=0,hitReactionMovesEnemy=False,teleport=False,spawnReinforcements=False,idleBetweenMoves=.5,offscreenTellSeconds=1),source=dict(catalog=str(SOURCE.relative_to(ROOT)).replace('\\','/'),catalogSha256=source_hash,description=record.get('moves',record.get('counter','')),adapterTuning=['Unspecified shape dimensions, movement speed/turn rate, preferred/start ranges and active windows adapt the existing Cocos state machine; these are tuning defaults, not newly claimed source values.','Damaged awareness is bounded30m for every identity including legacy, covering the largest legal player skill envelope (THU05 center18m +radius9m +target collider0.3m =27.3m). Initial awareness and ordinary18m projectile/start ranges remain unchanged; this is not unlimited pursuit.']+(tuning or [])))
        if defense:data['defense']=dict(guardArcDegrees=120,frontalDamageMultiplier=.4,breakOpenSeconds=0 if boss else 2)
        if stationary:data['movement'].update(stationary=True,facingPoint=facing_point)
        if half:data['halfHealth']=half
        profiles[id]=data
    for record in catalog['enemies']:
        id=record['id'];w=record['windup'];lock=record['lock'];d=record['damage'];recovery=record['recovery'];kw={}
        if id in ['R1-3','R2-2','R4-2']:
            moves=[move('crossbow','弩线瞄准', [step('bolt',w,lock,d,line(),.02,projectile=projectile())],recovery,'shot','attack_bow',max_range=18)];kw=dict(preferred=15)
        elif id in ['R1-2','R4-1']:
            moves=[move('shield-thrust','抬盾直击',[step('thrust',w,lock,d,rect(1.8,.9))],recovery,'charge')];kw=dict(defense=True,preferred=1.8)
        elif id=='R1-4':
            moves=[move('snare-line','展开绊索',[step('snare',w,lock,d,line(6,.6),zone=zone(3,slowPercent=.2,slowSeconds=1,destructibleByDirectHit=True,hitOncePerTarget=True))],recovery,'shot','interact',max_range=16)];kw=dict(preferred=12)
        elif id=='R2-1':moves=[move('pick-strike','过肩裂岩镐',[step('pick',w,lock,d,rect(2.5,.7))],recovery)]
        elif id=='R2-3':
            moves=[move('pincer','四足钳击',[step('clamp',w,lock,d,fan(1.7,100))],recovery)];kw=dict(body='machine',speed=1.35,turn=1.35,preferred=1.7)
        elif id=='R2-4':
            moves=[move('horn','号声协同',[step('signal',w,lock,0,circle(8,'caster'),.12,support=dict(effect='nextWindupReduction',radius=8,maxAffected=7,amount=.1,windupFloor=.65,affectsExistingOnly=True))],recovery,'short','interact',min_range=2,max_range=16,requiresLivingAllies=True),move('close-jab','近身短击',[step('jab',.65,.2,d,fan())],.8,'short')];kw=dict(preferred=10,tuning=['close-jab fallback timing .65/.2/.8 reuses basic melee when no eligible living allies remain; horn never summons entities.'])
        elif id=='R3-2':
            moves=[move('fire-seal','赤焰印落区',[step('eruption',w,lock,d,circle(1.5),element='fire',zone=zone(3,4))],recovery,'shot','spell',max_range=16)];kw=dict(preferred=12,tuning=['The 4 base damage/second lingering flame is retained from the prior encounter source, reskinned as authored spell afterburn; no thrown item.'])
        elif id=='R3-3':moves=[move('bell-ring','钟腹环震',[step('ring',w,lock,d,ring())],recovery)];kw=dict(speed=1.2,turn=1.8,preferred=2.6)
        elif id=='R3-4':moves=[move('hook-blade','钩刃直击',[step('hook',w,lock,d,rect(3,.65))],recovery)];kw=dict(preferred=2.5)
        elif id=='R4-3':moves=[move('mirror-line','折镜光带',[step('beam',w,lock,d,line(16,.7),element='arcane')],recovery,'shot','spell',max_range=16)];kw=dict(preferred=13,tuning=['Arcane is an enemy optical-damage label only, never an ARC player skill/unlock.'])
        elif id=='R4-4':
            moves=[move('banner-double','旗杆双击',[step('first',w,lock,d,fan(2,100)),step('second',.65,.25,d,fan(2,110))],recovery),move('banner-rally','号令现有同伴',[step('rally',w,lock,0,circle(8,'caster'),support=dict(effect='rallyApproach',radius=8,maxAffected=2,duration=2,affectsExistingOnly=True))],recovery,'short','interact',max_range=12,requiresLivingAllies=True)];kw=dict(preferred=2,tuning=['Second banner swing telegraph .65s and rally radius/count are adapter defaults; each swing has an independent warning.'])
        elif id=='U1-1':moves=[move('hammer-arm','锤臂矩形',[step('hammer',w,lock,d,rect(2.2,1.2))],recovery)];kw=dict(speed=1.3,preferred=2.1)
        elif id=='U1-2':moves=[move('resonance','六足鸣震',[step('pulse',w,lock,d,circle(1.35,'caster'))],recovery)];kw=dict(speed=1.9,turn=2.4,preferred=1.3)
        elif id=='U1-3':moves=[move('lantern-hook','举灯钩刺',[step('hook',w,lock,d,rect(2.4,.7))],recovery)];kw=dict(preferred=2.3)
        elif id=='U1-4':moves=[move('counterweight','配重落框',[step('slam',w,lock,d,rect(2,2,origin='lockedTarget'))],recovery)];kw=dict(speed=1,turn=1.4,preferred=2.7)
        elif id=='U2-1':moves=[move('hook-feet','钩足四角',[step('feet',w,lock,d,rect(2,1.8))],recovery)];kw=dict(speed=1.45,turn=1.9,preferred=1.8)
        elif id=='U2-2':moves=[move('tablet-swing','石板短扇',[step('swing',w,lock,d,fan(1.8,90))],recovery)];kw=dict(defense=True,speed=1.15,preferred=1.8)
        elif id=='U2-3':moves=[move('lens-bolt','镜眼地面光点',[step('light',w,lock,d,line(18,.5),.02,'arcane',projectile=projectile('spell',9))],recovery,'shot','spell',max_range=18)];kw=dict(preferred=14,body='machine',tuning=['Mirror floats only visually; its gameplay collider stays within basic weapon height.'])
        elif id=='U2-4':moves=[move('gapped-bell','缺口钟震',[step('ring',w,lock,d,ring(3.2,1,90),element='arcane')],recovery,'swing','spell',max_range=3.4)];kw=dict(speed=1.15,preferred=3.1)
        else:moves=[move('blade-swing','举刃短扇',[step('swing',w,lock,d,fan(1.4,80))],recovery)]
        profile(record,moves,**kw)
    bosses={r['id']:r for r in catalog['bosses']}
    def boss(id,moves,**kw):profile(bosses[id],moves,**dict({'speed':1.5},**kw))
    boss('BOSS_R1',[
        move('sweep','锤横扫',[step('sweep',.8,.25,22,fan(2.1,150))],1),
        move('charge','盾冲',[step('charge',1,.35,24,fan(1,150),.55,selfMove=self_move(3.8,.55,stagger=1.5))],1.5,'charge',max_range=8),
        move('short','半血短击',[step('short',.6,.25,14,fan(1.5,150))],1.2,'short'),
    ],cycle=['sweep','charge'],defense=True,preferred=2.8,half=dict(threshold=.5,once=False,followUpAfter={'sweep':'short'}),tuning=['Preserves the tested R1 sweep/charge/half-health short-step states and their 150 degree geometry. Charge ending recovery is the new authored 1.50s opening, independent of obstacle collision.'])
    boss('BOSS_R2',[move('shield-rush','盾锋突击',[step('rush',.75,.25,16,rect(1.2,.9),.28,selfMove=self_move(1.2,.28))],.85,'charge')],defense=True,preferred=1.8,tuning=['The two R2-2 escorts are existing authored spawns; their attack slots must be staggered, never spawned by the boss.'])
    boss('BOSS_R3',[move('fire-seal','爆炎印',[step('eruption',1.2,.35,12,circle(1.6),element='fire',zone=zone(3,4))],1,'shot','spell',max_range=16,cooldown=3.5),move('flame-cleave','裂焰斩',[step('cleave',.9,.3,18,fan(2,120),element='fire')],1.2)],preferred=11,tuning=['Afterburn 4/s, 1s recovery and 3.5s seal cooldown retain prior-source concrete values where v8 gives no replacement. Fixed escorts are owned by WorldData, not this profile.'])
    boss('BOSS_R4',[
        move('double-slash','重斩两段',[step('first',.85,.25,22,fan(2.4,120)),step('second',.65,.25,18,fan(2.4,130))],1.35),
        move('shield-charge','统帅盾冲',[step('charge',1.05,.35,26,fan(1.1,100),.65,selfMove=self_move(4.8,.65,stagger=1.5))],1.5,'charge',max_range=10),
        move('inner-bolts','半血内弩号令',[step('call',1.4,0,0,shape('none'),.02),step('left-port',1,1,16,line(36,.65,origin='arenaPoint',arenaPoint=dict(x=-23,z=24)),.02,projectile=projectile(range=36)),step('right-port',1,1,16,line(36,.65,origin='arenaPoint',arenaPoint=dict(x=23,z=24)),.02,projectile=projectile(range=36))],.5,'shot','interact',max_range=30),
    ],cycle=['double-slash','shield-charge'],defense=True,preferred=2.8,half=dict(threshold=.5,once=True,queuedAttackId='inner-bolts'),tuning=['Slash fan dimensions, charge active .65s, fixed F13 inner-port coordinates and projectile speed/range are adapter geometry. Inner ports are one queued volley, not revived outer-tower entities.','Only the two fixed F13 ports use36m projectile range and line warning length: each is24.70m from the boss at(0,15), so the ordinary18m moving-crossbow range cannot reach the central encounter. Both ports keep their fixed positions, separate1s lock warnings,16 base damage and once-only half-health trigger.'])
    boss('ELITE_01',[move('split-pick','裂地镐',[step('pick',.95,.3,18,rect(3,.65))],1.1),move('rope-pull','横拉绳',[step('rope',1.2,.35,12,line(6,.6),zone=zone(3,slowPercent=.2,slowSeconds=1,destructibleByDirectHit=True,hitOncePerTarget=True))],1.2,'shot','interact',max_range=12),move('lamp-sweep','收灯横扫',[step('lamp',1.1,.3,16,fan(2.2,140))],1.2)],cycle=['split-pick','rope-pull'],preferred=2.5,half=dict(threshold=.5,once=True,queuedAttackId='lamp-sweep'))
    boss('ELITE_02',[move('double-arrow','双风箭',[step('first',1.25,.35,14,line(),.02,projectile=projectile()),step('second',.7,.3,14,line(),.02,projectile=projectile())],1.6,'shot','attack_bow',max_range=18),move('pin-arrow','钉地箭',[step('pin',1.3,.4,16,circle(1.2),zone=zone(4,destructibleByDirectHit=True,hitOncePerTarget=True))],1.3,'shot','attack_bow',max_range=18),move('rock-reposition','沿山路换岩位',[step('walk',0,0,0,shape('none'),2,selfMove=self_move(4,2,'visibleReposition'))],.5,'short','interact',max_range=24)],cycle=['double-arrow','pin-arrow'],preferred=15,half=dict(threshold=.5,once=True,queuedAttackId='rock-reposition'),tuning=['Pin-arrow aftermath has zero additional damage: source gives a destructible stake and duration, not extra damage. Reposition is path movement, never teleport/invulnerability.'])
    boss('ELITE_03',[move('hook','拖钩直击',[step('hook',1.1,.35,18,rect(3,.7))],1.2),move('rope-sweep','缆绳横扫',[step('sweep',1.2,.35,20,fan(2.4,140))],1.4),move('anchor','半血吊锚',[step('drop',1.5,.5,22,circle(1.8))],1.8,'short','interact',max_range=14)],cycle=['hook','rope-sweep'],preferred=2.8,half=dict(threshold=.5,once=True,queuedAttackId='anchor'))
    boss('ELITE_04',[move('spike-rush','钉甲突击',[step('rush',1,.35,20,rect(2.5,1),.4,selfMove=self_move(2.5,.4))],1.2,'charge'),move('hammer-double','锤击两段',[step('first',1.1,.3,18,fan(2,100)),step('second',.75,.25,14,fan(2,110))],1.5),move('key-chain','钥链锁道',[step('chain',1.4,.4,12,line(6,.6),zone=zone(3,destructibleByDirectHit=True,hitOncePerTarget=True))],1.2,'shot','interact',max_range=12)],defense=True,preferred=2.4)
    double_boxes=[rect(1.6,1.6,origin='lockedTarget',offsetX=-1),rect(1.6,1.6,origin='lockedTarget',offsetX=1)]
    boss('ELITE_05',[move('double-hammer','双锤落地',[step('hammers',1.4,.4,22,double_boxes)],1.6),move('pressure-ring','冷光泄压',[step('ring',1.6,.5,18,ring(4,1.2,80),element='arcane')],1.5,'short','spell',max_range=4.3),move('overload-hammer','过载重复锤击',[step('extra-hammer',1.8,.5,22,double_boxes)],1.8)],cycle=['double-hammer','pressure-ring'],body='machine',turn=1.3,preferred=3,half=dict(threshold=.5,once=True,queuedAttackId='overload-hammer'),tuning=['Both hammer boxes share one hit ledger for this step, not 22 damage twice at the overlap. The once-only overload queues after the current action to repeat a hammer with its own1.8s warning.'])
    boss('ELITE_06',[
        move('three-blades','第一剑→第二剑→第三剑',[step('first',.9,.3,16,fan(2.5,120)),step('second',.85,.3,16,rect(3.2,1.4)),step('third',1.1,.35,20,[rect(5,.75),fan(3,240,gapAngleDegrees=80,gapDirectionDegrees=180,onlyBelowHp=.5)])],1.8,max_range=2.8),
        move('oath-cut','守誓追斩',[step('ground-cut',1.25,.4,20,rect(12,.9))],1.8,'shot','spell',min_range=4,max_range=12,cooldown=7)
    ],cycle=['three-blades','oath-cut'],body='machine',preferred=2.2,speed=2,turn=2.8,tuning=[
        '2026-11-12 user-requested behavior review supersedes the fixed door-facing emplacement: the shared base visibly glides at2m/s and tracks the player until each final lock; no teleport or invented walking frames.',
        'Three statues remain one logical formation and one HP/reward ledger. Existing independently drawn blade poses are reused; the ranged cut uses the third-blade pose. Independent statue anchors remain an art limitation.',
        'Melee starts within2.8m and retains all three original windups, locks, damage,1.8s recovery and the half-health third-sword gap. The melee third cut returns to5m rather than the historical30m fixed-axis adapter.',
        'Beyond4m, a12m x0.9m ground-cut has1.25s warning,0.4s final lock,20damage,1.8s recovery and7s cooldown. Between moves the formation closes distance using existing collision/navigation. Movement and attack positions are authoritative; no HP/loot increase.'
    ])
    boss('ELITE_07',[move('wheel-rush','闸轮盾撞',[step('rush',1.2,.4,22,rect(3,1.2),.5,selfMove=self_move(3,.5))],1.4,'charge'),move('counterweight','配重砸击',[step('slam',1.5,.45,24,rect(2.2,2.2,origin='lockedTarget'))],1.6),move('sluice-channels','半血交替光槽',[step('left',1.8,.5,16,line(12,1.1,offsetX=-2),element='arcane'),step('right',1,.4,16,line(12,1.1,offsetX=2),element='arcane')],1.4,'shot','spell',max_range=16)],cycle=['wheel-rush','counterweight'],body='machine',defense=True,preferred=3,half=dict(threshold=.5,once=True,queuedAttackId='sluice-channels'),tuning=['Second-channel warning1.0s and line offsets/dimensions are adapter defaults. Bounded strips leave dry side lanes; no water level/countdown system is introduced.'])
    boss('ELITE_08',[move('double-mirrors','聚镜→左束→右束',[step('focus',1.4,.4,0,shape('none'),.02),step('left',.8,.3,14,line(16,.6,offsetX=-1.2),element='arcane'),step('right',.8,.3,14,line(16,.6,offsetX=1.2),element='arcane')],1.5,'shot','spell',max_range=16),move('tablet-seals','双铭板落印',[step('seals',1.5,.5,18,[circle(1.1,offsetX=-1.4),circle(1.1,offsetX=1.4)])],1.4,'shot','spell',max_range=16),move('open-core','半血开镜',[step('core-beam',1.8,.5,20,line(18,.9),element='arcane')],2,'shot','spell',max_range=18)],cycle=['double-mirrors','tablet-seals'],body='machine',preferred=13,half=dict(threshold=.5,once=True,queuedAttackId='open-core'),tuning=['Opening focus1.4s precedes each independent0.8s beam warning. Two seal disks share a step hit ledger. The exposed core remains hittable from any legal range.'])
    assert len(profiles)==36
    expected={r['id']for r in catalog['enemies']+catalog['bosses']};assert set(profiles)==expected
    for p in profiles.values():
        p['route']='legacy' if p['id'] in ['R1-1','R1-2','R1-3','BOSS_R1'] else 'profile'
        assert all(id in p['attacks']for id in p['cycle'])
        for move_data in p['attacks'].values():
            assert move_data['steps'] and move_data['recovery']>=0
            for s in move_data['steps']:
                if 'projectile'in s:s['projectile'].update(count=1,spreadDegrees=0,element=s['element'])
                if 'zone'in s:
                    z=s['zone'];z['tickInterval']=z.pop('tickSeconds');z['tickBaseDamage']=z.pop('baseTickDamage');z['element']=s['element'];z['maxTicks']=int(z['duration']/z['tickInterval'])
                    if p['id'] in ['R1-4','ELITE_01','ELITE_04'] and z.get('hitOncePerTarget'):
                        z['tickBaseDamage']=s['baseDamage'];s['baseDamage']=0;z['tickInterval']=.25;z['maxTicks']=int(z['duration']/.25)
                        if p['id']=='R1-4':
                            for g in s['geometry']:g['origin']='lockedTarget'
                    if 'slowPercent'in z:z['status']=dict(kind='slow',percent=z.pop('slowPercent'),seconds=z.pop('slowSeconds'))
                    if z.pop('destructibleByDirectHit',False):
                        z['attackableAnchor']=dict(kind='chainLock' if p['id']=='ELITE_04' else 'stake',placement='zoneEnd',hp=12,radius=.45,directHitsOnly=True,reward=False,expiresWithZone=True)
                        p['source']['adapterTuning'].append('Attackable hazard anchor HP12/radius0.45 are explicit adapter defaults; one baseline free weapon hit clears it, and it gives no resource/loot reward.')
                        p['source']['adapterTuning'].append('The visible stake/chain lock is placed at the hazard zone end (a circular pin landing has its end at its center). This endpoint is adapter placement: line/rectangle length is clipped by real visibility and same layer; the anchor backs off by its radius to a reachable legal endpoint. If no counterable anchor exists, do not create an uncounterable zone. The source specifies a visible bypassable chain, not a unique authored lock coordinate.')
                if 'selfMove'in s:
                    m=s['selfMove'];m['duration']=m['distance']/m.pop('speed')
                    if 'blockedStaggerSeconds'in m:m['collisionStaggerSeconds']=m.pop('blockedStaggerSeconds')
                    if m['mode']=='charge':
                        move_data['maxRange']=round(m['distance']+.32,3)
                        p['source']['adapterTuning'].append('Charge start range is travel distance +0.32m player collider radius, so the authored movement can physically reach a stationary target; damage and windup are unchanged.')
                if 'support'in s:
                    support=s['support'];support['excludeSelf']=True;support.setdefault('duration',6)
                    if 'amount'in support:support['hasteSeconds']=support.pop('amount')
                    if 'windupFloor'in support:support['minWindup']=support.pop('windupFloor')
                if p['id']=='R4-3':
                    s['attackableAnchor']=dict(kind='mirrorFrame',placement='casterFront',offsetMetres=.8,hp=12,radius=.5,directHitsOnly=True,reward=False,expiresWithStep=True,interruptOwner=True)
                    p['source']['adapterTuning'].append('Mirror frame HP12/radius0.5 is a targetable adapter anchor, not another reward-bearing enemy; destroying it interrupts this beam step.')
                    p['source']['adapterTuning'].append('Mirror frame is a physical counter at0.8m in front of its caster, not the far beam endpoint; placement is an explicit reachable adapter offset.')
                assert 0<=s['lock']<=s['windup'] and s['active']>0 and s['baseDamage']>=0
                assert s['maxHitsPerTarget']==1 and s['requiresLineOfSight'] and s['requiresSameLayer']
    OUTPUT.mkdir(parents=True,exist_ok=True)
    text=json.dumps(profiles,ensure_ascii=False,indent=2)
    (OUTPUT/'enemy-combat-profiles.json').write_text(text+'\n','utf-8')
    ts='/** Prepared by tools/design/prepare-enemy-combat.py. Adapter tuning is explicitly separated from authored damage/timings. */\n'+"import {MONSTER_COMBAT_PROFILES,installHuntProfiles} from '../../world/data/MonsterEcology';\nimport {applyEarlyChapterBosses} from './EarlyChapterBosses';\n"+TYPES+'export const ENEMY_COMBAT_PROFILES:Record<string,EnemyCombatProfile> = {\n  ...MONSTER_COMBAT_PROFILES,'+text[1:]+';\ninstallHuntProfiles(ENEMY_COMBAT_PROFILES);\napplyEarlyChapterBosses(ENEMY_COMBAT_PROFILES);\nfor(const profile of Object.values(ENEMY_COMBAT_PROFILES))profile.policy.hitReactionMovesEnemy=!profile.movement.stationary&&!profile.solidBody;\n'
    (OUTPUT/'EnemyCombat.ts.preview').write_text(ts,'utf-8',newline='\n')
    report=dict(status='data-validated-runtime-acceptance-separate',profiles=36,common=24,bosses=12,moves=sum(len(p['attacks'])for p in profiles.values()),steps=sum(len(m['steps'])for p in profiles.values()for m in p['attacks'].values()),sourceSha256=source_hash,validation=['exact36 canonical identities','valid cycle references','lock window within authored windup','positive active window','one target hit per step union','wall/same-layer legality','no forced player displacement or teleport','no reinforcement spawn','no retired player skill IDs'],runtimeConsumer='src/cocos/assets/scripts/features/combat/common/EnemyCombat.ts',runtimeWiring='Not evaluated by this data exporter: core integration and live mechanism probes are separate evidence',artAcceptance='Not evaluated by this data exporter: independently generated pilots and runtime silhouette/gait reviews are separate evidence')
    (OUTPUT/'profile-validation.json').write_text(json.dumps(report,indent=2)+'\n','utf-8')
    return ts,report

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--install',action='store_true');args=parser.parse_args();ts,report=prepare()
    if args.install:(ROOT/'src/cocos/assets/scripts/features/combat/data/EnemyCombat.ts').write_text(ts,'utf-8',newline='\n')
    print(json.dumps(report))

if __name__=='__main__':main()
