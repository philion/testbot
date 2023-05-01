import glob
import os
import pytest_asyncio
import discord
import discord.ext.commands as commands
import discord.ext.test as dpytest
from discord.ext.commands import Cog, command
import logging

log = logging.getLogger("testbot.test")
logging.getLogger().setLevel(logging.DEBUG)

class Misc(Cog):
    @command()
    async def ping(self, ctx):
        await ctx.send("Pong !")

    @command()
    async def echo(self, ctx, text: str):
        await ctx.send(text)

@pytest_asyncio.fixture
async def bot():
    intents = discord.Intents.default()
    intents.members = True
    intents.message_content = True
    b = commands.Bot(command_prefix="!",
                     intents=intents)
    await b._async_setup_hook()  # setup the loop

    await b.add_cog(Misc())
    await load_cogs(b)

    dpytest.configure(b)
    return b


@pytest_asyncio.fixture(autouse=True)
async def cleanup():
    yield
    await dpytest.empty_queue()


def pytest_sessionfinish(session, exitstatus):
    """ Code to execute after all tests. """

    # dat files are created when using attachements
    print("\n-------------------------\nClean dpytest_*.dat files")
    fileList = glob.glob('./dpytest_*.dat')
    for filePath in fileList:
        try:
            os.remove(filePath)
        except Exception:
            print("Error while deleting file : ", filePath)


async def load_cogs(bot) -> None:
    """
    The code in this function is executed whenever the bot will start.
    """
    p = f"{os.path.abspath(os.path.dirname(__file__))}/cogs"
    log.info(f"Loading from {p}")

    for file in os.listdir(p): # .. from test dir
        if file.endswith(".py"):
            extension = file[:-3]
            log.info(f"Loading {extension}")
            try:
                await bot.load_extension(f"cogs.{extension}")
                log.info(f"Loaded extension '{extension}'")
            except Exception as e:
                exception = f"{type(e).__name__}: {e}"
                log.error(f"Failed to load extension {extension}\n{exception}")
