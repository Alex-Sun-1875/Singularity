local Data = require("Game.Data")
local Chapter = {}
Chapter.__index = Chapter
local VERSION = 1
local function clamp(v,a,b) return math.max(a,math.min(b,v)) end
local function distance(a,b) return math.sqrt((a.x-b.x)^2+(a.y-b.y)^2) end
local function finite(n) return type(n)=="number" and n==n and n~=math.huge and n~=-math.huge end
local function copy(v)
    if type(v)~="table" then return v end
    local out={}
    for k,x in pairs(v) do out[k]=copy(x) end
    return out
end
local function nextRandom(seed) return (seed*48271)%2147483647 end
local function sourceSeed(seed,source)
    local n=seed
    for i=1,#source do n=(n*131+string.byte(source,i))%2147483647 end
    return nextRandom(n+1)
end

-- Collision plan (design pixels): actors use radius 18; walls are solid AABBs.
--  player circle -> wall       arrow segment -> inflated enemy circle
--     (o) | ####                 old -----> new       (enemy)
-- Resolve X/Y separately so corners slide. Swept segment checks prevent fast
-- arrows/dashes from crossing thin walls or skipping a target at low frame rates.
local function segmentBox(x1,y1,x2,y2,w,padding)
    local enter,leave=0,1
    local dx,dy=x2-x1,y2-y1
    local function axis(pos,delta,lo,hi)
        if math.abs(delta)<0.000001 then return pos>=lo and pos<=hi end
        local a,b=(lo-pos)/delta,(hi-pos)/delta
        if a>b then a,b=b,a end
        enter,leave=math.max(enter,a),math.min(leave,b)
        return enter<=leave
    end
    return axis(x1,dx,w.x-padding,w.x+w.w+padding) and axis(y1,dy,w.y-padding,w.y+w.h+padding)
end
local function segmentCircle(x1,y1,x2,y2,e,r)
    local dx,dy=x2-x1,y2-y1
    local n=dx*dx+dy*dy
    local t=n>0 and clamp(((e.x-x1)*dx+(e.y-y1)*dy)/n,0,1) or 0
    return (x1+dx*t-e.x)^2+(y1+dy*t-e.y)^2<=r*r
end

function Chapter.New(seed)
    local self=setmetatable({},Chapter)
    self:Init(seed)
    return self
end
function Chapter:Init(seed)
    self.seed=math.floor(math.abs(tonumber(seed) or 73013))%2147483646+1
    self.rng=self.seed
    self.scene="camp"
    self.player={x=260,y=430,hp=120,maxHp=120,oil=3,gold=0,iron=0,focus=100,angle=0,
        attack=0,dash=0,fire=0,skill=0,dashTime=0,hurtTime=0,moveTime=0}
    self.world=Data.World()
    self.owned={W01=true,W07=true,W11=true}
    self.weapon="W01"
    self.flags={accepted=false,saw_copy=false,recovered=false,complete=false}
    self.receipts={}
    self.projectiles={}
    self.effects={}
    self.status="playing"
    self.dialogue=nil
    self.time=0
    self.toast="与弥菈交谈，听听这份委托。"
    self.toastTime=6
    self.dirty=false
    self.revision=0
end
function Chapter:Changed()
    self.dirty=true
    self.revision=self.revision+1
end
function Chapter:Say(text)
    self.toast=text
    self.toastTime=5
end
function Chapter:Map() return self.world[self.scene] end
function Chapter:Blocked(x1,y1,x2,y2,r)
    for _,w in ipairs(self:Map().walls) do
        if segmentBox(x1,y1,x2,y2,w,r or 0) then return true end
    end
    return false
end
function Chapter:Move(actor,dx,dy,r)
    r=r or 18
    local nx,ny=clamp(actor.x+dx,32,Data.WIDTH-32),clamp(actor.y+dy,115,Data.HEIGHT-48)
    if not self:Blocked(actor.x,actor.y,nx,actor.y,r) then actor.x=nx end
    if not self:Blocked(actor.x,actor.y,actor.x,ny,r) then actor.y=ny end
