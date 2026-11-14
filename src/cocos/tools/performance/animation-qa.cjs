/* Actual Cocos sampler outputs, checked against the full imported clips. */
module.exports=async function verifyAnimation({requireMasked=false}={}){
 const {cc,app}=__perf,layer=app.actors.player?.combatLocomotion;
 if(!layer)throw Error('No 3D player locomotion sampler to verify');
 const manager=cc.director.getSystem('animation'),paused=cc.director.isPaused(),rows=[];
 if(!manager)throw Error('AnimationManager is unavailable');
 const pathOf=(node,root)=>{const path=[];for(let n=node;n&&n!==root;n=n.parent)path.unshift(n.name);return path.join('/');};
 const pose=(root,paths)=>paths.map(path=>{const node=path?root.getChildByPath(path):root;return [node.position.x,node.position.y,node.position.z,node.rotation.x,node.rotation.y,node.rotation.z,node.rotation.w];});
 // Introspection is diagnostic only; the production sampler uses public initialize().
 const bindings=state=>{const e=state._clipEval;return (e?._trackEvalStatues?.length??0)+(e?._exoticAnimationEvaluator?._nodeEvaluations??[]).reduce((n,v)=>n+['_position','_rotation','_scale'].filter(k=>!!v[k]).length,0);};
 cc.director.pause();
 try{for(const kind of ['walk','run','brace']){
  const source=kind==='brace'?layer.braceRoot:layer.sampleRoot,state=kind==='brace'?layer.staffBrace:layer.samples[kind],joints=kind==='brace'?layer.braceJoints:layer.joints;
  if(!source||!state){if(kind==='brace')continue;throw Error('Missing stride sampler: '+kind);}
  const paths=joints.map(j=>pathOf(j.sample,source)),kept=new Set(paths),left=cc.instantiate(source),right=cc.instantiate(source),mask={joints:[]};
  const visit=(node,path='')=>{if(!kept.has(path))mask.joints.push({path,enabled:false});for(const child of node.children)visit(child,path?path+'/'+child.name:child.name);};visit(right);
  const full=new cc.AnimationState(state.clip),filtered=new cc.AnimationState(state.clip),savedTime=state.time;
  try{
   full.initialize(left);filtered.initialize(right,undefined,mask);full.wrapMode=filtered.wrapMode=cc.AnimationClip.WrapMode.Loop;
   const samples=kind==='brace'?32:160;let maxError=0,maxVariation=0,first;
   for(let i=0;i<samples;i++){
    full.time=filtered.time=state.time=state.clip.duration*i/samples;full.sample();filtered.sample();state.sample();manager.update(0);
    const expected=pose(left,paths),masked=pose(right,paths),actual=pose(source,paths);first??=expected;
    for(let j=0;j<expected.length;j++)for(let k=0;k<7;k++){maxError=Math.max(maxError,Math.abs(expected[j][k]-masked[j][k]),Math.abs(expected[j][k]-actual[j][k]));maxVariation=Math.max(maxVariation,Math.abs(expected[j][k]-first[j][k]));}
   }
   const row={kind,samples,joints:paths.length,fullBindings:bindings(full),maskedBindings:bindings(filtered),actualBindings:bindings(state),maxError,maxVariation};rows.push(row);
   if(maxError!==0||!(row.fullBindings>row.maskedBindings&&row.maskedBindings>0)||kind!=='brace'&&maxVariation===0)throw Error('Invalid sampler pose/binding coverage: '+JSON.stringify(row));
   if(requireMasked&&row.actualBindings!==row.maskedBindings)throw Error('Unused animation curves are still bound: '+JSON.stringify(row));
  }finally{state.time=savedTime;full.destroy();filtered.destroy();left.destroy();right.destroy();}
 }}finally{if(!paused)cc.director.resume();}
 return {status:'passed',scope:'Consumed auxiliary joints only; main action skeleton and gameplay are untouched',samples:rows.reduce((n,row)=>n+row.samples,0),rows};
};
