"""
Report output formatting.
"""
import abc
from .core import Schema

I_P = Schema.Column.PARENT_IDX
I_T = Schema.Column.TYPE_IDX
I_K = Schema.Column.KEY_IDX


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
                symbol = ('{}', '[]')[row[I_T] == 'array']
                self.begin_item()
                self.one('{}{}'.format(key, symbol))
                self.depth += 1
            self.begin_itemize()
            for j in range(len(table)):
                if table[j][I_P] == i:
                    self._item(table, j)
            self.end_itemize()
            if key:
                self.depth -= 1
                self.end_item()

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
    def begin_item(self):
        pass

    @abc.abstractmethod
    def end_item(self):
        pass

    @abc.abstractmethod
    def one(self, value):
        pass

    @abc.abstractmethod
    def pair(self, key, value):
        pass


class SimpleText(SchemaOutput):
    def __init__(self, *args):
        super(SimpleText, self).__init__(*args)
        self._blank_line = False

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
        self.writeln('-----------------')

    def end(self):
        self.writeln('')

    def begin_itemize(self):
        self.writeln('')

    def end_itemize(self):
        pass

    def begin_item(self):
        self.write('{}- '.format(self.indent))

    def end_item(self):
        self.writeln('')

    def one(self, value):
        self.write(str(value))

    def pair(self, key, value):
        self.write('{}: {}'.format(key, value))
