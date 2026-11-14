local Environment=require("Game.Environment")
local Weapons=require("Game.Weapons3D")
---@type ChapterActorAssetSet
local Assets=require("Game.ActorAssets")
---@class ChapterScene3D
---@field app table
---@field scene Scene
---@field camera Camera
---@field cameraNode Node
---@field environment ChapterEnvironment
---@field name string
---@field actors table
---@field props table
---@field transient Node[]
local Scene3D={}
Scene3D.__index=Scene3D
local function solid(r,g,b,metal,emission)
    local mat=Material:new()
    mat:SetTechnique(0,cache:GetResource("Technique","Techniques/PBR/PBRNoTexture.xml"))
    mat:SetShaderParameter("MatDiffColor",Variant(Color(r,g,b)))
    mat:SetShaderParameter("Metallic",Variant(metal or 0))
    mat:SetShaderParameter("Roughness",Variant(0.7))
    if emission then mat:SetShaderParameter("MatEmissiveColor",Variant(Color(r,g,b))) end
    return mat
end
function Scene3D.New(app)
    local self=setmetatable({app=app,scene=Scene(),actors={},props={},transient={},name=""},Scene3D)
    self.scene:CreateComponent("Octree")
    local headless=false
    for _,arg in ipairs(GetArguments()) do if arg=="-graphicsheadless" then headless=true end end
    if not headless then
        local group=self.scene:CreateChild("LightGroup")
        group:LoadXML(assert(cache:GetResource("XMLFile","LightGroup/Daytime.xml")):GetRoot())
        local sun=group:GetComponent("Light",true)
        sun.castShadows=true; sun.brightness=2.2
        local zone=group:GetComponent("Zone",true)
        zone.depthFogStart=35; zone.depthFogEnd=75
    end
    self.cameraNode=self.scene:CreateChild("ChapterCamera")
    self.camera=self.cameraNode:CreateComponent("Camera")
    self.camera.orthographic=true; self.camera.orthoSize=15.5
    self.camera.nearClip=0.1; self.camera.farClip=90
    renderer:SetViewport(0,Viewport:new(self.scene,self.camera))
    renderer.drawShadows=true; renderer.shadowMapSize=2048; renderer.hdrRendering=true
    self:Rebuild()
    self:Update(0)
    return self
end
---@param id string
---@param definition ChapterActorAsset
function Scene3D:CreateActor(id,definition)
    local hasModel=definition.model and cache:Exists(definition.model)
    local hasPrefab=definition.prefab and cache:Exists(definition.prefab)
    if not hasModel and not hasPrefab then return nil end
    local actor=self.environment.root:CreateChild(id)
    local mesh
    if hasPrefab then
        local xml=cache:GetResource("XMLFile",definition.prefab)
        if not xml or not actor:LoadXML(xml:GetRoot()) then actor:Remove(); return nil end
        mesh=actor:GetComponent("AnimatedModel",true)
    else
        local model=cache:GetResource("Model",definition.model)
        if not model then actor:Remove(); return nil end
        mesh=actor:CreateComponent("AnimatedModel")
        mesh.model=model
        for i,path in ipairs(definition.materials or {}) do
            if not cache:Exists(path) then actor:Remove(); return nil end
            local material=cache:GetResource("Material",path)
            if not material then actor:Remove(); return nil end
            mesh:SetMaterial(i-1,material)
        end
    end
    if not mesh then actor:Remove(); return nil end
    mesh.castShadows=true
    if definition.scale then actor.scale=Vector3(definition.scale,definition.scale,definition.scale) end
    local clips=definition.clips or {}
    local ready=mesh.skeleton.numBones>0
    for _,state in ipairs({"idle","run","attack","hit"}) do
        if not clips[state] or not cache:Exists(clips[state]) then ready=false end
    end
    local controller=mesh.node:GetComponent("AnimationController") or mesh.node:CreateComponent("AnimationController")
    local result={node=actor,mesh=mesh,controller=controller,clips=clips,ready=ready,state=nil,yawOffset=definition.yawOffset or 0}
    result.weapons=Weapons.New(result,definition,id~="Raphael" and id~="Mira")
    return result
