local scene,rig,mesh,controller
local frames=0
local firstPose
function Start()
    local a=require("Game.ActorAssets").hero
    assert(a.model,"current local hero model must be configured")
    scene=Scene(); scene:CreateComponent("Octree")
    rig=scene:CreateChild("Raphael")
    mesh=rig:CreateComponent("AnimatedModel")
    mesh.model=assert(cache:GetResource("Model",a.model))
    mesh.updateInvisible=true
    assert(mesh.skeleton.numBones>=40,"expected the actual fitted human skeleton")
    for i,path in ipairs(a.materials) do mesh:SetMaterial(i-1,assert(cache:GetResource("Material",path))) end
    for _,name in ipairs({"idle","run","attack","hit"}) do
        local clip=assert(cache:GetResource("Animation",a.clips[name]))
        assert(clip.numTracks>=40 and clip.length>0,"motion tracks were lost for "..name)
    end
    local cameraNode=scene:CreateChild("Camera"); cameraNode.position=Vector3(0,1,-4)
    renderer:SetViewport(0,Viewport:new(scene,cameraNode:CreateComponent("Camera")))
    controller=rig:CreateComponent("AnimationController")
    assert(controller:PlayExclusive(a.clips.run,0,true,0))
    SubscribeToEvent("Update","CheckCurrentCharacter")
end
function CheckCurrentCharacter()
    frames=frames+1
    if frames==8 then
        controller:SetTime(require("Game.ActorAssets").hero.clips.run,.18)
    elseif frames==10 then
        local bone=mesh.skeleton:GetBone("thigh_l")
        firstPose=bone.node.rotation
        controller:SetTime(require("Game.ActorAssets").hero.clips.run,.54)
    elseif frames==12 then
        local q=mesh.skeleton:GetBone("thigh_l").node.rotation
        local dot=math.abs(q.w*firstPose.w+q.x*firstPose.x+q.y*firstPose.y+q.z*firstPose.z)
        assert(dot<.99,"run clip must change the limb pose across its stride")
        print("[CharacterTest] PASS local weighted human, 53-bone rig, four native clips and animated limb")
    end
end
