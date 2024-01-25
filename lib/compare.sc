def(lt)={  eq(sign(args[0]-args[1]),-1)},
def(gt)={  eq(sign(args[0]-args[1]), 1)},
def(le)={1-eq(sign(args[0]-args[1]), 1)},
def(ge)={1-eq(sign(args[0]-args[1]),-1)},
def(ne)={1-bind(eq,args)}