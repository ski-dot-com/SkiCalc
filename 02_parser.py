from math import log
from typing import Any, Callable
from operator import add,sub,mul,truediv as div,floordiv,pow,neg,pos

def tokenize(code:str)->list[str]:
	"""
	式をトークンと呼ばれる単語のようなものに切り分ける。
	"""
	tokens_old=code.split()# まずは空白で切り分ける。
	"""
	トークン候補の配列。作業を行う際、元の配列がこちらに入る。
	"""
	tokens:list[str]=[]
	"""
	トークン候補の配列。作業を行う際、結果がこちらに入る。
	"""
	for token in tokens_old:
		"""
		空白で区切った後、それぞれのトークン候補(ここでは①と呼ぶ)に対して、そのその中に演算子となる記号がないか探して、あった場合は切り出す。
		"""
		tmp_old:list[str|list[str]]=[token]
		"""
		①から生じたトークン候補の配列。作業を行う際、元の配列がこちらに入る。
		"""
		tmp:list[str|list[str]]=[]
		"""
		①から生じたトークン候補の配列。作業を行う際、結果がこちらに入る。
		"""
		for op in sorted(signs,key=len,reverse=True):# 各演算子に対して行っているが、ある演算子の中にほかの演算子としてもみなせるものが入っている場合を考慮して、長いものから順番に行う。
			for t in tmp_old:# それぞれのトークン候補に対して行っている。
				if isinstance(t, list):# 演算子の場合(演算子の場合はリストで覆うことにしている)
					tmp.append(t)# そのまま流す。
				else:# そうでない場合
					tmp+=sum(([x,[op]] for x in t.split(op)),start=[])[:-1]
					"""
					まずトークン候補をその演算子でくぎり、その間に演算子をリストで覆って入れている。
					間に演算子をリストで覆ったもの(ここでは、演算子リストと呼ぶ)を入れる処理は、まず、すべての要素の後ろに演算子リストを挿入し、最後の演算子リストを取り除くことによって行っている。
					次のようなイメージである:
					1+2+3
					↓「+」で区切る
					1,  2,  3
					↓すべての要素の後ろに「+」を挿入
					1,+,2,+,3,+
					↓最後の「+」を削除
					1,+,2,+,3
					"""
			tmp_old,tmp=tmp,[]
			"""
			次の操作のために、結果をtmp_oldに移してtmpを初期化している。
			"""
		tokens+=[t[0] if isinstance(t,list) else t for t in tmp_old]
		"""
		結果を移す処理は最後の演算子でも行われるので、tmp_oldに結果は入っている。
		ここでは、リストで覆われた演算子からリストをはがして、tokensに追加している。
		"""
	tokens=[t for t in tokens if t]# 切り分けるときに生じる空白を取り除く
	return tokens
