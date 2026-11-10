-- No-ROM exact-lane simulation for three Gen3 mGBA Held Item side scripts.
-- Usage: lua tests/optimization/side_exact_mock.lua <script-path>
local path=assert(arg[1])
local game=assert(arg[2], "pass game name: E, FRLG or RS")
assert(game=="E" or game=="FRLG" or game=="RS")
local ver=game=="E" and 0x45 or game=="FRLG" and 0x52 or 0x56
local frame,tick,seed=0,0,0xCAFE
local prints=0
local saveCalls=0
local clock=os.time
os.time=function()return math.floor(tick/60)end
C={GBA_KEY={A=1,START=4,SELECT=8}}
console={}
function console:createBuffer()
 local buf={}
 function buf:setSize() end
 function buf:clear() end
 function buf:print() prints=prints+1 end
 return buf
end
local buf=console:createBuffer()
input={}
function input:isKeyActive() return false end
emu={}
function emu:read8(addr)
 if addr==0x80000AE then return ver end
 if addr==0x80000AF then return 0x45 end
 return 0
end
function emu:read16(addr)
 if addr==0x2020000 then return 0xCAFE end
 return seed & 0xFFFF
end
function emu:read32() return seed end
function emu:readRange() return string.rep("\0",16) end
function emu:currentFrame()return frame end
function emu:reset()frame=0 end
function emu:setBreakpoint() return 1 end -- Breakpoint remains dormant in this mock scenario.
function emu:clearBreakpoint() end
callbacks={}
function callbacks:add(name,fn)self[name]=fn end
dofile(path)
assert(callbacks.frame and getRngInfo and getSaveStateInput)
local originalSave=getSaveStateInput
getSaveStateInput=function()
 saveCalls=saveCalls+1
 return originalSave()
end
-- Skip PK3 decoding with invalid synthetic pointers. Keep RNG renderer invoked
-- just as the original did, so the test counts the UI update reduction.
updateCaptureBuffer=function()showRngInfo(buf)end
local trace={}
for i=1,480 do
 tick=tick+1;frame=frame+1
 seed=(seed*0x41C64E6D+0x6073)&0xFFFFFFFF
 callbacks.frame()
 local a,b,c=getRngInfo()
 trace[#trace+1]=string.format("%08X/%08X/%d/%d",a,b,c,saveCalls)
end
print(table.concat(trace,","))
print("PRINTS "..prints)
os.time=clock
