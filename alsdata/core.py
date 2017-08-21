"""
Core functionality for alsdata
"""
import six


class CompareResult(object):
    """Encode a comparison result with why and the values involved.
    """
    LENGTH = 1  # Length mismatch
    TYPE = 2    # Type mismatch
    DEPTH = 3   # Depth mismatch
    KEY = 4     # Key mismatch
    EQUAL = 0   # Same
    CONST = {'type': TYPE, 'depth': DEPTH, 'key': KEY}

    def __init__(self, reason=EQUAL, v1=None, v2=None):
        self.reason, self.v1, self.v2 = reason, v1, v2

    def __bool__(self):
        return self.reason == self.EQUAL


class Schema(object):
    """Schema inferred from an input document.
    """
    def __init__(self):
        self._table = []
        self._done = False
        self._iter_table, self._cmp_table = None, None

    @property
    def table(self):
        tbl = self._cmp_table if self._done else self._table
        if self._iter_table is None:
            self._iter_table = [{'depth': t[0], 'key': t[1], 'type': t[2],
                                 'parent': t[3]} for t in tbl]
        return self._iter_table

    @property
    def cmp_table(self):
        return self._cmp_table

    def add(self, depth: int, key: str, type_: str, parent: int) -> int:
        if self._done:
            raise RuntimeError('Cannot add to schema after done() is called')
        skip, row = False, (depth, key, type_, parent)
        # remove duplicate scalar array entries (e.g. 'str' only once)
        # note: this is a simple case for eliminating duplicate array entries
        # (including array and dict entries).
        skip = ((parent >= 0 and self._table[parent][2] == 'array') and
                (type_ not in ('dict', 'array')) and (row in self._table))
        if not skip:
            self._table.append(row)
        return len(self._table) - 1

    def check_arr_dup(self, arr_idx, item_idx):
        print('@@ check arr dup of item {:d} in array {:d}'.format(item_idx, arr_idx))
        # make sub-schema for item, and all other children of arr
        # see if item matches any of the other children
        # if so, remove all its rows

    def done(self):
        self._cmp_table = tuple(sorted(self._table))
        self._done = True

    def compare(self, other) -> CompareResult:
        if not self._done:
            raise RuntimeError('Must call done() first')
        t1, t2 = self.cmp_table, other.cmp_table
        if len(t1) != len(t2):
            return CompareResult(CompareResult.LENGTH,
                                 len(t1), len(t2))
        for item1, item2 in zip(t1, t2):
            if item1 == item2:
                continue
            for idx, attr in enumerate(('depth', 'key', 'type', 'parent')):
                a1, a2 = item1[idx], item2[idx]
                if a1 != a2:
                    return CompareResult(CompareResult.CONST[attr], a1, a2)
        return CompareResult()

    def __eq__(self, other):
        if not self._done:
            raise RuntimeError('Must call done() first')
        return bool(self.compare(other))

    def __hash__(self):
        if not self._done:
            raise RuntimeError('Must call done() first')
        return hash(self.cmp_table)


class SchemaFactory(object):
    """Generate :class:`Schema` objects from input JSON data.
    """
    def __init__(self):
        self.schema = None

    def process(self, input_data: dict) -> Schema:
        schema = Schema()
        self._process_dict(schema, -1, 0, input_data)
        schema.done()
        return schema

    def _process_dict(self, schema: Schema, n: int, depth: int, obj: dict):
        """Process contents of `obj`, at index `n` and depth `depth`.
        """
        for key, val in six.iteritems(obj):
            if key == '_id':
                continue
            t = self._type_name(val)
            i = schema.add(depth, key, t, n)
            # print('@@ {:d}->{:d}: key={} type={}'.format(n, i, key, t))
            if t == 'array':
                self._process_array(schema, i, depth + 1, val)
            elif t == 'dict':
                self._process_dict(schema, i, depth + 1, val)

    def _process_array(self, schema: Schema, n: int, depth: int, arr: list):
        for val in arr:
            t = self._type_name(val)
            i = schema.add(depth, '', t, n)
            # print('@@ {:d}->{:d}: key=NA type={}'.format(n, i, t))
            if t == 'array':
                self._process_array(schema, i, depth + 1, val)
            elif t == 'dict':
                self._process_dict(schema, i, depth + 1, val)
            schema.check_arr_dup(n, i)

    @staticmethod
    def _type_name(val):
        if isinstance(val, int):
            return 'int'
        if isinstance(val, float):
            return 'float'
        if isinstance(val, str):
            return 'str'
        if isinstance(val, dict):
            return 'dict'
        if isinstance(val, list):
            return 'array'
        raise ValueError('Cannot determine type for "{}" ({})'.format(
            val, type(val)))


class SchemaSet(object):
    """A set of distinct schemas.
    """
    def __init__(self):
        self.schemas = {}

    def add(self, s, id_):
        try:
            self.schemas[s].append(id_)
        except KeyError:
            self.schemas[s] = [id_]

    def __iter__(self):
        return iter(self.schemas.keys())

    def __getitem__(self, key):
        return self.schemas[key]

    def __len__(self):
        return len(self.schemas)