end
function Scene3D:Rebuild()
    if self.environment then self.environment:Destroy() end
    self.name=self.app.game.scene
    self.environment=Environment.New(self.scene,self.name)
    self.actors={}
    self.props={}
    self.transient={}
    self.actors.player=self:CreateActor("Raphael",Assets.hero)
    if self.name=="camp" then self.actors.mira=self:CreateActor("Mira",Assets.mira) end
    for _,e in ipairs(self.app.game:Map().enemies) do self.actors[e.id]=self:CreateActor(e.id,Assets.raider) end
    local env=self.environment
    local iron=solid(0.18,0.20,0.19,0.65)
    local brass=solid(0.56,0.38,0.13,0.6)
    for _,chest in ipairs(self.app.game:Map().chests) do
        local p=Environment.ToWorld(chest.x,chest.y)
        local n=env.root:CreateChild(chest.id)
        n.position=p
        env:Shape("Coffer",env.block,Vector3(0,0.28,0),Vector3(0.8,0.5,0.52),env.mats.wood,nil,n)
        env:Shape("Lid",env.block,Vector3(0,0.53,0),Vector3(0.83,0.15,0.56),env.mats.wood,nil,n)
        for _,x in ipairs({-0.25,0.25}) do env:Shape("IronBand",env.box,Vector3(x,0.35,0),Vector3(0.05,0.55,0.57),iron,nil,n) end
        env:Shape("Lock",env.block,Vector3(0,0.39,-0.29),Vector3(0.12,0.16,0.05),brass,nil,n)
        self.props[chest.id]=n
    end
    for _,barrel in ipairs(self.app.game:Map().barrels) do
        local p=Environment.ToWorld(barrel.x,barrel.y)
        local n=env.root:CreateChild(barrel.id); n.position=p
        env:Shape("WoodCask",env.cylinder,Vector3(0,0.47,0),Vector3(0.66,0.94,0.66),env.mats.wood,nil,n)
        for _,y in ipairs({0.16,0.72}) do env:Shape("Hoop",env.cylinder,Vector3(0,y,0),Vector3(0.69,0.08,0.69),iron,nil,n) end
        self.props[barrel.id]=n
    end
    for _,gate in ipairs(self.app.game:Map().exits) do
        local p=Environment.ToWorld(gate.x,gate.y)
        for _,z in ipairs({-0.95,0.95}) do
            env:Shape("WayPost",env.block,Vector3(p.x,0.8,p.z+z),Vector3(0.17,1.6,0.17),env.mats.wood)
            env:Shape("WayMarker",env.block,Vector3(p.x,1.4,p.z+z),Vector3(0.35,0.35,0.22),brass)
        end
    end
    if self.name=="camp" then self:Campfire() end
    if self.name=="pass" then self:Wagon() end
end
function Scene3D:Campfire()
    local env=self.environment
    local p=Environment.ToWorld(230,545)
    for i=0,9 do
        local a=i*math.pi/5
        env:Shape("HearthStone",env.rock,Vector3(p.x+math.cos(a)*0.62,0.14,p.z+math.sin(a)*0.62),Vector3(0.32,0.24,0.29),env.mats.stone[i%2+1],Quaternion(i*31,0,i*14))
    end
    for i=0,2 do
        env:Shape("Firewood",env.cylinder,Vector3(p.x,0.22+i*0.08,p.z),Vector3(0.15,1.0,0.15),env.mats.wood,Quaternion(90,i*60,0))
    end
    local ember=solid(1.0,0.32,0.035,0,true)
    self.fire=env:Shape("Embers",env.rock,Vector3(p.x,0.4,p.z),Vector3(0.38,0.6,0.38),ember)
    local light=self.fire:CreateComponent("Light")
    light.lightType=LIGHT_POINT; light.range=5; light.color=Color(1,0.52,0.15); light.brightness=1.2
