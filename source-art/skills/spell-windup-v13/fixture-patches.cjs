// Adapt the existing recording fixture through real session inputs only.
// There are no replacement gameplay / renderer modules or manufactured hits.
exports.prepare=function prepare(source){
 function change(before,after){if(source.split(before).length!==2)throw Error('Recording fixture changed near '+before.slice(0,90));source=source.replace(before,()=>after);}
 change('+.13;','+.67;');
 change('state.progression.learned[def.id]=def.rank??1;','state.progression.learned[def.id]=def.rank??1;for(const [id,rank]of Object.entries(def.levels??{}))state.progression.learned[id]=rank;');
 change('state.combat.passiveSlots=[null,null];','state.combat.passiveSlots=def.passives??[null,null];');
 change('targetPoint={x:targets[0].x,z:targets[0].z};','targetPoint=def.aim?point(origin,...def.aim):{x:targets[0].x,z:targets[0].z};');
 change('const result=session.castSkill(shot.id,targetPoint,angle);','const result=session.castSkill(shot.triggerId??shot.id,targetPoint,Math.atan2(targetPoint.x-player.x,targetPoint.z-player.z));');
 change("tick({attack:shot.id==='BASIC_WAR'&&time>=start&&time<start+.92});", "const drive=globalThis.thunderFamilyDrive?.(shot,time,sub,player,state)??{};tick({...drive,attack:drive.attack??(shot.id==='BASIC_WAR'&&time>=start&&time<start+.92)});");
 change('app.actors.update(session,dt,false,false);','app.actors.update(session,dt,Math.hypot(input.x??0,input.z??0)>.01,false);');
 change('targets:[...cast.targets]','targets:[...cast.targets],procs:[...cast.procs]');
 change("['skill_cast','skill_release','skill_segment','skill_hit','miss','hit']","['skill_cast','skill_release','skill_segment','skill_hit','skill_status','miss','hit','hurt','attack']");
 // Reset the renderer's contact hold when the disposable fixture rewinds its
 // session clock. This is a presentation reset, not a gameplay hit or cast.
 change('frame=0;events=[];logicEvents=[];castSnapshots=[];',"frame=0;events=[];logicEvents=[];castSnapshots=[];app.actors.onCombatEvents([{type:'area'}],state.time);");
 return source;
};
