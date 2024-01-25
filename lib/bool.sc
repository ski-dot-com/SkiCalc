def(bool)={1-eq(args[0],0)},
def(and)={bool(args[0]*args[1])},
def(or)={bool(bool(args[0])+bool(args[1]))},
def(xor)={bool(bool(args[0])-bool(args[1]))},
def(not)={1-bool(args[0])},
def(nand)={not(call(and,args))},
def(nor)={not(call(or,args))},
def(xnor)={not(call(xor,args))}