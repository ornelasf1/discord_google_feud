

def logger(func):
    def new_print(ctx = None, *args, **kwargs):
        if (ctx == None):
            return func(*args,**kwargs)
        else:
            return func(f'[{ctx.guild}][{ctx.channel}][{ctx.author.display_name}][{ctx.author.id}]', *args, **kwargs)
    return new_print