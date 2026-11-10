-- ROM-free deterministic mock for the three pure-seed Dolphin preview scripts.
-- Usage: lua tests/optimization/dolphin_pure_mock.lua <game_script>
local path=assert(arg[1])
local testSeed = 0
local frame = 0
local lastScreen = ""
ReadValue8=function(address)
 if address == 0x3 then return 0x45 end -- USA Channel
 return 0
end
ReadValue16=function() return 0 end
ReadValue32=function() return testSeed end
GetFrameCount=function() return frame end
SetScreenText=function(s) lastScreen=s end
dofile(path)
-- The three upstream scripts pass zero-padded IV strings into bitwise HP
-- calculations. Lua 5.4 may reject "08"/"09" as bitwise operands.
-- Apply the SAME type normalization in BOTH control and optimized copies,
-- preserving the original formatted IV text and isolating only cache parity.
local oldHP = assert(getHPTypeAndPower)
getHPTypeAndPower = function(...)
 local n = {...}
 for i = 1, #n do n[i] = assert(tonumber(n[i])) end
 return oldHP(table.unpack(n))
end
assert(type(onScriptStart)=="function")
assert(type(onScriptUpdate)=="function")
onScriptStart()
local seeds={0,0,0x1234,0x1234,0xAABBCCDD,0xAABBCCDD,1,1,0xDEADBEEF,0}
for _,s in ipairs(seeds) do
 testSeed=s
 frame=frame+1
 onScriptUpdate()
 -- Print full visual text with a frame separator, guaranteeing all resulting
 -- PID/IV/Nature/advance information is byte-equivalent to the original.
 io.write("--FRAME ",frame,"--\n")
 io.write(lastScreen)
 io.write("\n")
end