end
function Scene3D:Wagon()
    local env=self.environment
    local root=env.root:CreateChild("CapturedWagon")
    root.position=Environment.ToWorld(1420,405)
    env:Shape("Bed",env.block,Vector3(0,0.85,0),Vector3(1.9,0.2,2.5),env.mats.wood,nil,root)
    for i=0,5 do env:Shape("Plank",env.block,Vector3(-0.79+i*0.32,0.99,0),Vector3(0.3,0.08,2.42),env.mats.wood,nil,root) end
    for _,side in ipairs({-1,1}) do
        for _,y in ipairs({1.15,1.45}) do env:Shape("SideRail",env.block,Vector3(side*0.95,y,0),Vector3(0.1,0.22,2.6),env.mats.wood,nil,root) end
        for _,z in ipairs({-1,1}) do
            env:Shape("CornerPost",env.block,Vector3(side*0.95,1.2,z),Vector3(0.14,0.9,0.14),env.mats.wood,nil,root)
            local wheel=env:Shape("Wheel",TorusGeometry(0.46,0.065,8,24):ToModel(),Vector3(side*1.12,0.51,z),Vector3(1,1,1),env.mats.wood,Quaternion(0,90,0),root)
            for i=0,3 do
                env:Shape("Spoke",env.block,Vector3(side*1.12,0.51,z),Vector3(0.05,0.81,0.05),env.mats.wood,Quaternion(i*45,0,0),root)
            end
        end
    end
    env:Shape("RelicCoffer",env.block,Vector3(0,1.21,0.2),Vector3(0.68,0.42,0.9),solid(0.12,0.38,0.36,0.5),nil,root)
    for _,z in ipairs({-1,1}) do env:Shape("Axle",env.cylinder,Vector3(0,0.51,z),Vector3(0.12,2.2,0.12),env.mats.wood,Quaternion(0,0,90),root) end
end
function Scene3D:CharactersReady()
    if not self.actors.player or not self.actors.player.ready then return false end
    if self.name=="camp" and (not self.actors.mira or not self.actors.mira.ready) then return false end
    for _,e in ipairs(self.app.game:Map().enemies) do if not self.actors[e.id] or not self.actors[e.id].ready then return false end end
    return true
end
function Scene3D:GroundPoint(u,v)
    local ray=self.camera:GetScreenRay(u,v)
    local distance=ray:HitDistance(Plane(Vector3.UP,Vector3.ZERO))
    if distance<0 or distance>1000 then return nil end
    return Environment.ToChapter(ray.origin+ray.direction*distance)
end
function Scene3D:ScreenPoint(x,y,height)
    local p=Environment.ToWorld(x,y)
    p=Vector3(p.x,Environment.Height(p.x,p.z)+(height or 0),p.z)
    return self.camera:WorldToScreenPoint(p)
end
function Scene3D:UpdateActor(actor,state,x,y,angle,attackDuration)
    if not actor then return end
    local pos=Environment.ToWorld(x,y)
    actor.node.position=Vector3(pos.x,Environment.Height(pos.x,pos.z),pos.z)
    actor.node.rotation=Quaternion(0,90+(angle or 0)*180/math.pi+actor.yawOffset,0)
    if actor.ready and actor.state~=state then
        actor.controller:PlayExclusive(actor.clips[state],0,state=="idle" or state=="run",0.12)
        if state=="attack" then
            local animation=cache:GetResource("Animation",actor.clips[state])
            actor.controller:SetSpeed(actor.clips[state],animation.length/(attackDuration or .5))
        end
        actor.state=state
    end
