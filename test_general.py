import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest


@pytest.mark.asyncio
async def test_ping(bot):
    await dpytest.message("!ping")
    assert dpytest.verify().message().content("Pong !")


@pytest.mark.asyncio
async def test_echo(bot):
    await dpytest.message("!echo Hello world")
    assert dpytest.verify().message().contains().content("Hello")

@pytest.mark.asyncio
async def test_reverse(bot):
    await dpytest.message("!reverse hello")
    assert dpytest.verify().message().content("olleh")
    