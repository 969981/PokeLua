-- Gen1 Bot source trace: pure synthetic Game Boy memory, no ROM.
-- lua gen1_bot_mock.lua <file.lua> <biz|vba> <tid_success|tid_limit|shiny_limit|bite_limit|species_limit>
local source,platform,scenario=assert(arg[1]),assert(arg[2]),assert(arg[3])
local attempts,frames = 0,0
local trace={}
local function emit(v)trace[#trace+1]=v end
bit = {rshift=function(x,n)return x>>n end, band=function(x,m)return x&m end}
table.getn = table.getn or function(t)return #t end
local version = platform=="biz" and 0x5245 or 0x4552
memory={}
local function read16(addr)
 if addr==0x13C then return version end
 if addr==0xD359+4 then return 1 end
 if addr==0xD359 then
  if scenario=="tid_success" and attempts >= 2 then return 0 end
  return 65535
 end
 return 0
end
memory.read_u16_be=read16
memory.readwordunsigned=read16
memory.readbyte=function(addr)
 if addr==0x14E then return 0x04 end
 return 0
end
savestate={}
savestate.create=function()return 42 end
savestate.save=function()
 attempts=attempts+1
 emit("save:"..attempts..":"..frames)
end
savestate.load=function()
 emit("load:"..attempts..":"..frames)
end
joypad={}
joypad.get=function()return {Select=false,select=false} end
joypad.set=function(...)emit("joy:"..attempts..":"..frames)end
emu={}
emu.frameadvance=function()
 frames=frames+1
 if frames>3000 then error("synthetic frame budget exceeded") end
 emit("frame:"..frames)
end
emu.pause=function()end
client={screenwidth=function()return 160 end,screenheight=function()return 144 end,
borderheight=function()return 0 end,borderwidth=function()return 0 end,
pause=function()end}
console={clear=function()end}
gui={text=function()end,line=function()end,drawBox=function()end}
input={get=function()return {}end}
local f=assert(io.open(source,"rb"))
local code=assert(f:read("*a"))
f:close()
-- Never run the source's own emulator main loop in a synthetic harness.
local count
code,count=code:gsub('while warning == "" do','while false do',1)
assert(count==1,"one main loop should be disabled in test-only copy")
if scenario~="tid_success" then
 code,count=code:gsub("local BOT_MAX_ATTEMPTS = 0","local BOT_MAX_ATTEMPTS = 2",1)
 assert(count==1,"opt-in limit must exist in optimized copy")
end
local compiled,err=load(code,"@gen1_source","t")
assert(compiled,err)
compiled()
if scenario=="tid_success" or scenario=="tid_limit" then
 local result=TIDBotLoop()
 if scenario=="tid_limit" then assert(result==false,"cap not reached") end
 if scenario=="tid_success" then
  -- TIDFound is a local upvalue in the original scripts, not a global.
  local observedFound = false
  for i=1,40 do
   local name,value=debug.getupvalue(TIDBotLoop,i)
   if not name then break end
   if name=="TIDFound" then observedFound=value;break end
  end
  assert(observedFound and attempts==2,"expected TID success on second attempt")
 end
elseif scenario=="shiny_limit" then
 -- Select Gift mode for known 35-frame limit.
 for i=1,25 do
  local name = debug.getupvalue(shinyBotLoop,i)
  if name=="index" then debug.setupvalue(shinyBotLoop,i,2) break end
 end
 local result=shinyBotLoop(0xCFF1)
 assert(result==false,"shiny bound not reached")
elseif scenario=="bite_limit" then
 assert(fishingBotBiteLoop()==false,"bite bound not reached")
elseif scenario=="species_limit" then
 assert(fishingBotLoop()==false,"species/bite bound not propagated")
end
if scenario~="tid_success" then
 assert(attempts<=2,"unexpected extra savestate attempts")
end
if type(getBotAttemptStats)=="function" then
 local st=getBotAttemptStats()
 if scenario=="tid_success" then assert(st.tid==2) end
 if scenario=="tid_limit" then assert(st.tid==2) end
 if scenario=="shiny_limit" then assert(st.shiny==2) end
 if scenario=="bite_limit" then assert(st.bite==2) end
end
print("===TRACE===")
print(table.concat(trace,";"))
print("===STATS=== "..attempts.." "..frames)
