// Isolated review-session tuning. Rendering and collision both read these live catalog objects.
window.applyStudyDimensions = function applyStudyDimensions(basic, catalog, loadouts) {
  Object.assign(basic.sword, {rangeMetres: 2.65, angleDegrees: 48});
  function narrowFan(id, factor, firstAngle, angleGrowth) {
    for (const rank of catalog[id].ranks) {
      const reach = Math.round(rank.geometry.radiusMetres * factor * 100) / 100;
      Object.assign(rank, {rangeMetres:reach,castRangeMetres:reach,radiusMetres:reach});
      Object.assign(rank.geometry, {radiusMetres:reach,angleDegrees:firstAngle+(rank.rank-1)*angleGrowth});
    }
  }
  narrowFan('WAR_01',1.25,40,2);
  narrowFan('WAR_05',1.15,62,2);
  const meteor = catalog.FIR_02, sea = catalog.FIR_05;
  // Keep each spell's own damage events and geometry; exchange their slot and cost roles.
  const ultimateSlot=loadouts.FIR.activeSlots.indexOf(meteor.id);
  if(ultimateSlot<0)throw Error('The current fire skill slots differ from the review baseline');
  loadouts.FIR.activeSlots[ultimateSlot]=sea.id;
  loadouts.FIR.ultimate=meteor.id;
  for(const name of ['type','ultimateCost','sharedUltimateLockSeconds']){
    [meteor[name],sea[name]]=[sea[name],meteor[name]];
  }
  for(let i=0;i<meteor.ranks.length;i++){
    [meteor.ranks[i].cooldownSeconds,sea.ranks[i].cooldownSeconds]=[sea.ranks[i].cooldownSeconds,meteor.ranks[i].cooldownSeconds];
  }
  meteor.windupSeconds=.78;
  meteor.releaseCommitSeconds=.78;
  meteor.recoverySeconds=.32;
};
