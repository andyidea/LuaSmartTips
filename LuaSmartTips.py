import sublime, sublime_plugin
import re, os, itertools

compLua = [
    ("_G", "_G"),
    ("_VERSION", "_VERSION"),
	("assert", "assert"),
	("collectgarbage", "collectgarbage"),
	("dofile", "dofile"),
	("error", "error"),
	("getmetatable", "getmetatable"),
	("ipairs", "ipairs"),
	("pairs", "pairs"),
	("load", "load"),
	("loadfile", "loadfile"),
	("next", "next"),
	("pcall", "pcall"),
	("print", "print"),
	("rawequal", "rawequal"),
	("rawget", "rawget"),
	("rawlen", "rawlen"),
	("rawset", "rawset"),
	("require", "require"),
	("select", "select"),
	("setmetatable", "setmetatable"),
	("tonumber", "tonumber"),
	("tostring", "tostring"),
	("type", "type"),
	("xpcall", "xpcall"),

	("coroutine", "coroutine"),
	("math", "math"),
	("os", "os"),
	("string", "string"),
	("table", "table"),
	("io", "io"),
]

branchLua = {
	"coroutine" : [
		("create", "create"),
		("isyieldable", "isyieldable"),
		("resume", "resume"),
		("running", "running"),
		("status", "status"),
		("wrap", "wrap"),
		("yield", "yield"),
	],
	"math" : [
		("abs", "abs"),
		("acos", "acos"),
		("asin", "asin"),
		("atan", "atan"),
		("ceil", "ceil"),
		("cos", "cos"),
		("deg", "deg"),
		("exp", "exp"),
		("floor", "floor"),
		("fmod", "fmod"),
		("huge", "huge"),
		("log", "log"),
		("max", "max"),
		("maxinteger", "maxinteger"),
		("min", "min"),
		("mininteger", "mininteger"),
		("modf", "modf"),
		("pi", "pi"),
		("rad", "rad"),
		("random", "random"),
		("randomseed", "randomseed"),
		("sin", "sin"),
		("sqrt", "sqrt"),
		("tan", "tan"),
		("tointeger", "tointeger"),
		("type", "type"),
		("ult", "ult"),
	],
	"os" : [
		("clock", "clock"),
		("date", "date"),
		("difftime", "difftime"),
		("execute", "execute"),
		("exit", "exit"),
		("getenv", "getenv"),
		("remove", "remove"),
		("rename", "rename"),
		("setlocale", "setlocale"),
		("time", "time"),
		("tmpname", "tmpname"),
	],
	"string" : [
		("byte", "byte"),
		("char", "char"),
		("dump", "dump"),
		("find", "find"),
		("format", "format"),
		("gmatch", "gmatch"),
		("gsub", "gsub"),
		("len", "len"),
		("lower", "lower"),
		("match", "match"),
		("pack", "pack"),
		("packsize", "packsize"),
		("rep", "rep"),
		("reverse", "reverse"),
		("sub", "sub"),
		("unpack", "unpack"),
		("upper", "upper"),
	],
	"table" : [
		("concat", "concat"),
		("insert", "insert"),
		("move", "move"),
		("pack", "pack"),
		("remove", "remove"),
		("sort", "sort"),
		("unpack", "unpack"),
	],
	"io" : [
		("close", "close"),
		("flush", "flush"),
		("input", "input"),
		("lines", "lines"),
		("open", "open"),
		("output", "output"),
		("popen", "popen"),
		("read", "read"),
		("stderr", "stderr"),
		("stdin", "stdin"),
		("stdout", "stdout"),
		("tmpfile", "tmpfile"),
		("type", "type"),
		("write", "write"),
	],
}

compAll = list(compLua)

class LuaSmartTips(sublime_plugin.EventListener):
    def on_query_completions(self, view, prefix, locations):
        global compAll
        global branchLua
        if not (view.match_selector(locations[0], 'source.lua -string -comment -constant')):
            return []
        pt = locations[0] - len(prefix) - 1
        # get the character before the trigger
        ch = view.substr(sublime.Region(pt, pt + 1)) if pt >= 0 else None
        if ch == '.':
        	word = view.word(pt - 1) if pt >= 0 else None
        	word = view.substr(word) if word is not None else None
        	compFull = list(branchLua[word])
        	return (compFull, sublime.INHIBIT_WORD_COMPLETIONS |
            sublime.INHIBIT_EXPLICIT_COMPLETIONS)
        compDefault = [view.extract_completions(prefix)]
        compDefault = [(item + "\tDefault", item) for sublist in compDefault 
            for item in sublist if len(item) > 3]
        compDefault = list(compDefault)
        compFull = compAll
        compFull.extend(compDefault)
        compFull = list(set(compFull))
        compFull.sort()
        return (compFull, sublime.INHIBIT_WORD_COMPLETIONS |
            sublime.INHIBIT_EXPLICIT_COMPLETIONS)

class RequireSmartTips(sublime_plugin.EventListener):
	
	@staticmethod
	def filter_lua_files(filenames):
		for f in filenames:
			fname, ext = os.path.splitext(f)
			if ext == ".lua" or ext == ".luac":
				yield fname
	
	def on_query_completions(self, view, prefix, locations):
		if view.settings().get("syntax") != "Packages/Lua/Lua.tmLanguage":
			# Not Lua, don't do anything.
			return
		
		proj_file = view.window().project_file_name()
		if not proj_file:
			# No project
			return
		
		location = locations[0]
		src = view.substr(sublime.Region(0, location))
		
		match = re.search(r"""require\s*\(?\s*["']([^"]*)$""", src)
		if not match:
			return
		
		module_path = match.group(1).split(".")
		
		results = []
		proj_dir = os.path.dirname(proj_file)
		
		for proj_subdir in view.window().project_data()["folders"]:
			proj_subdir = proj_subdir["path"]
			cur_path = os.path.join(proj_dir, proj_subdir, *(module_path[:-1]))
			print("curpath:", cur_path)
			if not os.path.exists(cur_path) or not os.path.isdir(cur_path):
				continue
			
			_, dirs, files = next(os.walk(cur_path)) # walk splits directories and regular files for us
			
			results.extend(map(lambda x: (x+"\tsubdirectory", x+"."), dirs))
			results.extend(map(lambda x: (x+"\tmodule", x), RequireAutocomplete.filter_lua_files(files)))
		
		return results, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS