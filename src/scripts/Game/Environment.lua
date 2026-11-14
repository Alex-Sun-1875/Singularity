-- Scene geometry is measured in metres. Rules remain in chapter design pixels.
local Data=require("Game.Data")
---@class ChapterEnvironment
---@field root Node
---@field scene Scene
---@field name string
---@field box Model
---@field cylinder Model
---@field block Model
---@field rock Model
---@field crown Model
---@field mats table
local Environment={}
Environment.__index=Environment
local SCALE=40
local function h(x,z)
    local shoulder=math.min(1,math.max(0,(math.abs(z)-3.0)/5))
    return (math.sin(x*0.38+z*0.24)*0.27+math.cos(z*0.66-x*0.17)*0.18)*shoulder
end
function Environment.ToWorld(x,y) return Vector3((x-800)/SCALE,0,-(y-450)/SCALE) end
function Environment.ToChapter(p) return p.x*SCALE+800,450-p.z*SCALE end
function Environment.Height(x,z) return h(x,z) end
local function material(r,g,b,grain)
    local m=Material:new()
    assert(m:SetSurfaceShader("Shaders/BLGL/FieldSurface.shader"),"Field surface shader unavailable")
    m:SetShaderParameter("base_color",Variant(Color(r,g,b)))
    m:SetShaderParameter("grain_scale",Variant(grain or 5.0))
    return m
end
function Environment:Shape(name,model,pos,scale,mat,rotation,parent)
    local node=(parent or self.root):CreateChild(name)
    node.position=pos; node.scale=scale
    if rotation then node.rotation=rotation end
    local mesh=node:CreateComponent("StaticModel")
    mesh.model=model; mesh:SetMaterial(mat); mesh.castShadows=true
    return node
end
local function vertex(mesh,x,y,z,u,v)
    mesh:DefineVertex(Vector3(x,y,z))
    local nx=(h(x-0.05,z)-h(x+0.05,z))/0.1
    local nz=(h(x,z-0.05)-h(x,z+0.05))/0.1
    local n=Vector3(nx,1,nz):Normalized()
    mesh:DefineNormal(n); mesh:DefineTexCoord(Vector2(u or x,v or z))
end
function Environment:Terrain()
    local ground=self.root:CreateChild("Ground"):CreateComponent("CustomGeometry")
    ground:BeginGeometry(0,TRIANGLE_LIST)
    local step=0.65
    for x=-27,27-step,step do
        for z=-19,19-step,step do
            for _,p in ipairs({{x,z},{x,z+step},{x+step,z},{x+step,z},{x,z+step},{x+step,z+step}}) do
                vertex(ground,p[1],h(p[1],p[2]),p[2])
            end
        end
    end
    ground:Commit(); ground:SetMaterial(self.mats.grass)
    local road=self.root:CreateChild("Road"):CreateComponent("CustomGeometry")
    road:BeginGeometry(0,TRIANGLE_LIST)
    local function edge(x,side)
        local z=math.sin(x*0.18)*0.7+side*(1.7+0.15*math.sin(x*1.8))
        return {x,z}
    end
    for x=-26,25,0.4 do
        local a,b,c,d=edge(x,-1),edge(x,1),edge(x+0.4,-1),edge(x+0.4,1)
        for _,p in ipairs({a,b,c,c,b,d}) do vertex(road,p[1],h(p[1],p[2])+0.022,p[2]) end
    end
    road:Commit(); road:SetMaterial(self.mats.dirt)
end
function Environment:Tree(x,z,size,seed)
    local y=h(x,z)
    local root=self.root:CreateChild("Oak")
    root.position=Vector3(x,y,z)
    root.rotation=Quaternion(0,seed*71%360,0)
    local trunk=self:Shape("Trunk",self.cylinder,Vector3(0,size*0.75,0),Vector3(size*0.16,size*1.5,size*0.16),self.mats.bark,Quaternion(0,0,4),root)
    for i=0,4 do
        local a=i*2.399+seed
        local r=size*(0.28+0.08*(i%2))
        local bx,bz=math.cos(a)*r,math.sin(a)*r
        local by=size*(1.3+(i%3)*0.23)
        self:Shape("Branch",self.cylinder,Vector3(bx*0.5,by*0.75,bz*0.5),Vector3(size*0.07,size*0.75,size*0.07),self.mats.bark,Quaternion(math.sin(a)*30,0,-math.cos(a)*30),root)
        self:Shape("Crown",self.crown,Vector3(bx,by,bz),Vector3(size*0.95,size*0.72,size*0.88),self.mats.leaves[i%3+1],Quaternion(i*19,seed*13,8),root)
    end
    for i=0,4 do
        local a=i*1.256
        self:Shape("Root",self.cylinder,Vector3(math.cos(a)*size*0.15,0.06,math.sin(a)*size*0.15),Vector3(size*0.07,size*0.48,size*0.07),self.mats.bark,Quaternion(math.cos(a)*70,0,math.sin(a)*70),root)
    end
    return trunk
