"""
Report output formatting.
"""
import abc
from .core import Schema

I_P = Schema.Column.PARENT_IDX
I_T = Schema.Column.TYPE_IDX
I_K = Schema.Column.KEY_IDX
I_D = Schema.Column.DEPTH_IDX

class SchemaOutput(object):
    """Abstract base class for formatting and writing a schema to the output.
    """
    __meta__ = abc.ABCMeta

    def __init__(self, stream, database, collection):
        self._stream = stream
        self.names = {
            'database': database,
            'collection': collection
        }
        self.depth = 1

    @property
    def output(self):
        return self._stream

    def write_schema(self, schema):
        self.begin()
        self.begin_itemize()
        table = schema.table
        for i in range(len(table)):
            if table[i][I_P] < 0:
                self._item(table, i)
        self.end()

    def write(self, txt):
        self._stream.write(txt)

    def writeln(self, txt):
        self._stream.write(txt)
        self._stream.write('\n')

    def _item(self, table, i):
        row = table[i]
        if row[I_T] not in ('dict', 'array'):
            self.begin_item()
            self._value(row[I_K], row[I_T])
            self.end_item()
        else:
            key = row[I_K]
            if key:
                is_array = row[I_T] == 'array'
                self.begin_item(key=key, array=is_array)
                self.depth += 1
            self.begin_itemize()
            for j in range(len(table)):
                if table[j][I_P] == i:
                    self._item(table, j)
            self.end_itemize()
            if key:
                self.depth -= 1
                self.end_item(key=key, array=is_array)

    def _value(self, key: str, type_: str):
        if key:
            self.pair(key, type_)
        else:
            self.one(type_)

    @abc.abstractmethod
    def begin(self):
        pass

    @abc.abstractmethod
    def end(self):
        pass

    @abc.abstractmethod
    def begin_itemize(self):
        pass

    @abc.abstractmethod
    def end_itemize(self):
        pass

    @abc.abstractmethod
    def begin_item(self, key=None, array=None):
        pass

    @abc.abstractmethod
    def end_item(self, key=None, array=None):
        pass

    @abc.abstractmethod
    def one(self, value):
        pass

    @abc.abstractmethod
    def pair(self, key, value):
        pass


# TODO: Rewrite this class using Reify
class SimpleText(SchemaOutput):
    def __init__(self, *args):
        super(SimpleText, self).__init__(*args)
        self._blank_line = True

    @property
    def indent(self):
        return '  ' * (self.depth - 1)

    def writeln(self, s):
        if s == '':
            if not self._blank_line:
                super(SimpleText, self).writeln('')
            self._blank_line = True
        else:
            super(SimpleText, self).writeln(s)

    def write(self, s):
        self._blank_line = False
        super(SimpleText, self).write(s)

    def begin(self):
        self.writeln('')

    def end(self):
        self.writeln('')

    def begin_itemize(self):
        self.writeln('')

    def end_itemize(self):
        pass

    def begin_item(self, key=None, array=None):
        if array is None:
            self.write('{}- '.format(self.indent))
        else:
            symbol = ('{}', '[]')[array]
            self.one('{}{}'.format(key, symbol))

    def end_item(self):
        self.writeln('')

    def one(self, value):
        self.write(str(value))

    def pair(self, key, value):
        self.write('{}: {}'.format(key, value))


class Reify(object):
    __meta__ = abc.ABCMeta

    def __init__(self, output_stream=None):
        self._i = 0
        self._depth = 0
        self._c = []
        self._ostrm = output_stream

    def row(self, key, type_, depth):
        container = None
        while depth < self._depth:
            self.pop()
        if type_ in ('array', 'dict'):
            self.push(key, type_)
            container = type_
        else:
            self.item(key, type_)
        return container

    def done(self):
        while self._c:
            self.pop()

    def pop(self):
        type_ = self._c.pop()
        self._depth -= 1
        self.end_container(type_)

    def push(self, key, type_):
        self.begin_container(key, type_)
        self._c.append(type_)
        self._depth += 1

    def write(self, s):
        self._ostrm.write(s)

    @abc.abstractmethod
    def item(self, key, type_):
        pass

    @abc.abstractmethod
    def begin_container(self, key, type_):
        pass

    @abc.abstractmethod
    def end_container(self, type_):
        pass


class JsonSchemaify(Reify):
    """Make a JSON Schema representation.
    """
    def __init__(self, **kw):
        super(JsonSchemaify, self).__init__(**kw)
        self._in_list = False
        self._offset = 0
        self._solo = False

    def iwrite(self, s):
        indent = (self._depth + self._offset) * '  '
        self.write(indent + s)

    def section_start(self):
        if self._in_list:
            self.write('\n')
        self._in_list = False

    def section_end(self):
        if self._in_list:
            self.write('\n')
        self._in_list = False

    def begin_container(self, key, type_):
        self.section_start()
        if key:
            self.iwrite('"{}": {{\n'.format(key))
        else:
            self.iwrite('{\n')
        self._offset += 1
        if type_ == 'dict':
            self.iwrite('"type": "object",\n')
            self.iwrite('"properties": {\n')
        else:
            self.iwrite('"type": "array",\n')
            self.iwrite('"items": ')
        self._offset += 1
        self._in_list = False

    def end_container(self, type_):
        self.section_end()
        if type_ == 'dict':
            self._offset -= 1
            self.iwrite('}\n')
            self._offset -= 1
            self.iwrite('}\n')
        else:
            self._offset -= 1
            if self._solo:
                self.iwrite('}\n')
            else:
                self.iwrite(']\n')
            self._offset -= 1
            self.iwrite('}\n')

    def item(self, key, type_):
        if self._in_list:
            self.write(',\n')
        if key:
            self.iwrite('"{}": {{ "type": "{}"}}'.format(key, type_))
        else:
            if self._solo:
                self.iwrite('"type": "{}"'.format(type_))
            else:
                self.iwrite('{{"type": "{}"}}'.format(type_))
        self._in_list = True


class JsonSchemaReport(object):
    def __init__(self, ofile, *ignore):
        self._o = ofile
        self.js = None

    def write_schema(self, schema):
        self.js = JsonSchemaify(output_stream=self._o)
        self.js.row('', 'dict', 0)  # wrap in outer object
        # process top-level
        for i in range(len(schema.table)):
            if schema.table[i][I_P] < 0:
                self.process(schema.table, i)
        self.js.done()

    def process(self, table, i):
        row = table[i]
        k, t, d = row[I_K], row[I_T], row[I_D] + 1
        container = self.js.row(k, t, d)
        if container:
            children = [j for j in range(len(table))
                        if table[j][I_P] == i]
            if container == 'array':
                # JSON Schema has 2 ways to represent array items,
                # either as "all of type X" or "type X, type Y, type Z".
                # One is a single schema, the other a list of schemas.
                self.js._solo = len(children) == 1
                if self.js._solo:
                    self.js.write('{\n')
                else:
                    self.js.write('[\n')
            for child in children:
                self.process(table, child)