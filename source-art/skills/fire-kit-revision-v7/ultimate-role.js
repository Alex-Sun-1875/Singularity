// Review loadout only; ordinary skill damage, targets, footprints and ticks stay their own.
window.applyFireUltimateRole=function(catalog,loadouts){
  const meteor=catalog.FIR_02,sea=catalog.FIR_05;
  if(loadouts.FIR.ultimate!==meteor.id){
    const slot=loadouts.FIR.activeSlots.indexOf(meteor.id);
    if(slot<0)throw Error('Meteor is missing from the current fire loadout');
    loadouts.FIR.activeSlots[slot]=sea.id;loadouts.FIR.ultimate=meteor.id;
    for(const name of ['type','ultimateCost','sharedUltimateLockSeconds'])[meteor[name],sea[name]]=[sea[name],meteor[name]];
    for(let i=0;i<meteor.ranks.length;i++)[meteor.ranks[i].cooldownSeconds,sea.ranks[i].cooldownSeconds]=[sea.ranks[i].cooldownSeconds,meteor.ranks[i].cooldownSeconds];
  }
  meteor.windupSeconds=.85;meteor.releaseCommitSeconds=.85;meteor.recoverySeconds=.32;
  window.applyFireKitReview=function(mode){
    const enlarged=mode!=='previous';
    for(const r of meteor.ranks){const radius=enlarged?[3.8,4.2,4.6,5.0,5.5][r.rank-1]:[2.8,3.2,3.6,4.0,4.5][r.rank-1];r.radiusMetres=radius;r.geometry.radiusMetres=radius;}
    const field=catalog.FIR_05;field.name='焚焰火域';
    for(const r of field.ranks){r.geometry={kind:'filledWaveRectangle',origin:'aimPoint',widthMetres:6,depthMetres:3};}
    const jet=catalog.FIR_04;jet.name='烈焰喷流';jet.windupSeconds=.25;jet.releaseCommitSeconds=.25;jet.recoverySeconds=1.65;
    // Existing cast is an animation carrier only. New skill damage/slow rules are not implemented here.
    for(const r of jet.ranks){r.geometry={kind:'instantCorridor',origin:'caster',lengthMetres:7,widthMetres:1.8,totalTargetLimit:0};r.targetLimit=0;r.maxDamagePerTargetS=0;r.breakPower=0;r.slowPercent=0;r.zoneDurationSeconds=1.45;}
    window.fireKitReview=true;window.fireKitRadius=meteor.ranks[0].radiusMetres;
  };
  window.fireUltimateReview={ultimate:meteor.id,activeSlots:[...loadouts.FIR.activeSlots],windup:.85,ordinaryDamageAndGeometry:true};
};