end
function Environment:Ruin(w,index)
    local pos=Environment.ToWorld(w.x+w.w/2,w.y+w.h/2)
    local sx,sz=w.w/SCALE,w.h/SCALE
    -- Broken retaining walls follow the actual blocking footprint.
    for row=0,2 do
        for i=0,math.max(1,math.floor(sx/0.68))-1 do
            local x=pos.x-sx/2+0.35+i*0.68+(row%2)*0.1
            local z=pos.z
            self:Shape("MossStone",self.block,Vector3(x,h(x,z)+0.28+row*0.48,z),Vector3(0.65,0.46,sz),self.mats.stone[row%2+1],Quaternion(0,(i*7+index)%8-4,0))
        end
    end
    for i=0,7 do
        local x=pos.x+math.cos(i*2.3)*sx*0.7
        local z=pos.z+math.sin(i*2.3)*sz*0.8
        self:Shape("FallenMasonry",self.rock,Vector3(x,h(x,z)+0.16,z),Vector3(0.6,0.3,0.45),self.mats.stone[i%2+1],Quaternion(i*19,i*31,20))
    end
end
function Environment:Grass()
    local mesh=self.root:CreateChild("GrassTufts"):CreateComponent("CustomGeometry")
    mesh:BeginGeometry(0,TRIANGLE_LIST)
    for i=1,2600 do
        local x=((i*0.61803398875)%1)*47-23.5
        local z=((i*0.41421356237)%1)*29-14.5
        if math.abs(z-math.sin(x*0.18)*0.7)>2.2 and (math.sin(x*0.76+z*0.42)+math.cos(z*0.81))>0.25 then
            local y=h(x,z); local tall=0.17+(i%7)*0.04
            for a=0,1 do
                local dx,dz=math.cos(i+a*1.57)*0.08,math.sin(i+a*1.57)*0.08
                vertex(mesh,x-dx,y,z-dz,0,0)
                vertex(mesh,x+dx,y,z+dz,1,0)
                vertex(mesh,x+dx*0.8,y+tall,z+dz*0.8,0.5,1)
            end
        end
    end
    mesh:Commit(); mesh:SetMaterial(cache:GetResource("Material","Materials/Meadow.xml"))
