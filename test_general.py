import discord
import discord.ext.commands as commands
from discord.ext.commands import Cog, command
import pytest
import pytest_asyncio
import discord.ext.test as dpytest

from cogs.tasks import ParamMapper, FileBackingStore, SheetsBackingStore, TaskManager

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


def test_file_fieldnames():
    store = FileBackingStore("test.csv")
    assert store.fieldnames == ['id', 'title', 'project', 'status', 'assigned', 'updated', 'notes']

def test_file_value():
    store = FileBackingStore("test.csv")
    assert store.get('4', 'project') == 'yoyo'
    assert store.get('1', 'assigned') == 'philion'

def test_file_find():
    store = FileBackingStore("test.csv")

    assert store.find({'status': 'jolly'})[0]['id'] == "4"

def test_file_update():
    store = FileBackingStore("test.csv")

    # confirm status=jolly
    assert store.get('4', 'status') == 'jolly'

    # update
    store.update('4', {'status': 'perturbed'})
    assert store.get('4', 'status') == 'perturbed'

    # reset to orig
    store.update('4', {'status': 'jolly'})
    assert store.get('4', 'status') == 'jolly'

# google sheets
import random
import datetime
def get_sheets_store():
    try:
        store = SheetsBackingStore("Taskbot Test Sheet")
        return TaskManager(store) # id handling was moved to task manager
    except Exception as ex:
        pytest.skip(f"Cannot load config: {ex}")

def test__sheet_add():
    tasks = get_sheets_store()
    row = {
        'title': f'Test title {random.randint(42, 9999)}',
        'project': random.choice(['acme','rocket','yoyo','skateboard']),
        'status': random.choice(['new','open','working','rejected','closed']),
        'assigned': random.choice(['unassigned','philion','wile','bugs','roadrunner']),
        'updated': datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    }

    id = tasks.add(row)
    assert id is not None, "id is missing from add() response"

    testrow = tasks.get(id)

    for name, value in row.items():
        assert str(testrow[name]) == str(value)

def test_fieldnames():
    tasks = get_sheets_store()
    assert tasks.fieldnames() == ['id', 'title', 'project', 'status', 'assigned', 'updated', 'notes']

def test_value():
    tasks = get_sheets_store()
    assert tasks.get('4')['project'] == 'yoyo'
    assert tasks.get('1')['assigned'] == 'philion'

def test_sheets_list():
    tasks = get_sheets_store()
    assert tasks.list({'status': 'jolly'})[0]['id'] == 4

def test_sheets_edit():
    tasks = get_sheets_store()

    # confirm status=jolly
    assert tasks.get('4')['status'] == 'jolly'

    # update
    tasks.edit('4', {'status': 'perturbed'})
    assert tasks.get('4')['status'] == 'perturbed'

    # reset to orig
    tasks.edit('4', {'status': 'jolly'})
    assert tasks.get('4')['status'] == 'jolly'
