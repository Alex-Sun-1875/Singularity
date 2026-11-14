function Start()
    local scene=Scene()
    scene:CreateComponent("Octree")
    local lights=scene:CreateChild("LightGroup")
    local file=assert(cache:GetResource("XMLFile","LightGroup/Daytime.xml"))
    lights:LoadXML(file:GetRoot())
    local zone=lights:GetComponent("Zone",true)
    zone.depthFogStart=35; zone.depthFogEnd=80
    local sun=lights:GetComponent("Light",true)
    sun.castShadows=true
    sun.brightness=2.2
    require("Game.Environment").New(scene,"road")
    local node=scene:CreateChild("Camera")
    node.position=Vector3(-5,15,-13)
    node:LookAt(Vector3(-5,0,1),Vector3.UP)
    local camera=node:CreateComponent("Camera")
    camera.orthographic=true; camera.orthoSize=19; camera.farClip=90
    renderer:SetViewport(0,Viewport:new(scene,camera))
    renderer.hdrRendering=true
    renderer.drawShadows=true
    renderer.shadowMapSize=2048
    print("[EnvironmentTest] 3D scene ready; no placeholder characters instantiated")
end