end
function Scene3D:Update(_)
    local game=self.app.game
    if self.name~=game.scene then self:Rebuild() end
    local p=Environment.ToWorld(game.player.x,game.player.y)
    self.cameraNode.position=Vector3(p.x,16,p.z-12)
    self.cameraNode:LookAt(Vector3(p.x,0,p.z+1),Vector3.UP)
    local player=game.player
    local state=player.hurtTime>0 and "hit" or (player.attack>0 and "attack" or ((self.app.moving or player.dashTime>0) and "run" or "idle"))
    self:UpdateActor(self.actors.player,state,player.x,player.y,player.angle,(game.weapon=="W01" or game.weapon=="L01") and .44 or .7)
    if self.actors.player and self.actors.player.weapons then self.actors.player.weapons:Set(game.weapon) end
    self:UpdateActor(self.actors.mira,"idle",420,380,math.pi)
    for _,enemy in ipairs(game:Map().enemies) do
        local actor=self.actors[enemy.id]
        if actor then
            actor.node.enabled=enemy.hp>0
            local d=(enemy.x-player.x)^2+(enemy.y-player.y)^2
            local action=enemy.windup>0 and "attack" or (d<410^2 and d>60^2 and not game.dialogue and "run" or "idle")
            self:UpdateActor(actor,action,enemy.x,enemy.y,math.atan(player.y-enemy.y,player.x-enemy.x))
            if actor.weapons then actor.weapons:Set("W01") end
        end
    end
    for _,barrel in ipairs(game:Map().barrels) do if self.props[barrel.id] then self.props[barrel.id].enabled=barrel.alive end end
    for _,chest in ipairs(game:Map().chests) do
        local n=self.props[chest.id]
        if n then
            local lid=n:GetChild("Lid")
            lid.rotation=Quaternion(chest.opened and -75 or 0,0,0)
            lid.position=chest.opened and Vector3(0,0.75,0.22) or Vector3(0,0.53,0)
        end
    end
    if self.fire and self.name=="camp" then self.fire.scale=Vector3(0.38,0.6+math.sin(game.time*9)*0.08,0.38) end
    self:UpdateEffects()
end
function Scene3D:UpdateEffects()
    -- A small reusable scene-node pool; the rules own projectile lifetime and hits.
    local game,env=self.app.game,self.environment
    local index=0
    local function effect(model,pos,scale,rotation,kind)
        index=index+1
        local n=self.transient[index]
        if not n then
            n=env.root:CreateChild("CombatEffect")
            n:CreateComponent("StaticModel")
            self.transient[index]=n
        end
        n.enabled=true; n.position=pos; n.scale=scale; n.rotation=rotation
        local mesh=n:GetComponent("StaticModel")
        mesh.model=model
        self.effectMats=self.effectMats or {arrow=solid(0.95,0.75,0.3,0,true),arcane=solid(0.17,0.58,0.85,0,true),fire=solid(1,0.25,0.02,0,true),slash=solid(0.85,0.92,0.76,0,true)}
        mesh:SetMaterial(self.effectMats[kind])
    end
    for _,a in ipairs(game.projectiles) do
        local p=Environment.ToWorld(a.x,a.y)
        effect(env.box,Vector3(p.x,1.05,p.z),Vector3(0.045,0.045,0.7),Quaternion(0,90+a.angle*180/math.pi,0),a.kind=="staff" and "arcane" or "arrow")
    end
    for _,e in ipairs(game.effects) do
        local p=Environment.ToWorld(e.x,e.y)
        if e.type=="blast" then
            local r=(1-e.t)*3+0.5
            effect(env.rock,Vector3(p.x,0.3,p.z),Vector3(r,0.7,r),Quaternion(),"fire")
        elseif e.type=="swing" then
            self.slashModel=self.slashModel or TorusGeometry(1.7,0.035,6,28,2.4):ToModel()
            effect(self.slashModel,Vector3(p.x,0.95,p.z),Vector3(1,1,1),Quaternion(90,0,-e.angle*180/math.pi-65),"slash")
        elseif e.type=="hit" then effect(env.rock,Vector3(p.x,1.15,p.z),Vector3(0.16,0.25,0.16),Quaternion(20,20,20),"slash") end
    end
    for i=index+1,#self.transient do self.transient[i].enabled=false end
end
return Scene3D
