from __future__ import annotations
from collections import defaultdict
from math import floor, log, sqrt
import os.path
from typing import Any, Callable, TypeAlias, ParamSpec, TypeVar
from operator import add, eq,sub,mul,truediv as div,mod,floordiv,pow,neg,pos
from functools import wraps
from traceback import print_exc
import argparse as ap

ap_main=ap.ArgumentParser(description="拡張しまくった計算機(インタプリタ)です。")
ap_main.add_argument("code",nargs="?",default=None, help="実行するファイル。なければREPL(普通の電卓)として起動。")
ap_main.add_argument("-s","--source",nargs="*",default=[], help="起動する前に実行するファイル。")
P=ParamSpec("P")
R=TypeVar("R")
class Ref:
	def __init__(self,value:Operands,name:str|None=None,*,unbound_error_message:str|None=None):
		self.__value=value
		self.unbound_error_message=unbound_error_message
		if name is not None:self.name=name
	@property
	def value(self):
		if self.unbound_error_message is not None:
			print("Error: "+self.unbound_error_message)
			raise NameError()
		return self.__value
	@value.setter
	def value(self,value):
		self.__value=value;self.unbound_error_message=None
class UndefinedNameRef:
	def __init__(self,name:str):
		self.name=name
class NonlocalNameRef(Ref,UndefinedNameRef):
	def __init__(self,ref:Ref,name:str):
		UndefinedNameRef.__init__(self,name)
		self.__ref=ref
	@property
	def value(self):return self.__ref.value
	@value.setter
	def value(self,value):
		self.__ref.value=value
class ListExp:
	def __init__(self,argc:int):
		self.argc=argc
class Block:
	def __init__(self,argc:int):
		self.argc=argc
	def __int__(self):return self.argc
class Param:
	def __init__(self,argc:int):
		self.argc=argc
	def __int__(self):return self.argc
Operands:TypeAlias=int|float|Callable|str|list[Ref]|dict[int|float|str,Ref]|defaultdict[int|float|str,Ref]
StackItem:TypeAlias=Operands|Ref|UndefinedNameRef
def tokenize(code:str)->list[str]:
	str_mode=0
	tokens:list[str]=[]
	for s in code.split('"'):
		match str_mode:
			case 0:
				if tokens and not s:
					tokens[-1]+='"'
				else:
					tokens.append(s)
					tokens.append('"')
				str_mode=1
			case 1:
				tokens[-1]+=s
				str_mode=0
	if not str_mode:
		print(f"Error:  ダブルクォーテーションが間違った使い方をされました。文字列が閉じていません。")
		raise ValueError()
	tokens[-1]=tokens[-1][:-1]
	tokens_old=sum([[s] if i%2 else s.split() for i,s in enumerate(tokens)],[])
	tokens=[]
	for token in tokens_old:
		if not token:continue
		if token[0]=='"':
			tokens.append(token)
			continue
		tmp_old:list[str|list[str]]=[token]
		tmp:list[str|list[str]]=[]
		for op in sorted(signs,key=len,reverse=True):
			for t in tmp_old:
				if isinstance(t, list):
					tmp.append(t)
				else:
					#print(f"{t}.split({op})")
					tmp+=sum(([x,[op]] for x in t.split(op)),start=[])[:-1]
			tmp_old,tmp=tmp,[]
		tokens+=[t[0] if isinstance(t,list) else t for t in tmp_old]
	tokens=[t for t in tokens if t]
	#print(tokens)
	return tokens
def parse_num(s:str, raise_error:bool=True):
	type:Callable[[str],int|float]
	for type in [int,float]:
		try:
			return type(s)
		except ValueError:
			pass
	if raise_error:
		print(f"Error: 文字列「{s}」を数に変換できませんでした。")
		raise ValueError()