def parse(tokens:list[str])->list[str|int|float]:
	"""
	切り分けられたトークンの配列を基に、式を解釈し、逆ポーランド記法に似た内部表現に変換する。
	"""
	code:list[str|int|float]= []
	"""
	内部表現候補。作業を行う際、結果がこちらに入る。
	"""
	for token in tokens:# 各トークンに対し、数値への変換を試みて、成功した場合は数値として解釈するようにしている。
		type:Callable[[str],int|float]
		for type in [int,float]:# 整数と少数を区別するため、整数。小数の順番で変換を試みている。
			try:
				token=type(token)
				break
			except ValueError:
				pass
		code.append(token)
	code,code_old=[],code # code_oldは、作業を行う際、元の内部表現候補が入れられる。
	stack:list[tuple[int|None,str|int]]=[]
	"""
	操車場アルゴリズムで用いられるスタックに近い働きを持つもの。
	演算子や、優先順位を示す括弧のほか、関数呼び出しの場合に、元のargcが入れられる。
	また、演算子などは優先順位(を表す数字)とともに入れられ、括弧などはNoneという特殊な値が入れられる。
	"""
	argc:int=0
	"""
	関数呼び出しの際、引数が何個あったかを示す。
	関数呼び出しがネストされた(複数重ねられた)場合には、stackに入れられる。
	"""
	after_exp=False
	"""
	式の後かどうか。
	"""
	for t in code_old:# 各トークンに対して、
		if after_exp:# 式の後であった場合
			if isinstance(t,str):# 数値でなかった場合
				if t in b_ops:# 二項演算子だった場合。
					tmp=b_ops[t][0]# 優先順位を取得
					# 操車場アルゴリズムと同様に自分より優先順位が下である演算子か開き括弧(関数呼び出し(例えば「f(3)」)か優先順位の括弧(例えば「1*(2+3)」))まで戻る(左結合性の演算子しかないので、これでいい。)
					for i in reversed(range(len(stack))):# スタックの先頭から順に
						tmp_=stack[i][0]# 先頭を見て、
						if tmp_ is None or tmp_ < tmp:break# 開き括弧であるか、自分より優先順位が下である場合は戻る処理を終了。
						code.append(stack.pop()[1])# そうでなければ流す。
					stack.append((b_ops[t][0],"b"+t))# 操車場アルゴリズムと同様に演算子をスタックに積む。このとき、先頭に二項演算子を意味する「b」をつけているのが肝である。
					after_exp=False# この後、また式が来るので偽に。
				elif t ==")":# コンマ「,」だった場合、
					# 開き括弧まで戻る
					for i in reversed(range(len(stack))):# スタックの先頭から順に
						if stack[i][1] == "(" or isinstance(stack[i][1],int):break# 先頭を見て、開き括弧の場合、戻る処理を終了。
						code.append(stack.pop()[1])# 演算子の場合は、操車場アルゴリズムと同様に流す。
					else:# スタックが無くなった場合(演算子しかなかった場合)(括弧が対応していないので不適)
						print(f"Error:  かっこが間違った使い方をされました。かっこが閉じていません。")# エラーを出す
						raise ValueError()
					tmp=stack.pop()[1]# 開き括弧をとりだして、
					if isinstance(tmp,int):# 関数呼び出しだった場合、
						code.append(argc)#  引数の個数と、
						code.append("call")#関数呼び出しを表すものを流して、
						argc=tmp# argcを復元する。
				elif t ==",":# カンマ「,」だった場合、
					# 関数呼び出しまで戻る
					for i in reversed(range(len(stack))):# スタックの先頭から順に
						tmp_=stack[i][1]# 先頭を見て、
						if isinstance(tmp_,int):break# 関数呼び出しの場合は、戻る処理を終了。
						elif stack[i][0] is None:# 関数呼び出しでなく、演算子でもなかった場合(優先順位の括弧だった場合)(優先順位の括弧内で「,」を使うことはないので不適)
							print(f"Error:  コンマが間違った使い方をされました。関数呼び出し内でのみ使ってください。")# エラーを出す
							raise ValueError()
						code.append(stack.pop()[1])# 演算子の場合は、操車場アルゴリズムと同様に流す。
					else:# スタックが無くなった場合(演算子しかなかった場合)(括弧の外で「,」を使うことはないので不適)
						print(f"Error:  コンマが間違った使い方をされました。関数呼び出し内でのみ使ってください。")# エラーを出す
						raise ValueError()
					argc+=1# 「,」が入ると引数が一個増えるので1増やす。(「f(0)」と「f(0, ...)」の違い)
					after_exp=False# この後、また式が来るので偽に。
				elif t =="(":# 開き丸かっこ「(」であった場合(関数呼び出しの始まり)
					stack.append((None,argc))# 前述の通り、argcを保存する。
					argc=1# このままいけば(「,」が入らなければ)引数は1個になるので1に。
					after_exp=False# この後、また式が来るので偽に。
				elif t in p_ops:# 二項演算子でなく前置単項演算子(前に来る演算子(例えば「-2」の「-」))であった場合(式の後に直接式が来ることはないので不適)
					print(f"Error: 前置単項演算子「{t}」が間違った使い方をされました。式の前においてください。")# エラーを出す
					raise ValueError()
				else:# (関数の)名前であった場合(式の後に数値が来ることはないので不適)
					print(f"Error: 値を直接連接させることはできません。")# エラーを出す
					raise ValueError()
			else:# 数値であった場合(式の後に数値が来ることはないので不適)
				print(f"Error: 値を直接連接させることはできません。")# エラーを出す
				raise ValueError()
		else:
			if isinstance(t,str):# 数値でなかった場合
				if t in p_ops:# 前置単項演算子であった場合
					stack.append((p_ops[t][0],"p"+t))# 操車場アルゴリズムと同様に演算子をスタックに積む。このとき、先頭に前置単項演算子を意味する「p」をつけているのが肝である。
				elif t =="(":# 「(」であった場合(優先順位の括弧の始まり)
					stack.append((None,"("))# 操車場アルゴリズムと同様に括弧をスタックに積む。
				elif t in b_ops:# 前置単項演算子でなく、二項演算子であった場合(二項演算子は前に式が必要なので不適)
					print(f"Error: 二項演算子「{t}」が間違った使い方をされました。前に式が必要です。")# エラーを出す
					raise ValueError()
				elif t ==")":# 「)」であった場合(関数呼び出しにしろ優先順位の括弧にしろ、前に式が必要なので不適)(関数の引数なし呼び出し(例えば「f()」)や最後にコンマを残しておくこと(例えば「f(1,2,)」)は禁止する)
					print(f"Error: かっこが間違った使い方をされました。閉じかっこの前に式が必要です。")# エラーを出す
					raise ValueError()
				elif t ==",":# 「,」であった場合(前に式が必要なので不適)
					print(f"Error: コンマが間違った使い方をされました。コンマの前に式が必要です。")# エラーを出す
					raise ValueError()
				else:# (関数の)名前であった場合
					code.append("v"+t)# 操車場アルゴリズムと同様にそのまま流す。このとき、先頭に名前を意味する「v」をつけているのが肝である。
					after_exp=True# 式が終わったので真に。
			else:# 数値であった場合
				code.append(t)# 操車場アルゴリズムと同様にそのまま流す。
				after_exp=True# 式が終わったので真に。
	# 終わった後に、残った演算子を取り出す。
	for i,token in reversed(stack):# スタックの先頭から順番に、
		if i is None:# 演算子以外が残っていた場合、不適なのでエラーを出す。
			match token:
				case "("|int(_):
					print("Error: かっこが間違った使い方をされました。かっこが閉じていません。")
			raise ValueError()
		code.append(token)# 演算子は操車場アルゴリズムと同様に流す。
	if not after_exp:# 式がなかった場合(明らかに不適)
		print(f"Error: 式が必要です。")# エラーを出す
		raise ValueError()
	return code
