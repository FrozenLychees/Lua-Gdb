import sys
sys.path.append("/home/ubuntu/lua-5.4.6/LuaGdb")

import gdb
import ldebug
import common

import traceback

# gdb -x LuaGdb/HelloGdbCommand.py -x lua.bp --args src/lua  test/test_upvalues.lua 

class LuaBacktrace(gdb.Command):
    """
        Lua LuaBacktrace.
        Output the current Lua call stack, the implementation method is the same as debug.trace in Lua.
        But there is no FuncName because it is too complicated.

        If the argument are given, it is converted to a poninter to lua_state, otherwise the L in current C stack is used.
        For example, lua-backtrace or lua-backtrace 0x5555557ac268
    """

    def __init__ (self):
        super(LuaBacktrace, self).__init__ ("lua-backtrace", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        
        try:
           self._ImpInvoke(args, from_tty)
           pass
        except Exception as e:
            traceback.print_exc()


    def _ImpInvoke (self, args, from_tty):
        argv = gdb.string_to_argv(args)

        if len(argv) == 0 :
            luaStatePointer = gdb.parse_and_eval("L")    
        else:
            # like lua-backtrace 0x5555557ac268
            luaStatePointer = common.CastPointer2LuaStatePointer(gdb.parse_and_eval(argv[0]))

        callInfoPointer = luaStatePointer['ci']

        ci = common.CallInfoValue(luaStatePointer, callInfoPointer)
        clusurePointer = ci.GetClosurePointer()
        # common.RemovePrint("clusurePointer = %s, addr = %s type = %s", clusurePointer, clusurePointer.address, clusurePointer.type)
        
        level = 0
        luaDebug = ldebug.LuaDebug()
        print("stack traceback:")
        while(ldebug.LuaGetstack(luaStatePointer, level, luaDebug) != 0):
            status = ldebug.LuaGetinfo(luaStatePointer, "Slnt",  luaDebug)

            level = level + 1
            if luaDebug.currentLine <= 0:
                print("\t%s: in" %(luaDebug.shortSrc))
            else:
                print("\t%s:%s" %(luaDebug.shortSrc, luaDebug.currentLine))

            if luaDebug.istailcall:
                print("\t(...tail calls...)")

class LuaPrintStack(gdb.Command):
    """
        Lua LuaPrintStack.

        Output all stackValues in the Lua stack, including their addresses and values

        If the argument are given, it is converted to a poninter to lua_state, otherwise the L in current C stack is used.
        For example, lua-printStack or lua-printStack 0x5555557ac268
    """

    def __init__(self):
        super(LuaPrintStack, self).__init__ ("lua-printStack", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        try:
           self._ImpInvoke(args, from_tty)
           pass
        except Exception as e:
            traceback.print_exc()
    
    def _ImpInvoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)

        if len(argv) == 0 :
            luaStatePointer = gdb.parse_and_eval("L")    
        else:
            # like lua-backtrace 0x5555557ac268
            luaStatePointer = common.CastPointer2LuaStatePointer(gdb.parse_and_eval(argv[0]))

        stackValuePointer = luaStatePointer['top']['p'] - 1

        index = 0
        while stackValuePointer >= luaStatePointer['stack']['p']:
            tValue = common.TValueObj(stackValuePointer['val'].address)
            print("[%s] --> [(StackValue*)%s] --> [%s][%s]\n" % (index, str(stackValuePointer), tValue.GetTypeName(), tValue.GetValue()))
            index = index + 1
            stackValuePointer = stackValuePointer - 1

class LuaPrintTValue(gdb.Command):
    """
        Lua LuaPrintTValue.

        Output the value of the target Tvalue
        For example, lua-printTValue 0x5555557ac268
    """
    def __init__(self):
        super(LuaPrintTValue, self).__init__ ("lua-printTValue", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        try:
           self._ImpInvoke(args, from_tty)
           pass
        except Exception as e:
            traceback.print_exc()

    def _ImpInvoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)

        # like lua-printTValue 0x5555557ac268
        voidPointer = gdb.parse_and_eval(argv[0])
        tValuePointer = common.Cast2TargetTypePointer(voidPointer, "TValue")
        tValue = common.TValueObj(tValuePointer)
        print("[%s][%s]\n" % (tValue.GetTypeName(), tValue.GetValue()))

class LuaPrintCoroutines(gdb.Command):
    """
        Lua LuaPrintCoroutines.

        Find global_State through lua_status, and then output all LUA_VTHREAD type objects.
        If the argument are given, it is converted to a poninter to lua_state, otherwise the L in current C stack is used.
        For example, lua-coroutines or lua-coroutines 0x5555557ac268
    """

    def __init__(self):
        super(LuaPrintCoroutines, self).__init__ ("lua-coroutines", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        try:
           self._ImpInvoke(args, from_tty)
           pass
        except Exception as e:
            traceback.print_exc()

    def _ImpInvoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)

        if len(argv) == 0 :
            luaStatePointer = gdb.parse_and_eval("L")    
        else:
            # like lua-backtrace 0x5555557ac268
            luaStatePointer = common.CastPointer2LuaStatePointer(gdb.parse_and_eval(argv[0]))
        globalStatePointer = luaStatePointer['l_G']
        gcObjectPointer = globalStatePointer['allgc']

        print("[m]Thread: ", str(globalStatePointer['mainthread']))
        while gcObjectPointer['next']:
            if int(gcObjectPointer['tt']) == common.LUA_VTHREAD:
                print("Thread:", str(gcObjectPointer))
            gcObjectPointer = gcObjectPointer['next']

class LuaPrintLocalVal(gdb.Command):
    """
        Lua LuaPrintLocalVal.

        Output the local variable information of the function call.
        If the argument are given, it is converted to a poninter to callInfo, otherwise the callInfo of L in current C stack is used.
        For example, lua-localVal or lua-localVal 0x5555557ac268
    """
    def __init__(self):
        super(LuaPrintLocalVal, self).__init__ ("lua-localVal", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        try:
           self._ImpInvoke(args, from_tty)
           pass
        except Exception as e:
            traceback.print_exc()

    def _ImpInvoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)
    
        if len(argv) == 0 :
            luaStatePointer = gdb.parse_and_eval("L")
            callInfoPointer = luaStatePointer['ci']
        else:
            # like lua-backtrace 0x5555557ac268
            callInfoPointer = common.Cast2TargetTypePointer(gdb.parse_and_eval(argv[0]), "CallInfo")

        index = 1
        while True:
            name, pos = ldebug.LuaGetLocal(luaStatePointer, callInfoPointer, index)
            if int(pos) == 0:
                break
            tValuePointer = common.Index2Value(luaStatePointer, index)
            tValueObj = common.TValueObj(tValuePointer)
            print("name = %s, value = %s pos = %s" % (name, tValueObj.GetValue(), pos))
            index += 1

class LuaPrintUpVal(gdb.Command):
    """
        Lua LuaPrintUpVal.

        Output the upvalus information of the function call.
        If the argument are given, it is converted to a poninter to callInfo, otherwise the callInfo of L in current C stack is used.
        For example, lua-upVal or lua-upVal 0x5555557ac268
    """
    def __init__(self):
        super(LuaPrintUpVal, self).__init__ ("lua-upVal", gdb.COMMAND_USER)

    def invoke (self, args, from_tty):
        try:
           self._ImpInvoke(args, from_tty)
           pass
        except Exception as e:
            traceback.print_exc()

    def _ImpInvoke(self, args, from_tty):
        argv = gdb.string_to_argv(args)
    
        if len(argv) == 0 :
            luaStatePointer = gdb.parse_and_eval("L")
            callInfoPointer = luaStatePointer['ci']
            tValuePointer = callInfoPointer['func']['p']['val'].address
        else:
            # like lua-backtrace 0x5555557ac268
            tValuePointer = common.Cast2TargetTypePointer(gdb.parse_and_eval(argv[0]), "TValue")

        index = 1
        while True:
            name, tValueObj = ldebug.AuxUpValue(tValuePointer, index)
            # common.RemovePrint("name = %s, tValueObj = %s", name, tValueObj)
            if not tValueObj:
                break
            index = index + 1
            print("name = %s, value = %s" % (name, tValueObj.GetValue()))


LuaBacktrace()
LuaPrintStack()
LuaPrintTValue()
LuaPrintCoroutines()
LuaPrintLocalVal()
LuaPrintUpVal()

