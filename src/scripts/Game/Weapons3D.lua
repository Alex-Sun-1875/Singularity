local Weapons={}
Weapons.__index=Weapons
local models={}
local function model(name)
    if models[name] then return models[name] end
    local path=name=="box" and "Models/Box.mdl" or (name=="sphere" and "Models/Sphere.mdl" or "Models/Cylinder.mdl")
    models[name]=cache:GetResource("Model",path)
    return models[name]
end
local function material(color,metal)
    local m=Material:new(); m:SetTechnique(0,cache:GetResource("Technique","Techniques/PBR/PBRNoTexture.xml"))
    m:SetShaderParameter("MatDiffColor",Variant(Color(color[1],color[2],color[3])))
    m:SetShaderParameter("Roughness",Variant(.48)); m:SetShaderParameter("Metallic",Variant(metal or 0))
    return m
end
local function shape(root,name,kind,p,s,mat)
    local node=root:CreateChild(name); node.position=p; node.scale=s
    local mesh=node:CreateComponent("StaticModel"); mesh.model=model(kind); mesh:SetMaterial(mat); mesh.castShadows=true
    return node
end
local function beam(root,a,b,r,mat)
    local node=shape(root,"CraftedPart","cylinder",(a+b)*.5,Vector3(r,(b-a).length,r),mat)
    node.rotation=Quaternion(Vector3.UP,(b-a):Normalized())
end
function Weapons.New(actor,definition,enemy)
    local bone=actor.mesh.skeleton:GetBone("hand_r")
    if not bone or not bone.node then return nil end
    return setmetatable({hand=bone.node,definition=definition,enemy=enemy,items={},current=nil},Weapons)
end
function Weapons:Create(id)
    local kind=(id=="W07" or id=="L02") and "bow" or (id=="W11" and "staff" or "sword")
    local spec=self.definition.sockets and self.definition.sockets[kind]
    if not spec then return nil end
    local root=self.hand:CreateChild("HeldWeapon")
    local q,p=spec.rotation,spec.position
    root.rotation=Quaternion(q[1],q[2],q[3],q[4]); root.position=Vector3(p[1],p[2],p[3])
    local scale=self.hand.worldScale; root.scale=Vector3(1/scale.x,1/scale.y,1/scale.z)
    local wood=material({.18,.08,.025}); local steel=material({.43,.48,.46},.8); local gold=material({.48,.3,.07},.65)
    if self.enemy then
        shape(root,"ClubGrip","cylinder",Vector3(0,.12,0),Vector3(.055,.5,.055),wood)
        shape(root,"ClubHead","sphere",Vector3(0,.48,0),Vector3(.17,.32,.17),wood)
        for y=.38,.55,.08 do shape(root,"IronBand","cylinder",Vector3(0,y,0),Vector3(.18,.025,.18),steel) end
    elseif kind=="sword" then
        shape(root,"LeatherGrip","cylinder",Vector3(0,-.025,0),Vector3(.045,.20,.045),wood)
        shape(root,"Pommel","sphere",Vector3(0,-.14,0),Vector3(.072,.07,.07),gold)
        shape(root,"CrossGuard","box",Vector3(0,.09,0),Vector3(.22,.03,.042),gold)
        local points={Vector3(-.034,.11,0),Vector3(.034,.11,0),Vector3(0,.11,.012),Vector3(0,.11,-.012),
            Vector3(-.026,.78,0),Vector3(.026,.78,0),Vector3(0,.78,.008),Vector3(0,.78,-.008),Vector3(0,.94,0)}
        local node=root:CreateChild("ForgedBlade")
        local mesh=node:CreateComponent("StaticModel"); mesh.model=ConvexGeometry(points):ToModel(); mesh:SetMaterial(steel); mesh.castShadows=true
        if id=="L01" then shape(root,"StormInset","box",Vector3(0,.15,.017),Vector3(.02,.1,.015),material({.2,.65,.9},.35)) end
    elseif kind=="bow" then
        local last
        for i=0,16 do
            local t=i/16*2-1
            local p=Vector3(.21*(1-t*t),t*.57,0)
            if last then beam(root,last,p,.025,wood) end
            last=p
        end
        beam(root,Vector3(0,-.57,0),Vector3(0,.57,0),.004,material({.65,.59,.4}))
        shape(root,"GripWrap","cylinder",Vector3(.21,0,0),Vector3(.035,.16,.035),wood)
    else
        shape(root,"AshStaff","cylinder",Vector3(0,.3,0),Vector3(.045,1.45,.045),wood)
        shape(root,"Ferrule","cylinder",Vector3(0,.98,0),Vector3(.07,.1,.07),gold)
        shape(root,"ArcaneStone","sphere",Vector3(0,1.1,0),Vector3(.13,.19,.13),material({.16,.52,.75},.3))
    end
    return root
end
function Weapons:Set(id)
    if id==self.current then return end
    for _,item in pairs(self.items) do item.enabled=false end
    local item=self.items[id]
    if not item then item=self:Create(id); self.items[id]=item end
    if item then item.enabled=true end
    self.current=id
end
return Weapons
