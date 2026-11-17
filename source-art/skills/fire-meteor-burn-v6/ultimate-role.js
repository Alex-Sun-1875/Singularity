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
  window.fireUltimateReview={ultimate:meteor.id,activeSlots:[...loadouts.FIR.activeSlots],windup:.85,ordinaryDamageAndGeometry:true};
};
