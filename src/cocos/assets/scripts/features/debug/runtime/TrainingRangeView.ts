import {Color,Material,MeshRenderer,Node,Vec3,primitives,utils} from 'cc';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import type {Hud} from '../../../app/Hud';
import {TrainingRange,type TargetFormation} from '../common/TrainingRange';
import {trainingText as tr} from '../locales';

/** Batched floor markings; ownership follows SceneBuilder's existing disposal. */
export function buildTrainingFloor(world:SceneBuilder){
 const positions:number[]=[],indices:number[]=[],normals:number[]=[];
 const rectangle=(x:number,z:number,w:number,d:number)=>{const i=positions.length/3;positions.push(x-w/2,.018,z-d/2,x+w/2,.018,z-d/2,x-w/2,.018,z+d/2,x+w/2,.018,z+d/2);normals.push(0,1,0,0,1,0,0,1,0,0,1,0);indices.push(i,i+2,i+1,i+1,i+2,i+3);};
 for(let n=-24;n<=24;n+=2){rectangle(n,0,.024,48);rectangle(0,n,48,.024);}
 const grid=utils.createMesh({positions,indices,normals},undefined,{calculateBounds:true}),material=new Material();material.initialize({effectName:'builtin-unlit'});material.setProperty('mainColor',new Color(102,111,108));
 const root=new Node('TrainingMetreGrid');world.root.addChild(root);const renderer=root.addComponent(MeshRenderer);renderer.mesh=grid;renderer.setMaterial(material,0);world.generatedMeshes.add(grid);world.materials.set('TrainingGrid',material);
 const disc=utils.createMesh(primitives.cylinder(.32,.32,.025,{radialSegments:24})),start=new Node('TrainingStart');world.root.addChild(start);start.setPosition(new Vec3(0,.025,-8));const marker=start.addComponent(MeshRenderer);marker.mesh=disc;marker.setMaterial(material,0);world.generatedMeshes.add(disc);
 // The arena uses a neutral solid floor so fire/lightning silhouettes stay readable.
 const floor=new Material();floor.initialize({effectName:'builtin-unlit'});floor.setProperty('mainColor',new Color(47,53,52));world.materials.set('TrainingFloor',floor);
 for(const surface of world.flatMapSurfaces)surface.setMaterial(floor,0);
}

export function renderTrainingRange(hud:Hud,range:TrainingRange){
 const formations:TargetFormation[]=['horde','single','cluster','line'];
 hud.showList(tr('title'),'',[
  {label:tr('skills'),detail:tr('skillsSummary'),action:'skill-effect-debug'},
  {label:tr(range.groupMode?'newWave':'reset'),detail:tr(range.groupMode?'newWaveDetail':'resetDetail'),action:'training:reset'},
  ...formations.map(id=>({label:tr('formation.'+id),detail:id==='horde'?tr('groupDetail'):'',value:range.formation===id?tr('selected'):undefined,action:'training:formation:'+id,selected:range.formation===id})),
  ...(range.groupMode?[{label:tr('monsterCount'),detail:tr('monsterCountValue',{count:range.monsterCount}),action:'training:monster-count'}]:[]),
  {label:tr('distance'),detail:tr('distanceValue',{metres:range.distance}),action:'training:distance'},
  ...(!range.groupMode?[{label:tr('retaliate'),detail:tr(range.retaliate?'retaliateOn':'retaliateOff'),action:'training:retaliate'}]:[]),
  {label:tr('injure'),detail:tr('injureDetail'),action:'training:injure'},
  {label:tr('resource'),detail:tr(range.unlimitedResource?'unlimited':'normal'),action:'training:resource'},
  {label:tr('report'),detail:(range.groupMode?tr('groupStats',{remaining:range.remainingMonsters,total:range.targetCount,defeated:range.defeatedMonsters})+'\n':'')+tr('stats',{damage:range.damage,hits:range.hits,misses:range.misses,criticals:range.criticalHits,dps:Math.round(range.dps),seconds:range.elapsed.toFixed(1)}),action:'training:report'},
 ],[{label:tr('exit'),action:'training:exit'},{label:tr('resume'),action:'close'}],hud.touchTargetSize,{placement:'right',width:Math.min(hud.width-48,620)});
}