end
function Chapter:Equip(id)
    if not self.owned[id] or not Data.Weapons[id] or self.status~="playing" then return false end
    for _,e in ipairs(self:Map().enemies) do
        if e.hp>0 and distance(self.player,e)<220 then self:Say("先离开敌人，才能整备武器。"); return false end
    end
    self.weapon=id
    self:Say("已装备「"..Data.Weapons[id].name.."」")
    self:Changed()
    return true
end
function Chapter:Travel(target)
    if not self.world[target] or not self.flags.accepted then self:Say("先与弥菈谈好这份委托。"); return false end
    local previous=self.scene
    self.scene=target
    self.player.x,self.player.y=target=="camp" and 1260 or (previous=="pass" and 1410 or 175),430
    self.projectiles,self.effects={},{}
    self:Say(Data.World()[target].name.." · 进度已记录")
    self:Changed()
    return true
end
function Chapter:Choose(choice)
    if choice=="accept" or choice=="ask_letter" then
        if not self.flags.accepted then
            self.flags.accepted=true
            self.player.gold=self.player.gold+60
            self.receipts.acceptance_advance=true
        end
        if choice=="ask_letter" then
            self.flags.saw_copy=true
            self:Say("她展示了求援段与日期，却遮住了姓名。委托预支 +60金币。")
        else self:Say("委托预支 +60金币 · 沿野路前往隘口。") end
    elseif choice=="read_letter" and self.flags.recovered then
        self.flags.read_letter=true
        self:Say(self.flags.saw_copy and "求援段与抄件一致。她隐去的，是伊芙琳的姓名。" or "弥菈接约前就知道有人求援。回旅店找她。")
    elseif choice=="finish" and self.flags.read_letter then
        self.flags.complete=true
        self:Say("被截获的星片 · 小章节完成。可以继续探索已到过的地方。")
    end
    self.dialogue=nil
    self:Changed()
end
function Chapter:Loot(id)
    for _,chest in ipairs(self:Map().chests) do
        if chest.id==id and not chest.opened then
            chest.opened=true
            self.receipts[id]=true
            if chest.kind=="gold" then self.player.gold=self.player.gold+chest.amount; self:Say("发现旧驿费袋 · 金币 +"..chest.amount)
            else self.player.iron=self.player.iron+chest.amount; self:Say("搜得废铁 +"..chest.amount) end
            if chest.kind=="relic" then self:RollLegend(id.."_legend",0.18) end
            self:Changed()
            return true
        end
    end
    return false
