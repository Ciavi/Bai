import asyncio

bai = None

def set_instance(bot):
    global bai
    bai = bot

def run_in_loop(func_name: str, *args):
    if bai is None:
        return

    loop = bai.loop
    func = getattr(bai, func_name)
    loop.create_task(func(*args))