"""Generate an isolated two-bone fixture for the real Runtime, not a game actor."""
from pathlib import Path
from native_export import write_model,write_animation

root=Path(__file__).resolve().parents[2]/'src/.tmp/skin-probe'
(root/'assets').mkdir(parents=True,exist_ok=True)
(root/'scripts').mkdir(exist_ok=True)
identity=[1,0,0,0,0,1,0,0,0,0,1,0]
bones=[dict(name='Root',parent=0,p=[0,0,0],q=[1,0,0,0],s=[1,1,1],offset=identity,bounds=[-1,-1,-1,1,1,1]),
       dict(name='Arm',parent=0,p=[0,0.5,0],q=[1,0,0,0],s=[1,1,1],offset=[1,0,0,0,0,1,0,-0.5,0,0,1,0],bounds=[-1,-1,-1,1,1,1])]
vertices=[dict(p=[x,y,0],n=[0,0,1],uv=[x+0.2,y],j=[joint,0,0,0],w=[1,0,0,0]) for x,y,joint in [(-0.2,0,0),(0.2,0,0),(-0.2,1,1),(0.2,1,1)]]
write_model(root/'assets/Probe.mdl',dict(vertices=vertices,indices=[0,1,2,2,1,3],geometries=[dict(start=0,count=6)],bones=bones))
write_animation(root/'assets/Probe.ani','Probe',1,[dict(name='Arm',keys=[dict(time=0,p=[0,0.5,0],q=[1,0,0,0],s=[1,1,1]),dict(time=1,p=[0,0.5,0],q=[0.70710678,0,0,0.70710678],s=[1,1,1])])])
(root/'scripts/main.lua').write_text('''local scene,mesh,controller
local frames=0
function Start()
 scene=Scene(); scene:CreateComponent("Octree")
 local node=scene:CreateChild("Probe")
 mesh=node:CreateComponent("AnimatedModel")
 mesh.model=assert(cache:GetResource("Model","Probe.mdl"))
 mesh.updateInvisible=true
 local material=Material:new()
 material:SetTechnique(0,cache:GetResource("Technique","Techniques/NoTextureUnlit.xml"))
 material:SetShaderParameter("MatDiffColor",Variant(Color(0.8,0.8,0.8)))
 mesh:SetMaterial(material)
 local cam=scene:CreateChild("Camera")
 cam.position=Vector3(0,0.5,-3); cam:LookAt(Vector3(0,0.5,0),Vector3.UP)
 renderer:SetViewport(0,Viewport:new(scene,cam:CreateComponent("Camera")))
 assert(mesh.skeleton.numBones==2,"bone data did not survive native export")
 local animation=assert(cache:GetResource("Animation","Probe.ani"))
 assert(animation.numTracks==1 and math.abs(animation.length-1)<0.001)
 controller=node:CreateComponent("AnimationController")
 assert(controller:PlayExclusive("Probe.ani",0,true,0))
 SubscribeToEvent("Update","CheckSkinning")
end
function CheckSkinning()
 frames=frames+1
 if frames==8 then
  controller:SetTime("Probe.ani",0.5)
 elseif frames==10 then
  local bone=mesh.skeleton:GetBone("Arm")
  assert(math.abs(bone.node.rotation.z)>0.1,"bone rotation never animated")
  print("[SkinningTest] PASS native mesh, 2 bones, animation tracks and moving joint")
 end
end
''',encoding='utf-8')
print(root)