end
function Chapter:RollLegend(source,chance)
    if self.receipts[source] then return self.receipts[source] end
    local roll=sourceSeed(self.seed,source)
    local result="none"
    if roll/2147483647<chance then
        local pool={}
        for _,id in ipairs({"L01","L02"}) do if not self.owned[id] then pool[#pool+1]=id end end
        if #pool>0 then
            result=pool[nextRandom(roll)%#pool+1]
            self.owned[result]=true
            self:Say("传奇发现 · 「"..Data.Weapons[result].name.."」 · 在安全处按 B 整备")
            self.effects[#self.effects+1]={type="legend",x=self.player.x,y=self.player.y,t=3}
        else self.player.iron=self.player.iron+3; result="duplicate_iron"; self:Say("已收藏此池全部传奇 · 废铁 +3") end
    end
    self.receipts[source]=result
    self.rng=nextRandom(self.rng)
    self:Changed()
    return result
end
function Chapter:Interact()
    local p=self.player
    if self.status~="playing" then return end
    if self.scene=="camp" then
        if distance(p,{x=420,y=380})<150 then
            self.dialogue=self.flags.read_letter and "debrief" or (self.flags.accepted and "accepted" or "offer")
            return
        elseif distance(p,{x=230,y=545})<110 then
            p.hp,p.oil,p.focus=p.maxHp,3,100
            self:Say("篝火休整 · 生命与火油恢复，保存进度。")
            self:Changed()
            return
        end
    end
    for _,chest in ipairs(self:Map().chests) do
        if not chest.opened and distance(p,chest)<90 then self:Loot(chest.id); return end
    end
    if self.scene=="pass" and distance(p,{x=1420,y=405})<140 then
        if self.flags.recovered then self.dialogue="letter"; return end
        for _,e in ipairs(self:Map().enemies) do
            if e.hp>0 then self:Say("守卫还在看守遗物匣。先解决隘口的守卫。"); return end
        end
        self.flags.recovered=true
        self.player.gold=self.player.gold+20
        self.receipts.rescue_payment=true
        self.dialogue="letter"
        self:Changed()
        return
    end
    for _,gate in ipairs(self:Map().exits) do if distance(p,gate)<110 then self:Travel(gate.to); return end end
    self:Say("靠近人物、篝火、宝箱或路口，再按 E 互动。")
end
function Chapter:Kill(e)
    if e.counted then return end
    e.hp,e.counted=0,true
    self.player.iron=self.player.iron+(e.kind=="elite" and 2 or 1)
    self.effects[#self.effects+1]={type="death",x=e.x,y=e.y,t=0.6}
    if e.kind=="elite" then self:RollLegend("legend_"..e.id,0.25) end
    self:Changed()
end
function Chapter:Hurt(e,damage,angle,push)
    if e.hp<=0 then return end
    e.hp=math.max(0,e.hp-damage)
    e.vx=e.vx+math.cos(angle)*(push or 0)
    e.vy=e.vy+math.sin(angle)*(push or 0)
    self.effects[#self.effects+1]={type="hit",x=e.x,y=e.y,t=0.22}
    if e.hp<=0 then self:Kill(e) end
    self:Changed()
end
function Chapter:Explode(barrel)
    if not barrel.alive then return end
    barrel.alive=false
    self.effects[#self.effects+1]={type="blast",x=barrel.x,y=barrel.y,t=0.7}
    for _,e in ipairs(self:Map().enemies) do
        if e.hp>0 and distance(e,barrel)<155 then self:Hurt(e,100,math.atan(e.y-barrel.y,e.x-barrel.x),330) end
    end
    for _,b in ipairs(self:Map().barrels) do if b.alive and distance(b,barrel)<155 then self:Explode(b) end end
    self:Changed()
end
function Chapter:SpawnProjectile(angle,power,skill)
    local p=self.player
    self.projectiles[#self.projectiles+1]={x=p.x,y=p.y,vx=math.cos(angle)*680,vy=math.sin(angle)*680,
        angle=angle,travelled=0,life=2,returning=self.weapon=="L02",leg="out",hits={},damage=power,
        kind=Data.Weapons[self.weapon].kind,skill=skill or false,pierce=skill and 2 or 1}
end
function Chapter:Attack(angle)
    local p=self.player
    if self.status~="playing" or p.attack>0 then return end
    p.angle=angle or p.angle
    local kind=Data.Weapons[self.weapon].kind
    p.attack=kind=="sword" and 0.44 or 0.70
    if kind=="sword" then
        self.effects[#self.effects+1]={type="swing",x=p.x,y=p.y,angle=p.angle,t=0.24}
        for _,e in ipairs(self:Map().enemies) do
            local a=math.atan(e.y-p.y,e.x-p.x)-p.angle
            a=math.atan(math.sin(a),math.cos(a))
            if e.hp>0 and distance(e,p)<110 and math.abs(a)<1.35 and not self:Blocked(p.x,p.y,e.x,e.y,0) then
                self:Hurt(e,self.weapon=="L01" and 33 or 27,p.angle,170)
                if self.weapon=="L01" and e.hp>0 then
                    self.rng=nextRandom(self.rng)
                    if self.rng/2147483647<0.22 then e.mark=7; self:Say("雷痕已留下 · 按 R 引爆") end
                end
            end
        end
        for _,b in ipairs(self:Map().barrels) do if b.alive and distance(b,p)<110 then self:Explode(b) end end
    else self:SpawnProjectile(p.angle,kind=="bow" and 22 or 19,false) end
end
function Chapter:Skill()
    local p=self.player
    if self.status~="playing" or p.skill>0 or p.focus<20 then return end
    p.focus=p.focus-20
    p.skill=6
    if Data.Weapons[self.weapon].kind=="sword" then
        self:Move(p,math.cos(p.angle)*35,math.sin(p.angle)*35)
        for _,e in ipairs(self:Map().enemies) do
            if e.hp>0 and distance(e,p)<145 and not self:Blocked(p.x,p.y,e.x,e.y,0) then
                self:Hurt(e,36,p.angle,260)
                if self.weapon=="L01" and e.mark>0 then
                    e.mark=0
                    self.effects[#self.effects+1]={type="lightning",x=e.x,y=e.y,t=0.35}
                    self:Hurt(e,25,p.angle,0)
                    local jumps=0
                    for _,other in ipairs(self:Map().enemies) do
                        if other~=e and other.hp>0 and distance(other,e)<240 and jumps<2 and not self:Blocked(e.x,e.y,other.x,other.y,0) then
                            jumps=jumps+1
                            self.effects[#self.effects+1]={type="arc",x=e.x,y=e.y,tx=other.x,ty=other.y,t=0.3}
                            self:Hurt(other,22,p.angle,80)
                        end
                    end
                end
            end
        end
        self.effects[#self.effects+1]={type="swing",x=p.x,y=p.y,angle=p.angle,t=0.3}
    else self:SpawnProjectile(p.angle,34,true) end
    self:Changed()
end
function Chapter:Fire()
    local p=self.player
    if p.fire>0 or p.oil<=0 or self.status~="playing" then return end
    local x,y=p.x+math.cos(p.angle)*190,p.y+math.sin(p.angle)*190
    if self:Blocked(p.x,p.y,x,y,0) then self:Say("墙体挡住了投掷路线。"); return end
    p.fire,p.oil=0.8,p.oil-1
    self.effects[#self.effects+1]={type="blast",x=x,y=y,t=0.85}
    for _,e in ipairs(self:Map().enemies) do if e.hp>0 and distance(e,{x=x,y=y})<120 then self:Hurt(e,75,p.angle,180) end end
    for _,b in ipairs(self:Map().barrels) do if b.alive and distance(b,{x=x,y=y})<120 then self:Explode(b) end end
    self:Changed()
end
function Chapter:HitProjectile(projectile,e)
    local key=projectile.leg..":"..e.id
    if e.hp<=0 or projectile.hits[key] then return false end
    projectile.hits[key]=true
    self:Hurt(e,projectile.damage,projectile.angle,70)
    return true
end
function Chapter:Damage(amount)
    local p=self.player
    if p.dashTime>0 or p.hurtTime>0 then return end
    p.hp=math.max(0,p.hp-amount)
    p.hurtTime=0.5
    if p.hp==0 then self.status="dead"; self:Say("在旅店篝火重整；已取得的物品与已败守卫保留。") end
    self:Changed()
end
function Chapter:Retry()
    self.status,self.scene="playing","camp"
    self.player.x,self.player.y,self.player.hp,self.player.oil=260,430,self.player.maxHp,3
    self.player.focus,self.player.dashTime,self.player.hurtTime=100,0,0
    self.projectiles,self.effects={},{}
    for _,map in pairs(self.world) do
        for _,e in ipairs(map.enemies) do if e.hp>0 then e.hp=e.maxHp; e.x,e.y=e.spawnX,e.spawnY end; e.windup,e.cooldown,e.vx,e.vy=0,0,0,0 end
    end
    self:Changed()
end
function Chapter:Step(dt,controls)
    dt=clamp(tonumber(dt) or 0,0,0.05)
    controls=controls or {}
    self.time=self.time+dt
    self.toastTime=math.max(0,self.toastTime-dt)
    for i=#self.effects,1,-1 do local e=self.effects[i]; e.t=e.t-dt; if e.t<=0 then table.remove(self.effects,i) end end
    if self.status~="playing" or self.dialogue then return end
    local p=self.player
    for _,key in ipairs({"attack","dash","fire","skill","hurtTime","dashTime"}) do p[key]=math.max(0,p[key]-dt) end
    p.focus=math.min(100,p.focus+5*dt)
    local mx,my=controls.x or 0,controls.y or 0
    local n=math.sqrt(mx*mx+my*my)
    if n>1 then mx,my=mx/n,my/n end
    if finite(controls.angle) then p.angle=controls.angle elseif n>0.1 then p.angle=math.atan(my,mx) end
    if controls.dash and p.dash<=0 then p.dash,p.dashTime=1.1,0.18 end
    local speed=p.dashTime>0 and 660 or 230
    local dx=p.dashTime>0 and math.cos(p.angle) or mx
    local dy=p.dashTime>0 and math.sin(p.angle) or my
    self:Move(p,dx*speed*dt,dy*speed*dt)
    if n>0 then p.moveTime=p.moveTime+dt end
    if controls.attack then self:Attack(p.angle) end
    if controls.skill then self:Skill() end
    if controls.fire then self:Fire() end
    if controls.interact then self:Interact() end
    for _,e in ipairs(self:Map().enemies) do
        if e.hp>0 then
            e.cooldown,e.mark=math.max(0,e.cooldown-dt),math.max(0,e.mark-dt)
            self:Move(e,e.vx*dt,e.vy*dt,e.kind=="elite" and 26 or 18)
            e.vx,e.vy=e.vx*math.exp(-9*dt),e.vy*math.exp(-9*dt)
            local d=distance(e,p)
            if e.windup>0 then
                e.windup=e.windup-dt
                if e.windup<=0 then
                    local reach=e.kind=="elite" and 120 or 62
                    if distance(e,p)<reach and not self:Blocked(e.x,e.y,p.x,p.y,0) then self:Damage(e.kind=="elite" and 27 or 12) end
                    self.effects[#self.effects+1]={type="enemySwing",x=e.x,y=e.y,t=0.22}
                    e.cooldown=e.kind=="elite" and 1.5 or 1.0
                end
            elseif d<(e.kind=="elite" and 105 or 54) and e.cooldown<=0 then e.windup=e.kind=="elite" and 0.85 or 0.48
            elseif d<410 and d>38 then
                local angle=math.atan(p.y-e.y,p.x-e.x)
                self:Move(e,math.cos(angle)*78*dt,math.sin(angle)*78*dt,e.kind=="elite" and 26 or 18)
            end
        end
    end
    for i=#self.projectiles,1,-1 do
        local arrow=self.projectiles[i]
        arrow.life=arrow.life-dt
        if arrow.returning and arrow.leg=="out" and arrow.travelled>420 then arrow.leg="back"; arrow.life=2 end
        if arrow.leg=="back" then
            local angle=math.atan(p.y-arrow.y,p.x-arrow.x)
            arrow.vx,arrow.vy,arrow.angle=math.cos(angle)*720,math.sin(angle)*720,angle
        end
        local nx,ny=arrow.x+arrow.vx*dt,arrow.y+arrow.vy*dt
        local blocked=self:Blocked(arrow.x,arrow.y,nx,ny,2)
        if blocked then arrow.life=0 end
        if not blocked then
            for _,e in ipairs(self:Map().enemies) do
                if e.hp>0 and segmentCircle(arrow.x,arrow.y,nx,ny,e,e.kind=="elite" and 32 or 23) and self:HitProjectile(arrow,e) then
                    if not arrow.returning then arrow.pierce=arrow.pierce-1; if arrow.pierce<=0 then arrow.life=0; break end end
                end
            end
            for _,b in ipairs(self:Map().barrels) do
                if b.alive and segmentCircle(arrow.x,arrow.y,nx,ny,b,20) then self:Explode(b); arrow.life=0; break end
            end
        end
        arrow.travelled=arrow.travelled+math.sqrt((nx-arrow.x)^2+(ny-arrow.y)^2)
        if arrow.leg=="back" and segmentCircle(arrow.x,arrow.y,nx,ny,p,20) then arrow.life=0 end
        arrow.x,arrow.y=nx,ny
        if arrow.life<=0 or nx<0 or nx>Data.WIDTH or ny<0 or ny>Data.HEIGHT then table.remove(self.projectiles,i) end
    end
end
function Chapter:Snapshot()
    return copy({version=VERSION,seed=self.seed,rng=self.rng,scene=self.scene,player=self.player,
        world=self.world,owned=self.owned,weapon=self.weapon,flags=self.flags,receipts=self.receipts,status=self.status})
end
function Chapter.Restore(s)
    if type(s)~="table" or s.version~=VERSION or type(s.player)~="table" or type(s.world)~="table"
        or type(s.flags)~="table" or type(s.receipts)~="table" or type(s.owned)~="table" then return nil end
    for _,key in ipairs({"x","y","hp","maxHp","oil","gold","iron","focus","angle","attack","dash","fire","skill","dashTime","hurtTime","moveTime"}) do
        if not finite(s.player[key]) then return nil end
    end
    if not finite(s.seed) or not finite(s.rng) or s.seed<1 or s.rng<1 or s.player.maxHp~=120 or s.player.hp<0
        or s.player.hp>120 or s.player.oil<0 or s.player.oil>3 or s.player.gold<0 or s.player.iron<0
        or s.player.x<0 or s.player.x>Data.WIDTH or s.player.y<0 or s.player.y>Data.HEIGHT then return nil end
    local defaults=Data.World()
    if not defaults[s.scene] or not Data.Weapons[s.weapon] or not s.owned[s.weapon] then return nil end
    for name,map in pairs(defaults) do
        local saved=s.world[name]
        if type(saved)~="table" or type(saved.enemies)~="table" or #saved.enemies~=#map.enemies
            or type(saved.barrels)~="table" or #saved.barrels~=#map.barrels or type(saved.chests)~="table" or #saved.chests~=#map.chests then return nil end
        for i,e in ipairs(saved.enemies) do
            if e.id~=map.enemies[i].id or not finite(e.hp) or not finite(e.x) or not finite(e.y) or e.hp<0 or e.hp>map.enemies[i].maxHp then return nil end
        end
    end
    local g=Chapter.New(s.seed-1)
    g.rng,g.scene,g.player,g.flags,g.receipts,g.owned,g.weapon,g.status=s.rng,s.scene,copy(s.player),copy(s.flags),copy(s.receipts),copy(s.owned),s.weapon,s.status=="dead" and "dead" or "playing"
    -- Restore only mutable fields into authoritative local map definitions.
    for name,map in pairs(g.world) do
        for i,e in ipairs(map.enemies) do
            local saved=s.world[name].enemies[i]
            e.x,e.y,e.hp,e.counted=saved.x,saved.y,saved.hp,saved.hp<=0
        end
        for i,b in ipairs(map.barrels) do b.alive=s.world[name].barrels[i].alive==true end
        for i,c in ipairs(map.chests) do c.opened=s.world[name].chests[i].opened==true end
    end
    g.player.dashTime,g.player.hurtTime=0,0
    g:Say("本地进度已恢复")
    return g
end

return Chapter
