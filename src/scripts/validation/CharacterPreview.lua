local scene,actor,cameraNode,controller
function Start()
    scene=Scene(); scene:CreateComponent("Octree")
    local group=scene:CreateChild("LightGroup")
    group:LoadXML(cache:GetResource("XMLFile","LightGroup/Daytime.xml"):GetRoot())
    local sun=group:GetComponent("Light",true)
    sun.castShadows=true
    local zone=group:GetComponent("Zone",true)
    print("[LightingProbe]",sun.shadowIntensity,sun.brightness,zone.envTextureDiffIntensity,zone.envTextureSpecIntensity)
    local a=require("Game.ActorAssets").hero
    actor=scene:CreateChild("Raphael")
    local mesh=actor:CreateComponent("AnimatedModel")
    mesh.model=cache:GetResource("Model",a.model); mesh.castShadows=true
    for i,path in ipairs(a.materials) do mesh:SetMaterial(i-1,cache:GetResource("Material",path)) end
    controller=actor:CreateComponent("AnimationController")
    controller:PlayExclusive(a.clips.idle,0,true,0)
    local floor=scene:CreateChild("Floor"); floor.position=Vector3(0,-.06,0); floor.scale=Vector3(50,.1,50)
    local model=floor:CreateComponent("StaticModel"); model.model=cache:GetResource("Model","Models/Box.mdl")
    local mat=Material:new(); mat:SetTechnique(0,cache:GetResource("Technique","Techniques/PBR/PBRNoTexture.xml"))
    mat:SetShaderParameter("MatDiffColor",Variant(Color(.11,.15,.12))); model:SetMaterial(mat)
    cameraNode=scene:CreateChild("Camera"); cameraNode.position=Vector3(2.5,1.9,4)
    cameraNode:LookAt(Vector3(0,.95,0),Vector3.UP)
    local camera=cameraNode:CreateComponent("Camera"); camera.orthographic=true; camera.orthoSize=2.4
    renderer:SetViewport(0,Viewport:new(scene,camera)); renderer.drawShadows=true
    renderer.shadowMapSize=2048; renderer.hdrRendering=true
    CharacterPreviewState={actor=actor,controller=controller,assets=a}
end
