from typing import Callable
from operator import add,sub,mul,truediv as div,floordiv,pow
def tokenize(code:str)->list[str]:
	"""
	演算子と被演算子を切り分ける
	"""
	tokens=tokens_old=code.split()# 空白で切り分けて終了。
	#tokens=[]
	return tokens_old
ops={
	"+":  (2,add),
	"-":  (2,sub),
	"*":  (2,mul),
	"/":  (2,div),
	"//": (2,floordiv),
	"**": (2,pow)
}
"""
演算子とその引数の数と実行する関数のタプルの辞書です。
タプルとは、値の組のようなもので、配列のように要素を取得できますが、書き換えることはできません。
"""
try:
	while True:
		tokens_old=tokenize(input("> "))# 読み取って、演算子と被演算子を切り分けています。
		"""
		トークンの配列。作業を行う際、元の配列がこちらに入る。
		"""
		tokens:list[int|float|str]=[]
		"""
		トークンの配列。作業を行う際、結果がこちらに入る。
		"""
		for token in tokens_old:# 各トークンに対し、数値への変換を試みて、成功した場合は数値として解釈するようにしている。
			type:Callable[[str],int|float]
			for type in [int,float]:# 整数と少数を区別するため、整数。小数の順番で変換を試みている。
				try:
					token=type(token)
					break
				except ValueError:
					pass
			tokens.append(token)
		# ここから解釈が始まる。
		stack:list[int|float]=[]
		"""
		配列であるが、ここではスタックのように使っている。
		"""
		for token in tokens:# 各演算子or被演算子について、
			match token:
				case int(i)|float(i):stack.append(i)# 数値(被演算子)場合、そのままスタックに積んでいる。
				case str(s) if s in ops:# 演算子の場合
					tmp=ops[s]# その演算子の情報を取得して、
					stack[-tmp[0]:]=[tmp[1](*stack[-tmp[0]:])]# その分値をスタックから取り出して関数を実行し、結果をスタックに積んでいる。
		print(stack[-1])
except KeyboardInterrupt:
	pass
except EOFError:
	pass