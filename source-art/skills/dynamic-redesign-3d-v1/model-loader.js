// Standalone design-preview adapter. Reads current production 3D assets; never mutates Cocos files.
import { GLTFLoader } from '../../../src/cocos/node_modules/three/examples/jsm/loaders/GLTFLoader.js';
import { FBXLoader } from '../../../src/cocos/node_modules/three/examples/jsm/loaders/FBXLoader.js';
import * as SkeletonUtils from '../../../src/cocos/node_modules/three/examples/jsm/utils/SkeletonUtils.js';
import { ACTOR_METADATA } from './references/actor-metadata.js';

const ROOT = new URL('../../../', document.baseURI);
const resource = path => new URL('src/cocos/assets/resources/' + path, ROOT).href;
const project = path => new URL(path, ROOT).href;
const clamp = (n,a,b) => Math.min(b, Math.max(a,n));

export async function loadActors(THREE, scene) {
  const gltf = new GLTFLoader();
  const textureLoader = new THREE.TextureLoader();
  const textureCache = new Map();
  const warnings = [];
  const metadata = {
    mode: 'true-3D skeletal standalone design preview',
    heroSource: 'src/cocos/assets/resources/actors/raphael/raphael-polish.glb',
    heroManifest: 'src/cocos/assets/resources/actors/raphael/manifest.json',
    locomotionRevision: ACTOR_METADATA.hero.locomotionRevision,
    appearanceRevision: ACTOR_METADATA.hero.appearanceRevision,
    hair: 'src/cocos/assets/resources/actors/raphael/hair-curly.glb',
    weapons: {WAR:'W01',BOW:'W07',FIR:'W11',THU:'W11'},
    clips: [], warnings,
    scope: 'Design preview only. No game source, damage geometry, resources or saves changed.'
  };
  async function texture(path, actorId, color, fbx = false) {
    if (!path) return null;
    const url = new URL(path, resource('actors/' + actorId + '/')).href;
    const key = url + ':' + color + ':' + fbx;
    if (!textureCache.has(key)) textureCache.set(key, textureLoader.loadAsync(url).then(t => {
      t.flipY = fbx;
      t.colorSpace = color ? THREE.SRGBColorSpace : THREE.NoColorSpace;
      t.anisotropy = 4;
      return t;
    }));
    return textureCache.get(key);
  }
  async function applyMaterials(model, actorId, actorMeta, fbx = false) {
    const records = new Map(actorMeta.materials.map(r => [r.runtimeName,r]));
    const pending = [];
    model.traverse(node => {
      if (!node.isMesh) return;
      node.castShadow = true; node.receiveShadow = true; node.frustumCulled = false;
      const input = Array.isArray(node.material) ? node.material : [node.material];
      pending.push(Promise.all(input.map(async old => {
        const record = records.get(old.name) || records.get(old.name.replace(/-NativePBR$/, '')) || [...records.values()].find(r => r.runtimeName.replace(/\./g,'_') === old.name);
        if (!record) return old;
        const [albedo,normal,orm,rough] = await Promise.all([
          texture(record.maps.albedo,actorId,true,fbx),texture(record.maps.normal,actorId,false,fbx),
          texture(record.maps.orm,actorId,false,fbx),texture(record.maps.roughness,actorId,false,fbx)
        ]);
        const factors = record.sourcePBR?.effectiveFactors || {};
        const material = new THREE.MeshStandardMaterial({
          name:record.runtimeName + '-DesignPBR', color:0xffffff,
          map:albedo, normalMap:normal,
          roughnessMap:orm || rough, metalnessMap:orm,
          roughness:factors.roughness ?? (orm || rough ? 1 : record.sourcePBR?.roughness ?? .7),
          metalness:factors.metallic ?? (orm ? 1 : record.sourcePBR?.metallic ?? 0),
          side:record.doubleSided ? THREE.DoubleSide : THREE.FrontSide,
          alphaTest:record.alphaClip ? record.alphaThreshold ?? .32 : 0
        });
        // Three uses glTF ORM G/B channels; the existing standalone roughness PNG is grayscale.
        if (node.geometry.attributes.uv && !node.geometry.attributes.uv2) node.geometry.setAttribute('uv2',node.geometry.attributes.uv);
        if (orm) { material.aoMap = orm; material.aoMapIntensity = 1; }
        return material;
      })).then(materials => { node.material = Array.isArray(node.material) ? materials : materials[0]; }));
    });
    await Promise.all(pending);
    for (const [part,def] of Object.entries(actorMeta.parts || {})) if (def.defaultVisible === false || actorMeta.defaultHiddenParts?.includes(part)) {
      for (const name of def.nodes || []) { const node = model.getObjectByName(name); if (node) node.visible = false; }
    }
    model.traverse(node => { if (node.name.toLowerCase().startsWith('equipped')) node.visible = false; });
  }

  const [heroGLTF,hairGLTF,swordGLTF,bowGLTF,staffGLTF,comboGLTF] = await Promise.all([
    gltf.loadAsync(resource('actors/raphael/raphael-polish.glb')),
    gltf.loadAsync(resource('actors/raphael/hair-curly.glb')),
    gltf.loadAsync(project('source-art/weapons/3d-design-v1/glb/W01.glb')),
    gltf.loadAsync(project('source-art/weapons/3d-design-v1/glb/W07.glb')),
    gltf.loadAsync(project('source-art/weapons/3d-design-v1/glb/W11.glb')),
    gltf.loadAsync(resource('actors/player-melee-combo/combos-native.glb'))
  ]);
  const heroClips = [...heroGLTF.animations,...comboGLTF.animations.filter(c => !heroGLTF.animations.some(existing => existing.name===c.name))];
  metadata.comboSource = 'src/cocos/assets/resources/actors/player-melee-combo/combos-native.glb';
  swordGLTF.scene.updateMatrixWorld(true);
  const swordBounds = new THREE.Box3().setFromObject(swordGLTF.scene);
  const swordTipLocal = new THREE.Vector3((swordBounds.min.x+swordBounds.max.x)/2,swordBounds.max.y,(swordBounds.min.z+swordBounds.max.z)/2);
  const swordBaseLocal = new THREE.Vector3(0,0,0);
  metadata.weaponAnchors = {source:'Unparented current W01 GLB local bounds and authored grip origin',tip:swordTipLocal.toArray(),base:swordBaseLocal.toArray(),axis:'+Y'};
  const hero = new THREE.Group(); hero.name = 'Current3DHero'; scene.add(hero);
  const heroModel = heroGLTF.scene; hero.add(heroModel);
  await applyMaterials(heroModel,'raphael',ACTOR_METADATA.hero);

  // The separately streamed current curly hairstyle has the same native 67-bone rig.
  // Rebind its actual skinned mesh to the animated hero bones rather than rendering a second rig.
  const bones = new Map(); heroModel.traverse(n => { if (n.isBone) bones.set(n.name,n); });
  const heroRig = heroModel.getObjectByName('raphael_Native65') || heroModel;
  const hairMeshes = []; hairGLTF.scene.traverse(n => { if (n.isSkinnedMesh) hairMeshes.push(n); });
  for (const mesh of hairMeshes) {
    const mapped = mesh.skeleton.bones.map(b => bones.get(b.name));
    if (mapped.some(b => !b)) throw new Error('Current curly hair bone mismatch');
    const skeleton = new THREE.Skeleton(mapped,mesh.skeleton.boneInverses.map(m => m.clone()));
    mesh.removeFromParent(); heroRig.add(mesh); mesh.bind(skeleton,mesh.bindMatrix.clone());
    mesh.frustumCulled = false;
  }
  await applyMaterials(heroModel,'raphael',ACTOR_METADATA.hero);

  function handGrip(model,side,name) {
    const hand = model.getObjectByName('hand_' + side);
    if (!hand) throw new Error('Missing true 3D hand socket ' + side);
    const index = hand.getObjectByName('index_01_' + side), pinky = hand.getObjectByName('pinky_01_' + side);
    const group = new THREE.Group(); group.name = name; hand.add(group);
    if (index && pinky) {
      group.position.copy(index.position).add(pinky.position).multiplyScalar(.5);
      const axis = index.position.clone().sub(pinky.position).normalize();
      group.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),axis);
    }
    return group;
  }
  const swordGrip = handGrip(heroModel,'r','HeldSword'); swordGrip.add(swordGLTF.scene);
  const staffGrip = handGrip(heroModel,'r','HeldStaff'); staffGrip.add(staffGLTF.scene);
  const bowGrip = new THREE.Group(); bowGrip.name = 'HeldBow';
  (heroModel.getObjectByName('attach_bow_l') || heroModel.getObjectByName('hand_l')).add(bowGrip);
  const bowEuler = ACTOR_METADATA.hero.cocosBinding?.bowEuler || [90,0,180];
  bowGrip.rotation.set(...bowEuler.map(v => v*Math.PI/180),'YXZ'); bowGrip.add(bowGLTF.scene);
  const weaponGroups = {WAR:swordGrip,BOW:bowGrip,FIR:staffGrip,THU:staffGrip};
  for (const asset of [swordGLTF.scene,bowGLTF.scene,staffGLTF.scene]) asset.traverse(n => { if (n.isMesh) { n.castShadow=true; n.receiveShadow=true; } });
  const bowMorphs=[];
  bowGLTF.scene.traverse(node => {
    const index=node.morphTargetDictionary?.Draw;
    if (index!==undefined && node.morphTargetInfluences) bowMorphs.push({node,index});
  });
  const bowMotion=ACTOR_METADATA.hero.libraryMotion?.clips?.attack_bow || {};
  const bowCalibration=ACTOR_METADATA.hero.cocosBinding?.bowDrawWeightByItem?.W07 || {scale:1,offset:0};
  const bowDuration=heroClips.find(c=>c.name==='attack_bow')?.duration || bowMotion.duration || 1.1666667;
  metadata.bowDraw={
    source:'Current production libraryMotion.clips.attack_bow.drawWeights and cocosBinding.bowDrawWeightByItem.W07',
    holdFraction:bowMotion.holdFraction ?? .7428571428571429,
    duration:bowDuration,sampleCount:bowMotion.drawWeights?.length || 0,
    calibration:bowCalibration,
    morphMeshes:bowMorphs.map(({node,index})=>({name:node.name,index}))
  };
  function sampleBowDraw(time) {
    const fraction=clamp(time/bowDuration,0,1),samples=bowMotion.drawWeights;
    const hold=bowMotion.holdFraction ?? .65;
    let weight;
    if (samples?.length) {
      const cursor=fraction*(samples.length-1),lo=Math.floor(cursor),hi=Math.min(samples.length-1,lo+1);
      weight=samples[lo]+(samples[hi]-samples[lo])*(cursor-lo);
    } else {
      const relax=bowMotion.relaxFraction ?? hold+(1-hold)/3;
      weight=fraction<=hold?fraction/hold:Math.max(0,1-(fraction-hold)/Math.max(.001,relax-hold));
    }
    const mapped=weight*bowCalibration.scale+bowCalibration.offset*(fraction<=hold?1:clamp(weight,0,1));
    const maxWeight=Math.max(1,...(samples || []).map(w=>w*bowCalibration.scale+bowCalibration.offset));
    return clamp(mapped,Math.min(0,bowCalibration.offset),maxWeight);
  }

  function makePoseDriver(group,model,clips,actorMeta) {
    const mixer = new THREE.AnimationMixer(model);
    const actions = new Map(clips.map(c => [c.name,mixer.clipAction(c)]));
    const durations = Object.fromEntries(clips.map(c => [c.name,c.duration]));
    const isHero = group===hero;
    // A separate action instance permits blending the native first-cut preparation
    // against the moving first-cut clip without resetting either action's time.
    const readyClip = isHero ? clips.find(c => c.name==='attack_sword')?.clone() : null;
    if (readyClip) readyClip.name='__design_war_native_ready';
    const warReady = readyClip ? mixer.clipAction(readyClip) : null;
    const resolve = (name,family='WAR') => {
      const aliases = {attack:family==='WAR'?'attack_sword':family==='BOW'?'attack_bow':'spell',cast:'spell',charge:'spell',dash:'dodge',hurt:'hit',rest:family==='FIR'||family==='THU'?'idle_staff':'idle'};
      let key = aliases[name] || name || 'idle';
      if (key==='idle' && (family==='FIR'||family==='THU') && actions.has('idle_staff')) key='idle_staff';
      if (actions.has(key)) return key;
      return [...actions.keys()].find(n => n.endsWith(key) || n.toLowerCase().includes(key.toLowerCase())) || 'idle';
    };
    function pose({family='WAR',action='idle',time=0,weight=1,secondaryAction,secondaryTime=0,secondaryWeight=0,position,yaw,visible=true}={}) {
      family = String(family).toUpperCase();
      if (position) {
        if (Array.isArray(position)) group.position.set(position[0],position[1]||0,position[2]||0);
        else group.position.set(position.x||0,position.y||0,position.z||0);
      }
      if (yaw !== undefined) group.rotation.y = yaw;
      group.visible = visible;
      const key=resolve(action,family), idle=resolve('idle',family);
      mixer.stopAllAction();
      let primaryWeight=clamp(weight,0,1), secondWeight=secondaryAction ? clamp(secondaryWeight,0,1) : 0;
      const total=primaryWeight+secondWeight;
      if (total>1) {primaryWeight/=total;secondWeight/=total;}
      const restingWeight=Math.max(0,1-primaryWeight-secondWeight);
      function sample(a,t,blend,loop) {
        if (!a || blend<=0) return;
        a.reset().play(); a.enabled=true; a.paused=true; a.setEffectiveWeight(blend);
        a.time=loop ? Math.max(0,t)%a.getClip().duration : clamp(t,0,Math.max(0,a.getClip().duration-.00001));
      }
      const ready=isHero&&family==='WAR'&&warReady;
      const entries=new Map();
      function queue(clipKey,t,blend) {
        if (blend<=0) return;
        const useReady=ready&&clipKey===idle;
        const a=useReady?warReady:actions.get(clipKey);
        if (!a) return;
        const at=useReady?0:t, previous=entries.get(a);
        const shortKey=clipKey.split('|').pop();
        const loop=useReady?false:actorMeta.clips[shortKey]?.loop??/^(idle|walk|run)/.test(shortKey);
        if (previous) {
          previous.time=(previous.time*previous.weight+at*blend)/(previous.weight+blend);
          previous.weight+=blend;
        } else entries.set(a,{time:at,weight:blend,loop});
      }
      queue(idle,time,restingWeight);
      queue(key,time,primaryWeight);
      if (secondaryAction) queue(resolve(secondaryAction,family),secondaryTime,secondWeight);
      if (!entries.size) queue(idle,time,1);
      for (const [a,entry] of entries) sample(a,entry.time,entry.weight,entry.loop);
      mixer.update(0); group.updateMatrixWorld(true);
      return key;
    }
    return {mixer,actions,durations,pose,resolve};
  }
  const heroDriver = makePoseDriver(hero,heroModel,heroClips,ACTOR_METADATA.hero);
  metadata.clips = heroClips.map(c => ({name:c.name,duration:c.duration}));
  metadata.socketBones = [...bones.keys()].filter(n => /hand_|attach_|Head/.test(n));
  hero.userData.sockets = {
    right:heroModel.getObjectByName('hand_r'),left:heroModel.getObjectByName('hand_l'),
    bow:heroModel.getObjectByName('attach_bow_l'),arrow:heroModel.getObjectByName('attach_arrow_r')
  };

  const enemies=[]; const enemyDrivers=[];
  try {
    const enemyModel = await new FBXLoader().loadAsync(resource('actors/raider/raider.fbx'));
    await applyMaterials(enemyModel,'raider',ACTOR_METADATA.enemy,true);
    // FBX unit normalization is confined to this read-only Three adapter.
    const bounds=new THREE.Box3().setFromObject(enemyModel),height=bounds.max.y-bounds.min.y;
    const expected=ACTOR_METADATA.enemy.geometry?.idleHeightMetres || 1.79;
    if (height>3 || height<.5) enemyModel.scale.multiplyScalar(expected/height);
    enemyModel.updateMatrixWorld(true);
    const grounded=new THREE.Box3().setFromObject(enemyModel); enemyModel.position.y-=grounded.min.y;
    const clips=enemyModel.animations || [];
    for (let i=0;i<6;i++) {
      const group=new THREE.Group();group.name='Current3DRaider_'+i;scene.add(group);
      const model=SkeletonUtils.clone(enemyModel);group.add(model);
      const grip=handGrip(model,'r','RaiderSword'), weapon=swordGLTF.scene.clone(true);grip.add(weapon);
      group.updateMatrixWorld(true);
      const physicalScale=grip.getWorldScale(new THREE.Vector3());
      // GLB weapons are metres even when an FBX bone chain retains centimetre basis.
      weapon.scale.multiplyScalar(1/Math.max(.00001,Math.abs(physicalScale.x)));
      group.visible=false;enemies.push(group);enemyDrivers.push(makePoseDriver(group,model,clips,ACTOR_METADATA.enemy));
    }
    metadata.enemy={source:'src/cocos/assets/resources/actors/raider/raider.fbx',clips:clips.map(c=>({name:c.name,duration:c.duration})),unitHeight:height};
  } catch (error) {
    warnings.push('Current raider failed: '+error.message);
    // Keep the true 3D hero review usable; never replace a failed actor with sprites.
    metadata.enemy={error:String(error),source:'actors/raider/raider.fbx'};
  }

  function setPose(options={}) {
    const family=String(options.family||'WAR').toUpperCase();
    swordGrip.visible=family==='WAR';bowGrip.visible=family==='BOW';staffGrip.visible=family==='FIR'||family==='THU';
    const sampled=heroDriver.pose({...options,family});
    let draw=0;
    if (family==='BOW') {
      let primaryWeight=clamp(options.weight ?? 1,0,1),secondaryWeight=options.secondaryAction?clamp(options.secondaryWeight ?? 0,0,1):0;
      const total=primaryWeight+secondaryWeight;
      if (total>1) {primaryWeight/=total;secondaryWeight/=total;}
      if (heroDriver.resolve(options.action || 'idle',family)==='attack_bow') draw+=sampleBowDraw(options.time || 0)*primaryWeight;
      if (options.secondaryAction && heroDriver.resolve(options.secondaryAction,family)==='attack_bow') draw+=sampleBowDraw(options.secondaryTime || 0)*secondaryWeight;
    }
    for (const {node,index} of bowMorphs) node.morphTargetInfluences[index]=draw;
    return sampled;
  }
  function setEnemyPose(index,options={}) { return enemyDrivers[index]?.pose({...options,family:'WAR'}); }
  setPose({family:'WAR',action:'idle',time:0,position:[0,0,0],yaw:Math.PI/2});
  return {hero,enemies,setPose,setEnemyPose,ready:true,metadata,clips:heroClips,heroMixer:heroDriver.mixer,
    getSocket(name){const node=hero.userData.sockets[name];return node?node.getWorldPosition(new THREE.Vector3()):hero.position.clone();},
    getWeaponTip(){swordGLTF.scene.updateWorldMatrix(true,false);return swordGLTF.scene.localToWorld(swordTipLocal.clone());},
    getWeaponBase(){swordGLTF.scene.updateWorldMatrix(true,false);return swordGLTF.scene.localToWorld(swordBaseLocal.clone());}
  };
}
