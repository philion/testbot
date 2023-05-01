import csv
import discord
from discord.ext import commands
from tabulate import tabulate
import logging
import re

log = logging.getLogger("tasks")

async def setup(bot):
    store = FileBackingStore("test.csv")
    manager = TaskManager(store)
    await bot.add_cog(TaskCog(bot, manager))


# maps arg strs into param dicts.
class ParamMapper(commands.Converter):
    def parse(self, param_str):
        params = {}
        last_key = ""
        rest = ""
        for tok in re.split(r'[:=]', param_str):
            try:
                # split on last whitespace
                keyi = tok.rindex(' ')
                key = tok[keyi:].strip()
                rest = tok[:keyi].strip()
            except Exception as ex:
                log.debug(f"Exception: {ex}")
                log.debug(f'"last: {last_key}", "rest: {rest}"')

                # rest contains free-floating params, capture them
                if  len(rest) > 0:
                    params['none'] = rest

                # special end condition: no spaces in last segment
                key = tok.strip()
                rest = key

            # special end condition: last segment has a space, and key has the last segment
            # how can I detect before the split loop break? don't bother, just re-add? but lastkey has been updated.

            if last_key != "" and rest != "":
                params[last_key] = rest
                #print(f'"{last_key}", "{rest}"')
            last_key = key

        # condition breaking split-loop:
        # params contains everything correctly except last_key, which is supposed to be appended to the actual value of the last key.
        try:
            # edge conditions
            # param_str is empty, so no params
            if not param_str:
                log.debug("param_str is empty")
                return {} 
            elif len(params) == 0:
                # single param, return with 'none' to denote no args noted
                # 'none' should also grab any args without params
                log.debug(f"param_str is without params: {param_str}")
                return {'none': param_str}
            params[list(params)[-1]] = tok.strip()
        except Exception as ex:
            log.error(f"Error: {ex}")
            log.debug(f"params:{params}")
            log.debug(f"tok{tok}")
            log.debug(f"{last_key}")
            log.debug(f"{rest}")

        return params

    async def convert(self, ctx, argument):
        params = self.parse(argument)
        return params
 
 
class TaskCog(commands.Cog):
    def __init__(self, bot, manager):
        self.bot = bot
        self.manager = manager
        self.fields = bot.store.fieldnames # fixme looks like control coupling
        log.debug(f"init TaskCog with {self.fields}")

    @commands.command()
    async def add(self, ctx, *, params: ParamMapper()):
        none_value = params.pop('none', None)
        if none_value:
            # in this case, assume default key 'title'
            params['title'] = none_value
            # TODO there needs to be a general way to handle the tag-less defaults

        id = self.manager.add(params)
        await ctx.send(f'Added id={id} with {params}')

    @commands.command()
    async def edit(self, ctx, *, member: discord.Member = None):
        pass

    @commands.command()
    #async def list(self, ctx, arg):
    async def list(self, ctx, *, params: ParamMapper() = {}):
        #params = self.mapper.parse(arg) # a string with everything
        log.debug(f"list {params}")

        result = self.manager.find(params)

        table = self.render_table(result)
        await ctx.send(table)

    def render_table(self, dataset):
        # TODO table headers and formatting
        return f"```\n{tabulate(dataset)}\n```"
    
class TaskManager():
    def __init__(self, store):
        self.store = store

    def add(self,  params):
        none_value = params.pop('none', None)
        if none_value:
            # in this case, assume default key 'title'
            params['title'] = none_value
            # TODO there needs to be a general way to handle the tag-less defaults

        if 'id' not in params:
            params['id'] = self.gen_id()

        log.debug(f"params after id: {params}")
        return self.store.add(params)
    
    def gen_id(self):
        # just get the number of records and add 1.
        num_rows = self.store.count()

        log.debug(f"num_rows from store: {num_rows}")

        # note: num_rows contains the length including the header row.
        # -1 to remove header, +1 to add new row
        id = num_rows

        # there's intended flexibility ar
        return id
    
    def edit(self, id, params):
        self.store.update(id, params)
        pass

    def get(self, id):
        return self.store.row(id)

    def list(self, params):
        log.debug(f"### list {params}")
        return self.store.find(params)
    
    def fieldnames(self):
        return self.store.fieldnames


