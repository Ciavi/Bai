import asyncio

from __init__ import logger

bai = None

def set_instance(bot):
    global bai
    bai = bot

def run_in_loop(func_name: str, *args):
    if bai is None:
        logger.critical("Timekeeper: bai is none.")
        return

    loop = asyncio.get_event_loop()
    func = getattr(bai, func_name)
    loop.create_task(func(*args))