/** Read the actual Cocos catalog, not the legacy story JSON. */
import {AREAS} from '../../src/cocos/assets/scripts/features/world/data/WorldData';
import {EQUIPMENT} from '../../src/cocos/assets/scripts/features/equipment/data/Equipment';
import {COMBAT_SKILL_LIST} from '../../src/cocos/assets/scripts/features/combat/data/PureSkills';
import {CAMPAIGN_BOSSES,CAMPAIGN_COMMON_ENEMIES,MAIN_XP_EVENTS} from '../../src/cocos/assets/scripts/features/campaign/data/Campaign';
import {CAMPAIGN_EVENT_LIST} from '../../src/cocos/assets/scripts/features/campaign/data/CampaignEvents';
import {Navigation} from '../../src/cocos/assets/scripts/features/navigation/runtime/Navigation';
import {writeFileSync, mkdirSync,readFileSync,existsSync} from 'node:fs';
import {resolve} from 'node:path';
const target=process.argv[2] ? resolve(process.argv[2]) : resolve(__dirname,'../../source-art/encounters/cloud-world-v2');
const problems:string[]=[];
const expect=(condition:boolean,message:string)=>{if(!condition)problems.push(message);};
expect(Object.keys(AREAS).length===97,'Campaign must contain all 97 designed nodes');
expect(Object.keys(EQUIPMENT).length===74,'Campaign must contain 74 permanent equipment definitions');
expect(COMBAT_SKILL_LIST.length===30&&COMBAT_SKILL_LIST.reduce((sum,skill)=>sum+skill.ranks.length,0)===150,'Skill catalog must contain 30 skills / 150 ranks');
expect(COMBAT_SKILL_LIST.every(skill=>!skill.id.startsWith('ARC_')&&!skill.id.startsWith('FRO_')),'Retired skill IDs cannot be selectable');
expect(CAMPAIGN_BOSSES.length===12&&CAMPAIGN_COMMON_ENEMIES.length===24,'Campaign enemy catalog is incomplete');
const identities=new Set<string>();
for(const area of Object.values(AREAS)){
 const nav=new Navigation(area.width,area.depth,area.obstacles);
 for(const point of [...area.objects,...area.exits,...area.enemies]){
  expect(!identities.has(point.id),`Duplicate identity ${point.id}`);identities.add(point.id);
  expect(Math.abs(point.x)<area.width/2-.7&&Math.abs(point.z)<area.depth/2-.7,`${area.id}/${point.id} outside scene bounds`);
  expect(!area.obstacles.some(obstacle=>Math.abs(point.x-obstacle.x)<obstacle.width/2+.7&&Math.abs(point.z-obstacle.z)<obstacle.depth/2+.7),`${area.id}/${point.id} overlaps collision`);
  expect(nav.path(area.spawn,point).length>0,`${area.id}/${point.id} has no walking approach`);
 }
 for(const exit of area.exits){
  const destination=AREAS[exit.to];expect(!!destination,`${area.id}/${exit.id} has unknown destination`);
  if(destination){expect(destination.exits.some(reverse=>reverse.to===area.id),`${area.id}/${exit.id} has no return path`);const incomingNav=new Navigation(destination.width,destination.depth,destination.obstacles);expect(incomingNav.path(exit.entry,destination.spawn).length>0,`${area.id}/${exit.id} lands outside navigation`);}
 }
}
const reachable=new Set(['S01']);let changed=true;
while(changed){changed=false;for(const id of [...reachable])for(const exit of AREAS[id].exits)if(!reachable.has(exit.to)){reachable.add(exit.to);changed=true;}}
expect(reachable.size===97,`Only ${reachable.size}/97 nodes are connected to the walking graph`);
for(const boss of CAMPAIGN_BOSSES){
 const arena=AREAS[boss.arena!];expect(!!arena&&arena.enemies.some(enemy=>enemy.bossId===boss.id),`${boss.id} is missing from its authored arena`);
 if(arena)expect(arena.obstacles.filter(obstacle=>obstacle.kind!=='pillar').every(obstacle=>Math.abs(obstacle.x)-obstacle.width/2>=18||Math.abs(obstacle.z-15)-obstacle.depth/2>=13),`${boss.id} lacks its expanded 36×26m firing floor`);
}
for(const event of CAMPAIGN_EVENT_LIST){
 expect(AREAS[event.area]?.objects.some(object=>object.eventId===event.id),`${event.id} lacks a physical action`);
 expect(!event.experienceEvent||MAIN_XP_EVENTS.some(xp=>xp.id===event.experienceEvent),`${event.id} uses an unknown main XP event`);
 for(const id of [...(event.items??[]),...(event.choiceItems??[])])expect(!!EQUIPMENT[id],`${event.id} grants an undefined/retired item ${id}`);
}
const results=resolve(__dirname,'../../src/cocos/test-results');mkdirSync(results,{recursive:true});
const resources=resolve(__dirname,'../../src/cocos/assets/resources'),art=JSON.parse(readFileSync(resolve(resources,'equipment/v3/manifest.json'),'utf8')),hero=JSON.parse(readFileSync(resolve(resources,'flat2d/characters/raphael/manifest.json'),'utf8'));
const campaignIconPath=resolve(resources,'equipment/campaign-v1/index.json'),campaignIcons=existsSync(campaignIconPath)?JSON.parse(readFileSync(campaignIconPath,'utf8')).icons:{};
const mappedEquipment=new Set<string>([...(Object.values(art.items)as {existingIds?:string[]}[]).flatMap(item=>item.existingIds??[]),...Object.keys(campaignIcons)]),weapons=Object.values(EQUIPMENT).filter(item=>item.slot==='weapon');
const unimplementedPresentation=[
 {kind:'dedicated-npc-art',ids:['severin','elise'],areas:['H02','B03'],status:'Named research/appraisal stations keep their independent merchant accounts usable. No absent actor is loaded and no other person artwork is borrowed.'},
 {kind:'enemy-and-boss-art',authoredCommonArchetypes:24,authoredBosses:12,retainedIndependentIdentities:['R1-1','R1-2','R1-3','BOSS_R1'],currentlyUsedActorArt:['raider','raider-shield','raider-archer','captain','mine-crawler','mine-worker'],independent2DPilotsInstalled:[{template:'R2-3',conceptId:'mine-crawler',runtimeAtlas:[1024,1024],runtimePlayReview:'pending'},{template:'R2-1',conceptId:'mine-worker',runtimeAtlas:[1024,1024],runtimePlayReview:'pending'}],remainingRuntimeIndependent2DIdentities:30,remainingUngeneratedIdentities:30,remainingNative3DIdentities:32,status:'Four original independent actors are retained. R2-3 mine-crawler and R2-1 mine-worker have independent four-view2D pilots, source1536/runtime1024, corrected support-plane pivots and reviewed static identity/contact sheets, awaiting actual game gait/turn/collision acceptance. R2-1 edited side legs preserve the original upper bodies and other14 cells. The other30 runtime identities still reuse legacy human artwork; distinct art/animation and native3D have not been completed.'},
 {kind:'campaign-mechanism-presentation',actions:CAMPAIGN_EVENT_LIST.length,status:'Physical interaction points and persistent rule outcomes exist. campaign_event objects currently reuse SceneBuilder paper/book/candle props; distinct bridge winch, pressure valve, mirror bank, tower dismantling and core-operation models/animations still require implementation and visual review.'},
 {kind:'expanded-location-art',newScenes:65,totalScenes:97,status:'All locations have terrain-family assignments, named landmarks, collision and walking connections. The 65 added scenes reuse common landmark construction; individual scene composition, unique interiors, machinery and all 97 rendered paths have not been visually accepted.'},
 {kind:'equipment-art-coverage',dedicatedMapped:Object.keys(EQUIPMENT).filter(id=>mappedEquipment.has(id)).length,reviewedCloudPlateIcons:Object.keys(campaignIcons).length,fallbackIds:Object.keys(EQUIPMENT).filter(id=>!mappedEquipment.has(id)),status:'Existing v3 art has priority; 49 reviewed transparent icons are deterministic crops from explicit cloud plate mappings. Remaining equipment keeps category/slot fallback. Inventory icons do not count as held/wearable artwork or animation.'},
 {kind:'equipped-weapon-poses',exactIdlePoses:weapons.filter(item=>hero.actions[`idle_${item.id}`]).map(item=>item.id),familyPoseIds:weapons.filter(item=>!hero.actions[`idle_${item.id}`]).map(item=>item.id),status:'Unmapped weapon IDs require shared family poses. Unique held/stowed silhouettes and complete action sets are not yet available for every permanent weapon.'},
];
const missingActorManifests=Object.values(AREAS).flatMap(area=>area.objects.filter(object=>object.actor&&!existsSync(resolve(resources,`flat2d/characters/${object.actor}/manifest.json`))).map(object=>({area:area.id,actor:object.actor})));
expect(missingActorManifests.length===0,`Scene references absent character manifests: ${JSON.stringify(missingActorManifests)}`);
writeFileSync(resolve(results,'campaign-content-validation.json'),JSON.stringify({status:problems.length?'failed':'passed',scope:'generated data, authored walking graph, collider approaches and return entries',areas:Object.keys(AREAS).length,connectedAreas:reachable.size,equipment:Object.keys(EQUIPMENT).length,skills:COMBAT_SKILL_LIST.length,ranks:COMBAT_SKILL_LIST.reduce((sum,skill)=>sum+skill.ranks.length,0),commonArchetypes:CAMPAIGN_COMMON_ENEMIES.length,bosses:CAMPAIGN_BOSSES.length,physicalCampaignActions:CAMPAIGN_EVENT_LIST.length,missingActorManifests,problems,unimplementedPresentation,artAcceptance:'Not accepted: the checks above validate content and navigation, not complete rendered gameplay or art delivery.'},null,2));
if(problems.length)throw new Error(`Runtime content validation failed:\n${problems.join('\n')}`);
mkdirSync(target,{recursive:true});
writeFileSync(resolve(target,'runtime-content.json'),JSON.stringify({areas:AREAS,equipment:EQUIPMENT,skills:COMBAT_SKILL_LIST,campaignEvents:CAMPAIGN_EVENT_LIST},null,2));
console.log(`${Object.keys(AREAS).length} connected areas, ${Object.keys(EQUIPMENT).length} permanent items, 30 skills / 150 ranks, 12 placed bosses; walking/collision checks passed`);