# gspread
import gspread
class SheetsBackingStore:
    def __init__(self, name: str):
        gc = gspread.service_account()
        sh = gc.open(name)
        self.sheet = sh.sheet1
        self.fieldnames = self.sheet.row_values(1)
        self.field_map = {}
        # index of fields, and their 1-based sheet index
        for i, field in enumerate(self.fieldnames):
            self.field_map[field] = i + 1

    def count(self):
        # just get the number of values in id col
        col = self.field_map['id']
        return len(self.sheet.col_values(col))

        
    # get all the values as dict[]
    def values(self):
        return self.sheet.get_all_records()

    def find_id(self, id):
        col = self.field_map['id']
        log.debug(f"looking for {id} in col={col}")
        cell = self.sheet.find(str(id), in_column=col) # rampant str() - find() failed for int(id)
        if cell:
            log.debug(f"found row: {cell.row}")
            return cell
        else:
            log.debug(f"Couldn't: id={id} in col={col}")

    def row(self, id):
        cell = self.find_id(id)
        if cell:
            values = self.sheet.row_values(cell.row)
            # map columns items to names
            row = {}            
            #log.debug(f'{values}')

            for col, value in enumerate(values):
                name = self.fieldnames[col]
                #log.debug(f'{name}')
                row[name] = value

            return row

    def get(self, id, field):
        found = self.row(id)
        if found:
            return found[field]

    # return any fields that match all suppied params (they are "and"ed)
    def find(self, fields):
        result = []

        # more dumb search
        for row in self.values():
            for key, value in fields.items():
                if row[key] != value:
                    break;
            else: # all values match!
                result.append(row)

        return result

    def update(self, id, params):
        cell = self.find_id(id)

        # update the values
        for name, value in params.items():
            col = self.field_map[name]
            #log.debug(f"Updating a value: {id}, {name}/{col} -> {value}")

            self.sheet.update_cell(cell.row, col, value)


    def add(self, params):
        log.debug(f"add:params={params}")

        # create row value list
        row = [None] * (len(self.field_map.items()) + 1)

        for field, value in params.items():
            col = self.field_map.get(field)
            if col:
                row[col] = value
                #log.debug(f"add: {col}/{field} = {params}")
            else:
                log.warn(f'Unknown column name: {field}')

        # the list is too long currently, due to the 1-based index for sheets
        row = row[1:]

        # create a new row
        log.debug(f"Appending row, id={row[0]}: {row}")
        self.sheet.append_row(row)

        return params['id']

    
class FileBackingStore:
    def __init__(self, filename: str):
        self.filename = filename
        self.fieldnames = self._get_fieldnames()

    # get the column titles, as per csv.DictReader
    def _get_fieldnames(self):
        with open(self.filename) as csvfile:
            return csv.DictReader(csvfile).fieldnames
        
    # the number of records stored
    def count(self):
        with open(self.filename) as f:
            return sum(1 for line in f)

    # get all the values as dict[]
    def values(self):
        with open(self.filename) as csvfile:
            reader = csv.DictReader(csvfile)
            df = []
            for row in reader:
                df.append(row)

            # TODO return the iterator from the reader? or a seqproxy?
            return df

    def row(self, id):
        # dumb search
        for row in self.values():
            if row['id'] == id:
                return row

    def get(self, id, field):
        found = self.row(id)
        if found:
            return found[field]

    # return any fields that match all suppied params (they are "and"ed)
    def find(self, fields):
        result = []

        # more dumb search
        for row in self.values():
            for key, value in fields.items():
                if row[key] != value:
                    break;
            else: # all values match!
                result.append(row)

        return result

    def add(self, params):
        with open(self.filename, 'a') as csvfile:
            writer = csv.DictWriter(csvfile, self.fieldnames)
            writer.writerow(params)

    def update(self, id, params):
        # read the file
        rows = self.values()

        # update the values
        for row in rows:
            if row['id'] == id:
                row.update(params)
                break;

        # write the file
        self.write(rows)

        log.debug(f"Updated a value: id={id}, {params}")

    def write(self, rows):
        with open(self.filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(rows)