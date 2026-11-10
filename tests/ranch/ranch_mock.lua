-- Synthetic no-offer Dolphin Lua Core harness, no commercial ROM required.
-- Usage: lua tests/ranch/ranch_mock.lua <source-or-instrumented-ranch.lua> [updates]
local src = assert(arg[1], "source path")
local updates = tonumber(arg[2] or "10")
local lastText = ""
local ramWrites = 0
ReadValue8 = function() return 0 end
ReadValue16 = function() return 0 end
ReadValue32 = function() return 0 end
WriteValue8 = function() ramWrites = ramWrites + 1; error("unexpected RAM write") end
WriteValue16 = WriteValue8
WriteValue32 = WriteValue8
SetScreenText = function(s) lastText = s end
GetFrameCount = function() return 0 end
dofile(src)
assert(type(onScriptUpdate) == "function")
onScriptStart()
local trace = {}
for i=1,updates do
 onScriptUpdate()
 trace[#trace+1] = lastText
end
assert(ramWrites==0)
print(table.concat(trace, "\n--UPDATE--\n"))
