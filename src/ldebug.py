import gdb
from typing import Tuple
import common


# struct lua_Debug in lua.h
class LuaDebug(object):

    def __init__(self):
        
        self.event = 0
        self.name = ""
        self.namewhat = ""
        self.what = ""
        self.source = ""
        self.srclen = 0
        self.currentLine = 0
        self.linedefined = 0
        self.lastlinedefined = 0
        self.nups = ""
        self.nparams = ""
        self.isvararg = False
        self.istailcall = False
        self.ftransfer = 0
        self.ntransfer = 0
        self.shortSrc = ""
        self.iCi: gdb.Value = None 


def LuaGetinfo(luaStatePointer: gdb.Value, whatStr: str, ar:LuaDebug) -> int:
    ci = ar.iCi
    func = common.S2V(ci['func']['p'])

    cl = None
    if common.TtIsClosure(func):
        callInfoValue = common.CallInfoValue(luaStatePointer, ci)
        cl = callInfoValue.GetClosurePointer()
    status = AuxGetInfo(luaStatePointer, whatStr, ar, cl, ci)
    return status

# static int auxgetinfo (lua_State *L, const char *what, lua_Debug *ar, Closure *f, CallInfo *ci)
# ldebug.c
def AuxGetInfo(luaStatePointer: gdb.Value, whatStr: str, ar:LuaDebug, closurePointer: gdb.Value, callInfoPointer: gdb.Value) -> int:

    status = 1
    callInfoValue = common.CallInfoValue(luaStatePointer, callInfoPointer)
    for what in whatStr:
        if what == 'S':
            FuncInfo(ar, closurePointer)
        elif what == 'l':
            ar.currentLine = GetCurrentLine(callInfoValue) if callInfoValue.IsLua() else -1
        elif what == 'u':
            ar.nups =  0 if closurePointer == None else int(closurePointer['c']['nupvalues'])
            if(common.NoLuaClosure(closurePointer)):
                ar.isvararg = 1
                ar.nparams = 0
            else:
                ar.isvararg = int(closurePointer['l']['p']['is_vararg'])
        elif what == 't':
            ar.istailcall = (int(callInfoPointer['callstatus']) & common.CallInfoValue.CIST_TAIL) if callInfoPointer != None else 0
        elif what == 'n':
            # It's too complicated
            # ar.namewhat = GetFuncName(luaStatePointer, callInfoPointer)
            # if ar.namewhat == "":
            #     ar.namewhat = ""
            #     ar.name = ""
            pass
        elif what == 'r':
            if callInfoPointer == None or  not (int(callInfoPointer['callstatus']) & common.CallInfoValue.CIST_TRAN):
                ar.ftransfer = 0
                ar.ntransfer = 0
            else:
                ar.ftransfer = int(callInfoPointer['u2']['transferinfo']['ftransfer'])
                ar.ntransfer = int(callInfoPointer['u2']['transferinfo']['ntransfer'])
        elif what == 'L' or what == "f":
            # /* handled by lua_getinfo */
            pass
        else:
            status = 0
    return status
    

def FuncInfo(ar: LuaDebug, closurePointer: gdb.Value)->None:
    if common.NoLuaClosure(closurePointer):
        ar.source = "=[C]"
        ar.srclen = 4
        ar.linedefined = -1
        ar.lastlinedefined = -1
        ar.what = "C"
    else:
        protoPoninter = closurePointer['l']['p']
        
        if protoPoninter['source']:
            ar.source = common.Getstr(protoPoninter['source'])
            ar.srclen = common.Tsslen(protoPoninter['source'])
        else:
            ar.source = "=?"
            ar.srclen = 2
        ar.linedefined = int(protoPoninter['linedefined'])
        ar.lastlinedefined = int(protoPoninter['lastlinedefined'])
        ar.what =  "main" if int(ar.linedefined) == 0 else "Lua"
    LuaOChunkId(ar)

def GetCurrentLine(callInfoValue: common.CallInfoValue) -> int:
    if callInfoValue.IsLua():
        clusurePointer = callInfoValue.GetClosurePointer()
        callInfoPointer = callInfoValue.GetCallInfoPointer()
        protoPointer = clusurePointer['l']['p']
        savedpc = callInfoPointer['u']['l']['savedpc']
        currentPc= savedpc - protoPointer['code'] - 1
        return LuaG_Getfuncline(protoPointer, currentPc)
    return -1
    

def LuaG_Getfuncline(protoPointer: gdb.Value, currentPc: int) -> int:
    if(protoPointer['lineinfo'] == None):
        return -1
    else:
        basePc, baseLine = LuaG_GetBaseLineInfo(protoPointer, currentPc)
        while(basePc < currentPc):
            basePc += 1
            baseLine += int(protoPointer['lineinfo'][basePc])
        return baseLine

def LuaG_GetBaseLineInfo(protoPointer: int, pc: int) -> Tuple[int, int]:
    if protoPointer['sizeabslineinfo'] == 0 or pc < protoPointer['abslineinfo'][0].pc:
        return -1, int(protoPointer['linedefined'])
    i = pc / common.MAXIWTHABS - 1
    while(i + 1 < protoPointer['sizeabslineinfo'] and pc >= protoPointer['abslineinfo'][i + 1]['pc']):
        i += 1
    basePc = int(protoPointer['abslineinfo'][i]['pc'])
    baseLine = int(protoPointer['abslineinfo'][i]['line'])
    return basePc, baseLine

