const {validateSample}=require('./metrics.cjs');
function validateFarmSample(sample,seconds,performanceGates=true){
 const errors=validateSample(sample,seconds,performanceGates),n=sample.nativeHunt;
 if(!['auto-hunt','move-combat'].includes(sample.mode)||!n||n.frames!==sample.frameCount||!Number.isInteger(n.movingFrames)||!Number.isInteger(n.activeFrames)||n.movingFrames<0||n.movingFrames>n.activeFrames||n.activeFrames>n.frames)errors.push('invalid native hunting movement/action coverage');
 if(sample.mode==='move-combat'&&n?.movingFrames<sample.frameCount*.5)errors.push('insufficient actual moving-hunt movement coverage');
 if(n?.activeFrames<sample.frameCount*.2)errors.push('insufficient native attack-or-movement activity');
 if((sample.events.hit||0)+(sample.events.skill_hit||0)<1)errors.push('no actual damage/hit events');
 if((sample.events.action||0)+(sample.events.skill_release||0)<1)errors.push('no attack/release events');
 if(!(sample.events.skill_release>0))errors.push('no skill release events');
 if(!(sample.events.defeat>0))errors.push('native automation did not defeat an enemy');
 if(!(sample.events.enemy_respawn>0))errors.push('no natural enemy respawn observed');
 if(sample.family==='BOW'&&!(sample.events.projectile>0||sample.events.skill_release>0))errors.push('bow never released');
 return errors;
}
module.exports={validateFarmSample};