end
function Environment:Inn()
    local pos=Environment.ToWorld(695,152)
    local wood=self.mats.wood
    local wallMat=material(0.67,0.59,0.40,18)
    local roofMat=material(0.31,0.19,0.12,12)
    self:Shape("InnPlaster",self.block,Vector3(pos.x,1.5,pos.z),Vector3(7.2,3,2.6),wallMat)
    for _,x in ipairs({-3.45,-1.15,1.15,3.45}) do
        self:Shape("TimberFrame",self.block,Vector3(pos.x+x,1.6,pos.z-1.34),Vector3(0.16,3.25,0.18),wood)
    end
    for _,y in ipairs({0.28,2.65}) do self:Shape("CrossBeam",self.block,Vector3(pos.x,y,pos.z-1.34),Vector3(7.3,0.16,0.18),wood) end
    for _,side in ipairs({-1,1}) do
        self:Shape("SlatedRoof",self.block,Vector3(pos.x,3.5,pos.z+side*0.8),Vector3(7.9,0.18,1.98),roofMat,Quaternion(side*35,0,0))
        for j=0,5 do self:Shape("RoofRidge",self.block,Vector3(pos.x-3.5+j*1.4,3.52,pos.z+side*0.8),Vector3(0.04,0.22,1.98),wood,Quaternion(side*35,0,0)) end
    end
    self:Shape("Chimney",self.block,Vector3(pos.x+2.4,3.6,pos.z+0.3),Vector3(0.65,2,0.65),self.mats.stone[1])
    self:Shape("ChimneyCap",self.block,Vector3(pos.x+2.4,4.55,pos.z+0.3),Vector3(0.86,0.16,0.86),self.mats.stone[2])
    for _,x in ipairs({-2.1,2.1}) do
        self:Shape("WindowFrame",self.block,Vector3(pos.x+x,1.7,pos.z-1.39),Vector3(1.05,1.12,0.1),wood)
        self:Shape("WindowGlass",self.box,Vector3(pos.x+x,1.7,pos.z-1.46),Vector3(0.84,0.94,0.05),material(0.81,0.60,0.24,18))
        self:Shape("WindowMullion",self.box,Vector3(pos.x+x,1.7,pos.z-1.5),Vector3(0.06,0.95,0.04),wood)
    end
    self:Shape("InnDoor",self.block,Vector3(pos.x,1.03,pos.z-1.4),Vector3(1.3,2,0.18),wood)
    self:Shape("DoorLintel",self.block,Vector3(pos.x,2.15,pos.z-1.42),Vector3(1.65,0.28,0.3),self.mats.stone[1])
    local tablePos=Environment.ToWorld(430,325)
    self:Shape("CourtyardTable",self.cylinder,Vector3(tablePos.x,0.88,tablePos.z),Vector3(1.65,0.18,1.25),wood)
    self:Shape("TableStem",self.cylinder,Vector3(tablePos.x,0.43,tablePos.z),Vector3(0.3,0.86,0.3),wood)
    for i=1,3 do self:Shape("Cup",self.cylinder,Vector3(tablePos.x-0.48+i*0.24,1.05,tablePos.z),Vector3(0.12,0.18,0.12),self.mats.stone[1]) end
    for _,x in ipairs({-0.9,0.9}) do
        self:Shape("Stool",self.cylinder,Vector3(tablePos.x+x,0.48,tablePos.z),Vector3(0.52,0.16,0.52),wood)
        self:Shape("StoolLeg",self.cylinder,Vector3(tablePos.x+x,0.24,tablePos.z),Vector3(0.15,0.48,0.15),wood)
    end
end
function Environment.New(scene,name)
    local self=setmetatable({root=scene:CreateChild("ChapterEnvironment"),scene=scene,name=name},Environment)
    self.box=cache:GetResource("Model","Models/Box.mdl")
    self.cylinder=cache:GetResource("Model","Models/Cylinder.mdl")
    self.block=RoundedBoxGeometry(1,1,1,2,0.07):ToModel()
    self.rock=IcosahedronGeometry(0.5,1):ToModel()
    self.crown=IcosahedronGeometry(0.5,2):ToModel()
    self.mats={grass=material(0.28,0.36,0.15,8),dirt=material(0.42,0.32,0.19,11),bark=material(0.21,0.12,0.065,12),
        stone={material(0.43,0.45,0.37,8),material(0.35,0.39,0.29,9)},wood=material(0.40,0.25,0.11,14),
        leaves={material(0.19,0.31,0.075,15),material(0.27,0.38,0.10,14),material(0.32,0.41,0.12,16)}}
    self:Terrain()
    for i=1,24 do
        local x=(i*3.79)%48-24
        local z=(i%2==0 and 1 or -1)*(8.8+(i%4)*1.2)
        self:Tree(x,z,2.4+(i%4)*0.33,i)
    end
    for i=1,44 do
        local x=(i*3.17)%48-24; local z=(i%2==0 and 1 or -1)*(6+(i%7)*1.3)
        self:Shape("Boulder",self.rock,Vector3(x,h(x,z)+0.35,z),Vector3(1.2+(i%4)*0.2,0.9,0.8),self.mats.stone[i%2+1],Quaternion(i*21,i*61,i*13))
    end
    local map=Data.World()[name]
    for i,w in ipairs(map.walls) do if not (name=="camp" and i==1) then self:Ruin(w,i) end end
    if name=="camp" then self:Inn() end
    self:Grass()
    return self
end
function Environment:Destroy() self.root:Remove() end
return Environment
