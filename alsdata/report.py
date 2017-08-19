"""
Report output formatting.
"""
import abc


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
        for i, row in enumerate(table):
            if row['parent'] < 0:
                self._item(table, i)
        self.end_itemize()
        self.end()

    def write(self, txt):
        self._stream.write(txt)

    def writeln(self, txt):
        self._stream.write(txt)
        self._stream.write('\n')

    def _item(self, table, i):
        self.begin_item()
        row = table[i]
        if row['type'] not in ('dict', 'array'):
            self._value(row['key'], row['type'])
        else:
            self.one(row['key'])
            self.depth += 1
            self.begin_itemize()
            for j in range(i + 1, len(table)):
                if table[j]['parent'] == i:
                    self._item(table, j)
            self.end_itemize()
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
    def begin(self):
        #self.writeln('{database}/{collection}:'.format(**self.names))
        self.writeln('---')
        
    def end(self):
        pass

    def begin_itemize(self):
        self.writeln('')

    def end_itemize(self):
        pass

    def begin_item(self):
        self.write('{}- '.format('  ' * self.depth))

    def end_item(self):
        self.writeln('')

    def one(self, value):
        self.write(str(value))

    def pair(self, key, value):
        self.write('{}: {}'.format(key, value))