b_ops:dict[str,tuple[int,Callable[[Any,Any],Any]]]={
	"+":	(0,		add),
	"-":	(0,		sub),
	"*":	(1,		mul),
	"/":	(1,		div),
	"//":	(1,		floordiv),
	"**":	(2,		pow),
}
p_ops:dict[str,tuple[int,Callable[[Any],Any]]]={
	"+":	(10,	pos),
	"-":	(10,	neg),
}
system_vars:dict[str,Callable]={
	"inc":lambda x:x+1,
	"dec":lambda x:x-1,
	"sqrt":lambda x:x**0.5,
	"log":log
}
signs={*b_ops,*p_ops,*"(),"}
def rep():
	try:tokens:list[int|float|str]=parse(tokenize(input("> ")))
	except ValueError:return
	stack:list[int|float|Callable]=[]
	for token in tokens:
		match token:
			case int(i)|float(i):stack.append(i)
			case str(s) if s[0]=="b":
				tmp=b_ops[s[1:]]
				stack[-2:]=[tmp[1](*stack[-2:])]
			case str(s) if s[0]=="m":
				tmp=p_ops[s[1:]]
				stack[-1:]=[tmp[1](stack[-1])]
			case "call":
				tmp__=stack[-1]
				assert isinstance(tmp__,(int))
				#print(tmp__)
				tmp_=-tmp__-1
				tmp=stack[tmp_-1]
				if not callable(tmp):
					print("Error: 関数以外を呼び出そうとしました。")
					return
				stack[tmp_-1:]=[tmp(*stack[tmp_:-1])]
			case str(s) if s[0]=="v":
				stack.append(system_vars[s[1:]])
	print(stack[-1])
try:
	while True:
		rep()
except KeyboardInterrupt:
	pass
except EOFError:
	pass