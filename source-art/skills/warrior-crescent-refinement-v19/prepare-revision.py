"""Author only the two reach revisions requested with the v15 visual reference."""
from pathlib import Path
import copy,json
ROOT=Path(__file__).resolve().parents[3]
DESIGN=ROOT/'tools/design'
fixed=json.loads((DESIGN/'fixed-skill-kit-v1.json').read_text(encoding='utf8'))['skills']
four=json.loads((DESIGN/'four-skill-kit-revision-v1.json').read_text(encoding='utf8'))['skills']
skills={}
ranks=[]
for old,reach in zip(fixed['WAR_01']['ranks'],[3.9,3.9,4.1,4.3,4.5]):
 g=copy.deepcopy(old['geometry']);g['radiusMetres']=reach
 text=f"近身单体月牙连斩，仅一个目标；合计{old['maxDamagePerTargetS']}S，{2 if old['rank']<3 else 3}段，距离{reach}米"
 if old['rank']==5:text+='；末段命中强化下一次普攻20%'
 ranks.append(dict(rank=old['rank'],rangeMetres=reach,castRangeMetres=reach,geometry=g,evolution=text,upgradeEffect=text,vfxDirection='两段宽幅半月剑气依次前推，尖端收束，银灰波身与细亮刃口区分；实际接触仍共享一个目标，不增加伤害段数。'))
skills['WAR_01']={'targetShape':'前方单体半月连斩','ranks':ranks}
ranks=[]
for old in four['WAR_02']['ranks']:
 g=copy.deepcopy(old['geometry']);g['lengthMetres']=round(g['lengthMetres']*1.8,3);g['widthMetres']=round(g['widthMetres']*1.35,3);g['radiusMetres']=round(g['lengthMetres']/2,3)
 text=f"最远{old['rangeMetres']}米突进，落点{g['lengthMetres']}米长的双月牙交叉斩"
 if old['rank']==5:text+='；命中后3秒内下一次断空斩削韧提高20%，一次'
 ranks.append(dict(rank=old['rank'],radiusMetres=g['radiusMetres'],geometry=g,evolution=text,upgradeEffect=text,vfxDirection='保持真实突进路径，落点交叉范围扩大；两道银灰半月在屏幕投影以120度交错，刃口细亮、波身有明暗，不生成白色实心大片。'))
skills['WAR_02']={'targetShape':'沿地面突进后双月牙交叉斩','ranks':ranks}
record={'schemaVersion':1,'reason':'用户以图二纠正实际战士剑气：银灰层次替代大片纯白；第一、第二技能扩大有效范围并恢复半月轮廓。保留伤害、目标预算、冷却、突进距离与护盾。','skills':skills}
(DESIGN/'warrior-crescent-revision-v2.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('Authored WAR_01 reach 3.9–4.5 m and WAR_02 landing cross length 2.88–3.744 m')
