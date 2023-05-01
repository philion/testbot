import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest

from cogs.tasks import ParamMapper, FileBackingStore

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

# --- the good stuff ---

@pytest.mark.asyncio
@pytest.mark.skip(reason="not yet working")
async def test_list(bot):
    await dpytest.message("!list")
    assert dpytest.verify().message().contains().content("foobar")

def test_params():
    param_strs = [
        'id=6 title=This is a title. The end.',
        '',
        'just text without param',
        'just text with param=42',
    ]

    expected = [
        {'id':'6', 'title': 'This is a title. The end.'},
        {},
        {'none': 'just text without param'},
        {'none': 'just text with', 'param': '42'},
    ]

    pm = ParamMapper()
    for i, arg_str in enumerate(param_strs):
        result = pm.parse(arg_str)
        assert result == expected[i]


def test_fieldnames():
    store = FileBackingStore("test.csv")
    assert store.fieldnames == ['id', 'title', 'project', 'status', 'assigned', 'updated', 'notes']

def test_value():
    store = FileBackingStore("test.csv")
    assert store.get('4', 'project') == 'yoyo'
    assert store.get('1', 'assigned') == 'philion'

def test_find():
    store = FileBackingStore("test.csv")

    assert store.find({'status': 'jolly'})[0]['id'] == "4"

def test_update():
    store = FileBackingStore("test.csv")

    # confirm status=jolly
    assert store.get('4', 'status') == 'jolly'

    # update
    store.update('4', {'status': 'perturbed'})
    assert store.get('4', 'status') == 'perturbed'

    # reset to orig
    store.update('4', {'status': 'jolly'})
    assert store.get('4', 'status') == 'jolly'