
from time import strftime, localtime

def logger(func):
    def new_print(*args, **kwargs):
        now = strftime("%a, %d %b %Y %I:%M:%S %p", localtime())
        try:
            ctx = args[0]
            return func(f'[{now}][{ctx.guild}][{ctx.channel}][{ctx.author.display_name}][{ctx.author.id}]', *args[1:], **kwargs)
        except:
            return func(now, *args,**kwargs)
    return new_print