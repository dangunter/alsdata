"""
Report output formatting.
"""
import abc
from .core import Schema

I_P = Schema.Column.PARENT_IDX
I_T = Schema.Column.TYPE_IDX
I_K = Schema.Column.KEY_IDX
I_D = Schema.Column.DEPTH_IDX


class Reify(object):
    """Make a schema concrete by writing it to output.

    This is an abstract superclass.
    """
    __meta__ = abc.ABCMeta

    def __init__(self, output_stream=None):
        self._i = 0
        self._depth = 0
        self._c = []
        self._ostrm = output_stream
        self._offset = 0

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

    def iwrite(self, s):
        indent = (self._depth + self._offset) * '  '
        self._ostrm.write(indent + s)

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
        self._solo = False

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
            self.iwrite('"items": ')  # note, choose [ ] or { } later
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


class Textify(Reify):
    def item(self, key, type_):
        if key:
            self.iwrite('- {}: {}\n'.format(key, type_))
        else:
            self.iwrite('- {}\n'.format(type_))

    def begin_container(self, key, type_):
        symbol = ('{}', '[]')[type_ == 'array']
        if key:
            self.iwrite('- {}{}\n'.format(key, symbol))
        else:
            self.iwrite('- {}\n'.format(symbol))
        self._offset += 1

    @abc.abstractmethod
    def end_container(self, type_):
        self._offset -= 1


class Report(object):
    __meta__ = abc.ABCMeta

    def __init__(self, ofile, *ignore):
        self._o = ofile
        self.rf = None

    def set_output_file(self, o):
        if self._o:
            self._o.flush()
        self._o = o

    @abc.abstractmethod
    def write_schema(self, schema):
        pass

    def process(self, table, i):
        """Traverse the table depth-first from i-th element.
        """
        row = table[i]
        k, t, d = row[I_K], row[I_T], row[I_D] + 1
        container = self.rf.row(k, t, d)
        if container:
            children = [j for j in range(len(table))
                        if table[j][I_P] == i]
            self.process_children(table, i, container, children)

    @abc.abstractmethod
    def process_children(self, table, i, container, children):
        pass


class JsonSchemaReport(Report):
    def write_schema(self, schema):
        self.rf = JsonSchemaify(output_stream=self._o)
        # wrap in outer object
        self.rf.row('', 'dict', 0)
        # process top-level elements
        for i in range(len(schema.table)):
            if schema.table[i][I_P] < 0:
                self.process(schema.table, i)
        # finish up
        self.rf.done()

    def process_children(self, table, i, container, children):
        if container == 'array':
            # JSON Schema has 2 ways to represent array items,
            # either as "all of type X" or "type X, type Y, type Z".
            # One is a single schema, the other a list of schemas.
            # The attribute '_solo' records this decision.
            self.rf._solo = len(children) == 1
            if self.rf._solo:
                self.rf.write('{\n')
            else:
                self.rf.write('[\n')
        for child in children:
            self.process(table, child)


class TextReport(Report):
    def write_schema(self, schema):
        self.rf = Textify(output_stream=self._o)
        # process top-level elements
        for i in range(len(schema.table)):
            if schema.table[i][I_P] < 0:
                self.process(schema.table, i)
        # finish up
        self.rf.done()

    def process_children(self, table, i, container, children):
        for child in children:
            self.process(table, child)