def parse(tokens:list[str], is_single:bool=False)->list[str|int|float]:
	code:list[str|int|float]= []
	for token in tokens:
		tmp=parse_num(token,False)
		code.append(tmp if tmp is not None else token)
	
	code,code_old=[],code
	stack:list[tuple[int|None,str|int]|tuple[None,ListExp|Param|Block]]=[]
	argc:int=0
	after_exp=False
	for t in code_old:
		if after_exp:
			if isinstance(t,str):
				if t in b_ops:
					tmp=b_ops[t][0]
					for i in reversed(range(len(stack))):
						tmp_=stack[i][0]
						if tmp_ is None or tmp_ < tmp or tmp_ == tmp in r_op_level:break
						code.append(stack.pop()[1])  # type: ignore
					stack.append((b_ops[t][0],"b"+t))
					after_exp=False
				elif t ==")":
					for i in reversed(range(len(stack))):
						if stack[i][1] == "(" or isinstance(stack[i][1],int):break
						elif stack[i][0] is None:
							print(f"Error:  丸かっこが間違った使い方をされました。かっこは同じ種類のかっこで閉じてください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						print(f"Error:  丸かっこが間違った使い方をされました。かっこが閉じていません。")
						raise ValueError()
					tmp=stack.pop()[1]
					if isinstance(tmp,int):
						code.append(argc)
						code.append("call")
						argc=tmp
				elif t =="]":
					for i in reversed(range(len(stack))):
						if stack[i][1] == "[" or isinstance(stack[i][1],ListExp):break
						elif stack[i][0] is None:
							print(f"Error:  角かっこが間違った使い方をされました。かっこは同じ種類のかっこで閉じてください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						print(f"Error:  角かっこが間違った使い方をされました。かっこが閉じていません。")
						raise ValueError()
					tmp=stack.pop()[1]
					if isinstance(tmp,ListExp):
						code.append(argc)
						code.append("list")
						argc=tmp.argc
					elif tmp=="[":
						code.append("index")
				elif t =="}":
					for i in reversed(range(len(stack))):
						if isinstance(stack[i][1],Block):break
						elif stack[i][0] is None:
							print(f"Error:  波かっこが間違った使い方をされました。かっこは同じ種類のかっこで閉じてください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						print(f"Error:  波かっこが間違った使い方をされました。かっこが閉じていません。")
						raise ValueError()
					tmp=stack.pop()[1]
					if isinstance(tmp,Block):
						code.append("}")
						argc=tmp.argc
				elif t ==",":
					for i in reversed(range(len(stack))):
						tmp_=stack[i][1]
						if isinstance(tmp_,(int,ListExp,Block)):break
						elif stack[i][0] is None:
							print(f"Error:  コンマが間違った使い方をされました。関数呼び出し、リスト式、もしくはブロック内でのみ使ってください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						if is_single:
							print(f"Error:  コンマが間違った使い方をされました。関数呼び出し、リスト式、もしくはブロック内でのみ使ってください。")
							raise ValueError()
					argc+=1
					after_exp=False
				elif t =="(":
					for i in reversed(range(len(stack))):
						tmp_=stack[i][0]
						if tmp_ is None or tmp_ < CALL_LEVEL or tmp_ == CALL_LEVEL in r_op_level:break
						code.append(stack.pop()[1])  # type: ignore
					stack.append((None,argc))
					argc=1
					after_exp=False
				elif t =="[":
					for i in reversed(range(len(stack))):
						tmp_=stack[i][0]
						if tmp_ is None or tmp_ < CALL_LEVEL or tmp_ == CALL_LEVEL in r_op_level:break
						code.append(stack.pop()[1])  # type: ignore
					stack.append((None,"["))
					after_exp=False
				elif t in p_ops:
					print(f"Error: 前置単項演算子「{t}」が間違った使い方をされました。式の前においてください。")
					raise ValueError()
				else:
					print(f"Error: 値を直接連接させることはできません。")
					raise ValueError()
			else:
				print(f"Error: 値を直接連接させることはできません。")
				raise ValueError()
		else:
			if isinstance(t,str):
				if t[0]=='"':
					code.append(t)  # type: ignore
					after_exp=True
				elif t in p_ops:
					stack.append((p_ops[t][0],"p"+t))
				elif t =="(":
					stack.append((None,"("))
				elif t =="[":
					stack.append((None,ListExp(argc)))
					argc=1
				elif t =="{":
					stack.append((None,Block(argc)))
					code.append("{")
					argc=1
				elif t in b_ops:
					print(f"Error: 二項演算子「{t}」が間違った使い方をされました。前に式が必要です。")
					raise ValueError()
				elif t ==")":
					for i in reversed(range(len(stack))):
						if isinstance(stack[i][1],int):break
						elif stack[i][1] == "(":
							print(f"Error: 丸かっこが間違った使い方をされました。閉じかっこの前に式が必要です。")
							raise ValueError()
						elif stack[i][0] is None:
							print(f"Error:  丸かっこが間違った使い方をされました。かっこは同じ種類のかっこで閉じてください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						print(f"Error:  丸かっこが間違った使い方をされました。かっこが閉じていません。")
						raise ValueError()
					tmp=stack.pop()[1]
					if isinstance(tmp,int):
						code.append(argc-1)
						code.append("call")
						argc=tmp
					after_exp=True
				elif t =="]":
					for i in reversed(range(len(stack))):
						if isinstance(stack[i][1],ListExp):break
						elif stack[i][1] == "[":
							print(f"Error: 角かっこが間違った使い方をされました。閉じかっこの前に式が必要です。")
							raise ValueError()
						elif stack[i][0] is None:
							print(f"Error:  角かっこが間違った使い方をされました。かっこは同じ種類のかっこで閉じてください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						print(f"Error:  角かっこが間違った使い方をされました。かっこが閉じていません。")
						raise ValueError()
					tmp=stack.pop()[1]
					if isinstance(tmp,ListExp):
						code.append(argc-1)
						code.append("list")
						argc=tmp.argc
					after_exp=True
				elif t =="}":
					for i in reversed(range(len(stack))):
						if isinstance(stack[i][1],Block):break
						elif stack[i][0] is None:
							print(f"Error:  波かっこが間違った使い方をされました。かっこは同じ種類のかっこで閉じてください。")
							raise ValueError()
						code.append(stack.pop()[1])  # type: ignore
					else:
						print(f"Error:  角かっこが間違った使い方をされました。かっこが閉じていません。")
						raise ValueError()
					tmp=stack.pop()[1]
					if isinstance(tmp,Block):
						code.append(0)
						code.append("}")
						argc=tmp.argc
					after_exp=True
				elif t ==",":
					print(f"Error: コンマが間違った使い方をされました。コンマの前に式が必要です。")
					raise ValueError()
				else:
					code.append("v"+t)
					after_exp=True
			else:
				code.append(t)
				after_exp=True
	for i,token in reversed(stack):
		if i is None:
			match token:
				case "(":
					print("Error: かっこが間違った使い方をされました。かっこが閉じていません。")
				case int(_):
					print("Error: かっこが間違った使い方をされました。かっこが閉じていません。")
			raise ValueError()
		code.append(token)  # type: ignore
	if not after_exp:
		print(f"Error: 式が必要です。")
		raise ValueError()
	return code
def as_value(v:Ref|UndefinedNameRef|Operands)->Operands:
	if isinstance(v,Ref):return v.value
	elif isinstance(v,UndefinedNameRef):
		print(f"Error: 「{v.name}」という変数および関数は見つかりませんでした。")
		raise NameError()
	return v
def arg_as_value(f:Callable[P,R])->Callable[P,R]:
	@wraps(f)
	def res(*args:P.args,**kwargs:P.kwargs)->R:
		return f(*(as_value(x)for x in args),**{k:as_value(v)for k,v in kwargs.items()})  # type: ignore
	return res
def get_var(name:str)->Ref|UndefinedNameRef:
	tmp=scopes[0].get(name)
	if tmp is not None:
		return tmp 
	tmp=next(iter(scope[name] for scope in scopes if name in scope),None)
	if tmp is None:
		return UndefinedNameRef(name)
	return NonlocalNameRef(tmp,name)
def set_var(ref:UndefinedNameRef|Ref,value:Operands|Ref)->Operands:
	if not isinstance(ref,Ref):
		name=ref.name
		ref=global_scope[name]=Ref(0,name)
	tmp=ref.value=as_value(value)
	return tmp
def def_var(ref:UndefinedNameRef)->Ref:
	if isinstance(ref,UndefinedNameRef):
		name=ref.name
		tmp=scopes[0][name]=Ref(0,name)
	else:
		print(f"Error: 変数「{ref.name}」は、既に定義されてます。")
		raise NameError()
	return tmp
normal_ops={k:(i,arg_as_value(v))for k,(i,v) in{
	"+":  (0,  add),
	"-":  (0,  sub),
	"*":  (1,  mul),
	"/":  (1,  div),
	"%":  (1,  mod),
	"//": (1,  floordiv),
	"**": (2,  pow),
}.items()}
b_ops:dict[str,tuple[int,Callable[[Any,Any],Any]]]={**normal_ops,**{
	k+"=": (-10, (lambda v:lambda l,r:
			set_var(l,v(l,r))
		)(v))for k,(_,v) in normal_ops.items()
},
	"=":  (-10, set_var),
}
r_op_level={-10}
"""
右結合である優先順位の集合。
"""
CALL_LEVEL=100
"""
関数呼び出しなどの優先順位。
"""
def get_name(ref): # unused
	"""【未使用】"""
	if hasattr(ref,"name"):return ref.name
	else:
		print("Error: 変数以外の名前を取得できません。")
		raise NameError()
p_ops:dict[str,tuple[int,Callable[[Any],Any]]]={**{k:(i,arg_as_value(v))for k,(i,v) in{
	"+": (10, pos),
	"-": (10, neg),
}.items()},
	"$": (110, get_var)
}
def inc(x):x.value+=1
def dec(x):x.value-=1
signs={*b_ops,*p_ops,*"(),[]{}"}
class UserFunc:
	def __init__(self, sub_t:list[int|float|str]) -> None:
		self.scs=scopes
		self.sub_t=sub_t
	def __call__(self,*args):
		global scopes
		scopes_old,scopes = scopes,[{"args":Ref([Ref(as_value(a))for a in args],"args")},*self.scs]
		res=eval_(self.sub_t)
		scopes=scopes_old
		return res
	def start_tail_rec(self,args):
		global scopes
		scopes=[{"args":Ref([Ref(as_value(a))for a in args],"args")},*self.scs]
		return self.sub_t
	def __repr__(self):return "{"+repr_code(self.sub_t)+"}"
# def UserFunc(sub_t:list[int|float|str]):
# 	scs=scopes
# 	def res(*args):
# 		global scopes
# 		scopes_old,scopes = scopes,[{"args":[as_value(a)for a in args]},*scs]
# 		res=eval_(sub_t)
# 		scopes=scopes_old
# 		return res
# 	return res
def rep():
	"""
	コードを一行分読み、評価し、結果を表示する関数。
	これを無限ループに入れれば、REPLが出来上がる。
	"""
	try: repr_print(eval_(read()))
	except NameError:return
	except ValueError:return
def read():
	"""
	コードを一行分読んで、解釈する。
	結果は逆ポーランド記法的な内部表現になる。
	"""
	return parse(tokenize(input("> ")), True)
def eval_(tokens:list[int|float|str])->StackItem:
	try:
		#print(tokens)
		tokens=[*tokens]
		stack:list[StackItem]=[]
		sub_t:list[int|float|str]=[]
		nest_level=0
		last_tok_i=len(tokens)-1
		for (index,token) in enumerate(tokens):
			if nest_level:
				match token:
					case "{":
						nest_level+=1
					case "}":
						nest_level-=1
				if nest_level:
					sub_t.append(token)
				else:
					stack.append(UserFunc(sub_t))
			else:
				match token:
					case int(i)|float(i):stack.append(i)
					case str(s) if s[0]=="b":
						tmp=b_ops[s[1:]]
						stack[-2:]=[tmp[1](*stack[-2:])]
					case str(s) if s[0]=="p":
						tmp=p_ops[s[1:]]
						stack[-1:]=[tmp[1](stack[-1])]
					case "call":
						tmp__=stack[-1]
						assert isinstance(tmp__,(int))
						#print(tmp__)
						tmp_=-tmp__-1
						tmp=as_value(stack[tmp_-1])
						if not callable(tmp):
							print("Error: 関数以外を呼び出そうとしました。")
							raise ValueError()
						if index == last_tok_i and isinstance(tmp,UserFunc):
							tokens.extend(tmp.start_tail_rec(stack[tmp_:-1]))
							last_tok_i=len(tokens)-1
						else:
							stack[tmp_-1:]=[tmp(*stack[tmp_:-1])]
					case "list":
						tmp__=stack[-1]
						assert isinstance(tmp__,(int))
						#print(stack)
						#print(tmp__)
						tmp_=-tmp__-1
						stack[tmp_:]=[[Ref(as_value(x))for x in stack[tmp_:-1]]]
					case "{":
						nest_level+=1
						sub_t=[]
					case "index":
						tmp=as_value(stack[-2])
						tmp_=as_value(stack[-1])
						if isinstance(tmp,(list,str)):
							if (not isinstance(tmp_,(int,float)) or floor(tmp_)!=tmp_):
								print("Error: 整数以外はリストと文字列に添え字として使えません。")
								raise ValueError()
							stack[-2:]=[tmp[int(tmp_)]]
						elif isinstance(tmp,dict):
							if (not isinstance(tmp_,(int,float,str))):
								print("Error: 数と文字列以外は辞書に添え字として使えません。")
								raise ValueError()
							if (not isinstance(tmp,defaultdict)) and tmp_ not in tmp:
								tmp[tmp_]=Ref(0,unbound_error_message="辞書の存在しないキーを参照しようとしました。")
							stack[-2:]=[tmp[tmp_]]
						else:
							print("Error: リストと文字列と辞書以外に添え字を使えません。")
							raise ValueError()
						
					case str(s) if s[0]=="v":
						stack.append(get_var(s[1:]))
					case str(s) if s[0]=='"':
						stack.append(s[1:])
		as_value(stack[-1])
		tmp=stack[-1]
		return tmp
	except NameError:raise
	except ValueError:raise
	except Exception:
		print_exc();raise ValueError()
def repr_code(tokens:list[int|float|str]):
	stack:list[str]=[]
	sub_t:list[int|float|str]=[]
	nest_level=0
	for token in tokens:
		if nest_level:
			match token:
				case "{":
					nest_level+=1
				case "}":
					nest_level-=1
			if nest_level:
				sub_t.append(token)
			else:
				stack.append(repr_code(sub_t))
		else:
			match token:
				case int(i)|float(i):stack.append(repr(i))
				case str(s) if s[0]=="b":
					stack[-2:]=[s[1:].join(stack[-2:])]
				case str(s) if s[0]=="p":
					stack[-1:]=[s[1:]+stack[-1]]
				case "call":
					tmp__=int(stack[-1])
					#print(tmp__)
					tmp_=-tmp__-1
					stack[tmp_-1:]=[f"{stack[tmp_-1]}({', '.join(stack[tmp_:-1])})"]
				case "list":
					tmp__=int(stack[-1])
					tmp_=-tmp__-1
					stack[tmp_:]=[f"[{', '.join(stack[tmp_:-1])}]"]
				case "{":
					nest_level+=1
					sub_t=[]
				case "index":
					stack[-2:]=[f"{stack[-2]}[{stack[-1]}]"]
				case str(s) if s[0]=="v":
					stack.append(s[1:])
				case str(s) if s[0]=='"':
					stack.append(s.replace('"','""')[1:]+'"')
	return ", ".join(stack)
def repr_print(v:StackItem):
	print(repr_(v,True))
SPECIAL_VALUE_DISC_DICT={
	0: "偽orなし",
	1: "真",
}
def repr_(v:StackItem,readable:bool=False):
	if isinstance(v,(Ref,UndefinedNameRef)):return repr_(as_value(v))
	if isinstance(v,str):return '"'+v.replace('"','""')+'"'+(f" (「{v}」)" if readable else "")
	if isinstance(v,list):return f'[{", ".join(repr_(i)for i in v)}]'
	if isinstance(v,defaultdict):
		tmp=repr_(v.default_factory()) # type: ignore
		return f'dict({", ".join((*(repr_(k)+","+repr_(v)for k,v in v.items() if not(isinstance(v,Ref)and v.unbound_error_message is not None)),tmp))})'
	if isinstance(v,dict):return f'dict({", ".join(repr_(k)+","+repr_(v)for k,v in v.items() if not(isinstance(v,Ref)and v.unbound_error_message is not None))})'
	return str(v) +(f" ({SPECIAL_VALUE_DISC_DICT[v]})" if readable and v in SPECIAL_VALUE_DISC_DICT else "")
local_dir:str=os.path.dirname(__file__)
lib_dir:str=os.path.join(local_dir,"lib")
def import_(path:str,src:bool=False):
	global local_dir,global_scope,scopes
	if path.startswith("@"):
		path=os.path.abspath(os.path.join(lib_dir,path[1:]))
	else:
		path=os.path.abspath(os.path.join(local_dir,path))
	if not os.path.exists(path):
		path+=".sc"
	if not src:
		old_local_dir,local_dir=local_dir,os.path.dirname(path)
		old_global_scope,global_scope=global_scope,{}
		old_scopes,scopes=scopes,[global_scope,builtin_scope]
		with open(path,"r") as f:
			eval_(parse(tokenize(f.read())))
		res=global_scope
		local_dir,global_scope,scopes=old_local_dir,old_global_scope,old_scopes
		return res
	else:
		with open(path,"r") as f:
			eval_(parse(tokenize(f.read())))
		return 0

def list_(iter):
	return list(Ref(as_value(i))for i in iter)
builtin_scope:dict[str,Ref]={**{k:Ref(arg_as_value(v),k)for k,v in{
	"sqrt":        sqrt,
	"log":         log,
	"len":         len,
	"sign":        lambda a:0 if a == 0 else a//abs(a),
	"eq":          lambda l,r:int(eq(l,r)),
	"is_list":     lambda x:int(isinstance(x,list)),
	"is_str":      lambda x:int(isinstance(x,str)),
	"is_num":      lambda x:int(isinstance(x,(int,float))),
	"is_int":      lambda x:int(isinstance(x,(int,float))and floor(x)==x),
	"is_func":     lambda x:int(callable(x)),
	"is_dict":     lambda x:int(isinstance(x,dict)),
	"has_default": lambda x:int(isinstance(x,defaultdict)),
	"floor":       floor,
	"read_code":   lambda:UserFunc(read()),
	"ask_num":     lambda prompt=">":parse_num(input(prompt)),
	"ask_str":     lambda prompt=">":input(prompt),
	"parse_code":  lambda code:UserFunc(parse(tokenize(code))),
	"parse_num":   parse_num,
	"repr":        repr_,
	"print":       lambda v:(print(v if isinstance(v,str) else repr_(v)),0)[-1],
	"import":      lambda path:import_(path),
	"source":      lambda path:import_(path,True),
	"dict":        lambda*args:[defaultdict(lambda:Ref(args[-1]),content) if len(args) % 2 else content for content in [{k:Ref(v)for i in range(0,len(args)-1,2)for k,v in [[args[i],args[i+1]]]}]][-1],
	"keys":        lambda d:list_(d)if isinstance(d,dict)else list_(range(len(d))),
	"values":      lambda d:list_(d.values())if isinstance(d,dict)else list_(d),
	"call":        lambda func,args:func(*(as_value(arg)for arg in args))
}.items()},
	"list": lambda*x:list_(x),
	"def":  Ref(def_var,"def"),
	"inc":  Ref(inc,"inc"),
	"dec":  Ref(dec,"dec"),
	"if":   Ref(lambda c,t,f=lambda:0:t()if as_value(c) else f())
}
global_scope:dict[str,Ref]={}
scopes:list[dict[str,Ref]]=[global_scope,builtin_scope]
default_scopes=scopes
def main():
	global scopes,local_dir
	args=ap_main.parse_args()
	code=args.code
	for p in args.source:
		print(p)
		import_(p,True)
	if code is not None:
		code=os.path.abspath(code)
		local_dir=os.path.dirname(code)
		with open(code) as c:
			try:print("実行結果: "+repr_(eval_(parse(tokenize(c.read()))), True))
			except ValueError:pass
			except NameError: pass
	else:
		try:
			while True:
				rep()
				scopes=default_scopes
		except KeyboardInterrupt:
			pass
		except EOFError:
			pass
if __name__=="__main__":main()