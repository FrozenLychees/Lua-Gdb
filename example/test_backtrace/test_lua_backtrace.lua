-- gdb -x LuaGdb.py -x test/test_lua_backtrace.bp --args src/lua  test/test_lua_backtrace.lua
-- The progarm will block at cmath.random.
-- use command to dispaly infomation about lua

local cmath = require "math"
local debug = require("debug")
function a()
    b()
end


function b()
    return c()
end

function c()
    print(cmath.random(1, 2))
    
    print(debug.traceback())
end 


a()
