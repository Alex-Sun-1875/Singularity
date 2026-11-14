"""Materialize the reviewed skill-point design as a generator revision."""
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/'src/cocos/assets/scripts/features/combat/data/PureSkills.ts').read_text(encoding='utf8')
skills=json.JSONDecoder().raw_decode(source.split('export const COMBAT_SKILL_LIST:CombatSkillDef[] = ',1)[1])[0]
rank_source={d['id']:d['ranks'] for d in skills}
tables={}
for line in (ROOT/'docs/design/skill-points-progression-v1.md').read_text(encoding='utf8').splitlines():
 if line.startswith('| '):
  cells=[v.strip() for v in line.strip('|').split('|')]
  tables[cells[0]]=cells[1:]
FX={
 'WAR_01':[(5,{'finisherBasicPercent':20})], 'WAR_02':[(5,{'nextSlashBreakPercent':20})],
 'WAR_03':[(3,{'brokenReductionPercent':10,'brokenReductionSeconds':1}),(5,{'absorbBasicPercent':20})],
 'WAR_04':[(5,{'nextShieldPercent':10})], 'WAR_05':[(3,{'finalBreakPercent':20}),(5,{'shieldFinisherPercent':10})],
 'BOW_03':[(4,{'segmentSeconds':.09})], 'BOW_04':[(4,{'markSeconds':10}),(5,{'markBreakPercent':20})],
 'FIR_01':[(3,{'burningBonusPercent':5}),(5,{'burningBonusPercent':10})], 'FIR_02':[(5,{'refreshBurn':1})],
 'FIR_03':[(3,{'shieldBurnSeconds':.5}),(5,{'shieldMeteorRefresh':1})],
 'FIR_04':[(3,{'burningBonusPercent':5}),(5,{'burningBonusPercent':10})], 'FIR_05':[(5,{'finalBurningPercent':10})],
 'THU_03':[(2,{'buffSeconds':8}),(3,{'thirdBreakValue':4}),(4,{'buffSeconds':10}),(5,{'nextSpearPercent':15})],
 'COM_01':[(3,{'evadeBasicPercent':10}),(5,{'evadeBasicPercent':20})], 'COM_02':[(3,{'firstHealFraction':.5}),(5,{'emergencyHealPercent':6})],
 'WAR_P1':[(3,{'alternatePercent':8}),(5,{'alternatePercent':15})], 'WAR_P2':[(3,{'brokenLingerSeconds':1}),(5,{'brokenLingerSeconds':2})],
 'BOW_P1':[(3,{'stationaryBreakPercent':10}),(5,{'markedCriticalPercent':10})],
 'BOW_P2':[(3,{'speedSeconds':3}),(5,{'movingBasicPercent':15})],
 'FIR_P1':[(3,{'burningBonusPercent':6}),(5,{'burningBonusPercent':10})],
 'FIR_P2':[(3,{'spreadRadius':4}),(5,{'spreadTargets':3})],
 'THU_P1':[(3,{'movingSeconds':1.2}),(5,{'speedPercent':10})],
 'THU_P2':[(3,{'enemyThreshold':2}),(5,{'eliteSatisfies':1})],
}
patch={}
for d in skills:
 id=d['id'];suffix=id.split('_')[1]
 unlock={'01':1,'02':4,'03':8,'04':10,'05':11,'P1':6,'P2':11}[suffix]
 if id=='COM_02':unlock=2
 rows=[];cells=tables[d['name']]
 for i,old in enumerate(rank_source[id]):
  n=i+1;effects={}
  for minimum,values in FX.get(id,[]):
   if n>=minimum:effects.update(values)
  if d['type']=='passive':
   description=old.get('effect','')
   if n>=3:description+=' '+cells[1]
   if n>=5:description+=' '+cells[2]
  else:
   assert len(cells)==5,(id,cells)
   description=cells[i]
  row=dict(rank=n,requiredCharacterLevel=unlock,upgradeEffects=effects,upgradeEffect=description,evolution=description)
  if id=='COM_01':row['castRangeMetres']=[2.8,2.9,2.97,3.1,3.22][i]
  rows.append(row)
 patch[id]=dict(unlockLevel=unlock,ranks=rows)
out=Path(__file__).parent
(out/'skill-points-revision-v1.json').write_text(json.dumps(dict(date='2026-11-10',source='docs/design/skill-points-progression-v1.md',skills=patch),ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print('Prepared 30 skill definitions and 150 rank descriptions/effect parameters.')