def LuaGetstack(luaStatePointer: gdb.Value, level: int, ar: LuaDebug):

    status = 0
    if level  < 0:
        return 0
    
    ci = luaStatePointer['ci']
    while level > 0 and ci != luaStatePointer['base_ci'].address:
        level -= 1
        ci = ci['previous']

    if level == 0 and ci != luaStatePointer['base_ci'].address:
        status = 1
        ar.iCi = ci
    else:
        status = 0
    
    return status

def LuaOChunkId(ar: LuaDebug):

    RETS = "..."
    PRE	= "[string \""
    POS = "\"]"

    buffLen = common.LUA_IDSIZE
    srclen = ar.srclen
    ar.shortSrc = ""
    if ar.source[0] == "=":
        if(srclen <= buffLen):
            ar.shortSrc = ar.source[1: srclen]
        else:
            ar.shortSrc += ar.source[1: buffLen]
    elif ar.source[0] == '@':
        if(srclen <= buffLen):
            ar.shortSrc = ar.source[1: srclen]
        else:
            ar.shortSrc += RETS
            buffLen -= len(RETS)
            # common.RemovePrint("src len = %s, bufflen = %s", srclen, buffLen)
            ar.shortSrc += ar.source[1 + srclen - buffLen: buffLen]
    else:
        ar.shortSrc += PRE
        buffLen -= len(PRE) + len(RETS) + len(POS) + 1

        findPos = ar.source.find('\n')
        if(srclen < buffLen and findPos == -1):
            ar.shortSrc += ar.source[:srclen]
        else:
            if(findPos != -1):
                srclen = findPos
            if(srclen > buffLen):
                srclen = buffLen
            ar.shortSrc += ar.source[:srclen]
            ar.shortSrc += RETS
        ar.shortSrc += POS


def LuaGetLocal(L: gdb.Value, ci: gdb.Value, n: int) -> Tuple[str, gdb.Value]:
    callInfo = common.CallInfoValue(L, ci)
    return LuaG_FindLocal(L, callInfo, n)


def LuaG_FindLocal(L: gdb.Value, callInfo: common.CallInfoValue, n: int) -> Tuple[str, gdb.Value]:
    callInfoPointer = callInfo.GetCallInfoPointer()
    base = callInfoPointer['func']['p'] + 1
    name = ""
    if callInfo.IsLua():
        if n < 0:
            return FingVararg(callInfo, n)
        else:
            closurePointer = callInfo.GetClosurePointer()
            name = LuaF_GetLocalName(closurePointer['l']['p'], n, callInfo.CurrentPc())
    if name == "":
        if L['ci'] == callInfoPointer:
            limit = L['top']['p']
        else:
            limit = callInfoPointer['next']['func']['p']
        if limit - base >= n and n > 0:
            name = "(temporary)" if callInfo.IsLua() else "(C temporary)"
        else:
            return "", common.Cast2TargetTypePointer(gdb.Value(0), "StackValue")
    return name, base + n - 1


def FingVararg(callInfo: common.CallInfoValue, n: int) -> Tuple[str, gdb.Value]:
    ci = callInfo.GetCallInfoPointer()
    if common.ClLvalue(common.S2V(ci['func']['p'])['p']['is_vararg']) :
        nextra = ci['u']['l']['nextraargs']
        if n >= -nextra:
            pos = ci['func']['p'] - nextra - (n + 1)
            return "vararg", pos
    return "", common.Cast2TargetTypePointer(gdb.Value(0), "StackValue")


def LuaF_GetLocalName(proto: gdb.Value, localNumber: int, pc: int) -> str:
    i = 0
    while i < int(proto['sizelocvars']) and int(proto['locvars'][i]['startpc']) <= pc:
        if(pc < int(proto['locvars'][i]['endpc'])):
            localNumber = localNumber - 1
            if(localNumber == 0):
                return common.Getstr(proto['locvars'][i]['varname'])
        i = i + 1
    return ""


def AuxUpValue(tValuePointer: gdb.Value, n: int) -> Tuple[str, common.Tvalue] :
    typeTag = common.TtypeTag(tValuePointer)
    # common.RemovePrint("typeTag = %s", typeTag)
    if typeTag == common.LUA_VCCL:
        cClosurePointer = common.ClCValue(tValuePointer)
        if(n - 1 >= cClosurePointer['nupvalues']):
            return "", None
        tValueObj = common.TValueObj(cClosurePointer['upvalue'][n - 1].address)
        return "(c upvalue, no name)", tValueObj
    elif typeTag == common.LUA_VLCL:
        lClosurePointer = common.ClLvalue(tValuePointer)
        # common.RemovePrint("lClosurePointer = %s", lClosurePointer)
        protoPointer = lClosurePointer['p']
        if(n - 1 >= protoPointer['sizeupvalues']):
            return "", None
        tValueObj = common.TValueObj(lClosurePointer['upvals'][n - 1]['v']['p'])
        name = protoPointer['upvalues'][n - 1]['name']
        if name == "":
            return "(no name)", tValueObj
        else:
            return common.Getstr(name), tValueObj
    else:
        return "", None