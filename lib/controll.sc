def(while)={
    def(args_)=values(args),
    if(args[0](),{args_[1](),while(args_[0],args_[1])}),
},
def(do_while)={
    args[1](),
    call(while,args),
},
def(for)={
    args[0](),
    def(args_)=values(args),
    while(args[1],{
        args_[3](),
        args_[2](),
    }),
}