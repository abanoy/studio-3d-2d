extends RefCounted
static func existing_boundary(folder: String) -> String:
 var current:=ProjectSettings.globalize_path(folder).simplify_path()
 while not DirAccess.dir_exists_absolute(current):
  var parent:=current.get_base_dir()
  if parent==current or parent.is_empty():break
  current=parent
 return current
static func run(script: String,arguments: PackedStringArray) -> Dictionary:
 var python:=OS.get_environment("HYBRID_PYTHON");var output: Array=[];var args:=PackedStringArray([ProjectSettings.globalize_path("res://tools/"+script)]);args.append_array(arguments)
 var code:=OS.execute(python if not python.is_empty() else "python",args,output,false,false)
 return response(code,"" if output.is_empty() else str(output[0]))
static func response(code: int,output: String) -> Dictionary:
 if output.is_empty():return {"ok":false,"error":"Save worker ended without status. Check the configured Python and saved file before retrying.","outcome_unknown":true}
 var parser:=JSON.new()
 if parser.parse(output)!=OK or not parser.data is Dictionary:return {"ok":false,"error":"Save worker returned unreadable status. Inspect the saved file before retrying.","outcome_unknown":true}
 var result: Dictionary=parser.data
 if code==0 and result.get("ok") is bool and result.ok:return result
 result["ok"]=false
 if not result.get("error") is String or result.error.is_empty():result["error"]="Save commit failed. Inspect the saved file before retrying."
 return result
