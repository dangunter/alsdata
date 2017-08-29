"""
Core functionality for alsdata
"""
import logging
import six

_LOG_ROOT = 'alsdata'

# one-time log setup
h = logging.StreamHandler()
f = logging.Formatter(fmt='%(asctime)s %(name)s [%(levelname)s] %(message)s')
h.setFormatter(f)
logging.getLogger(_LOG_ROOT).addHandler(h)


def get_logger(name=''):
    """Create and return a logger instance.
    Leaving the name blank will get the root logger.
    """
    if name:
        g = logging.getLogger(_LOG_ROOT + '.' + name)
        g.propagate = True
    else:
        g = logging.getLogger(_LOG_ROOT)
    return g


class CompareResult(object):
    """Encode a comparison result with why and the values involved.
    """
    LENGTH = 1    # Length mismatch
    CONTENTS = 2  # Contents mismatch
    EQUAL = 0     # Same

    def __init__(self, reason=EQUAL, v1=None, v2=None):
        self.reason, self.v1, self.v2 = reason, str(v1), str(v2)

    def __bool__(self):
        return self.reason == self.EQUAL


class Schema(object):
    """Schema inferred from an input document.
    """
    class Column(object):
        DEPTH_IDX, DEPTH = 0, 'depth'
        KEY_IDX, KEY = 1, 'key'
        TYPE_IDX, TYPE = 2, 'type'
        PARENT_IDX, PARENT = 3, 'parent'
        ID_IDX, ID = 4, 'id'  # Must be last, otherwise sort() does nothing

    def __init__(self, initial_rows=None):
        if initial_rows:
            self._table = initial_rows
        else:
            self._table = []
        self._done = False
        self._cur_arr_idx = None
        self._cur_arr_set = SchemaSet()

    @property
    def table(self):
        if not self._done:
            raise AttributeError('Must call done() before retrieving result')
        return self._table

    def add(self, depth: int, key: str, type_: str, parent: int) -> int:
        if self._done:
            raise RuntimeError('Cannot add to schema after done() is called')
        idx = len(self._table)
        skip, row = False, (depth, key, type_, parent)
        # remove duplicate scalar array entries (e.g. 'str' only once)
        skip = ((parent >= 0 and
                 self._table[parent][self.Column.TYPE_IDX] == 'array') and
                (type_ not in ('dict', 'array')) and (row in self._table))
        if not skip:
            self._table.append(row)
        return idx

    def check_arr_dup(self, arr_idx, item_idx):
        item = self._table[item_idx]

        # If scalar, ignore; duplicate scalars were removed in `add()`.
        if item[self.Column.TYPE_IDX] not in ('dict', 'array'):
            return

        #print('@@ check dup table:\n{}'.format(self._dump_table()))

        # Get all child items, make into a Schema instance.
        # Shift all references by index of first item.
        it1 = self._table[item_idx]
        items = [(it1[0], it1[1], it1[2], -1)]
        for it in self._table[item_idx + 1:]:
            items.append((it[0], it[1], it[2], it[3] - item_idx))

        ssc = Schema(initial_rows=items)
        ssc.done()
        # print('@@ sub-schema from rows:\n{}'.format(ssc._dump_table()))

        # Have we already added items to this array?
        if self._cur_arr_idx == arr_idx:
            # Check if Schema is unique, by adding it to the SchemaSet.
            is_new = self._cur_arr_set.add(ssc, 0)
            # If Schema is a duplicate, remove associated items.
            if not is_new:
                # print('@@ rows {:d}-{:d} are duplicates'
                #     .format(item_idx, len(self._table) - 1))
                del self._table[item_idx:]
                # print('@@ new table:\n{}'.format(self._dump_table()))
            else:
                pass
                # print('@@ rows {:d}-{:d} are not duplicates'
                #       .format(item_idx, len(self._table) - 1))
                # print('@@ new table:\n{}'.format(self._dump_table()))
            # If we are in a new array, add this as the first item.
        else:
            self._cur_arr_idx = arr_idx
            self._cur_arr_set = SchemaSet()
            self._cur_arr_set.add(ssc, 0)

    def _dump_table(self):
        lines = ['-' * 45]
        i = 0
        for row in self._table:
            line = '{:2d} | {:3d} {:20s} {:12s} {:d}'.format(i, *row)
            lines.append(line)
            i += 1
        lines.append('-' * 45)
        return '\n'.join(lines)

    def done(self):
        n = len(self._table)
        last_idx = len(self._table[0])  # row length
        # Add an index column
        tbl = [self._table[i] + (i,) for i in range(n)]
        # Sort the table
        tbl.sort()

        # Remap parents to correct row, as they are shuffled after sorting
        idx_map = [0] * n
        # Build map from current index back to original one
        for i in range(n):
            idx_map[tbl[i][last_idx]] = i
        # Use map to fix parent references.
        # Copy result back into original table (remove index column).
        for i in range(n):
            row = tbl[i]
            parent = row[self.Column.PARENT_IDX]
            if parent >= 0:
                r = (row[0], row[1], row[2], idx_map[parent])
            else:
                r = tuple(row[:-1])
            self._table[i] = r
        self._table = tuple(self._table)

        # Now we are done
        self._done = True

    def compare(self, other) -> CompareResult:
        if not self._done:
            raise RuntimeError('Must call done() first')
        t1, t2 = self._table, other.table
        if len(t1) != len(t2):
            return CompareResult(CompareResult.LENGTH,
                                 len(t1), len(t2))
        for item1, item2 in zip(t1, t2):
            if item1 == item2:
                continue
            return CompareResult(CompareResult.CONTENTS, item1, item2)
        return CompareResult()

    def __eq__(self, other):
        if not self._done:
            raise RuntimeError('Must call done() first')
        return bool(self.compare(other))

    def __hash__(self):
        if not self._done:
            raise RuntimeError('Must call done() first')
        return hash(self._table)


class SchemaFactory(object):
    """Generate :class:`Schema` objects from input JSON data.

    Note: only one call to process() should be running at any given
    time for a single instance.
    """
    def __init__(self):
        self._schema = None

    def process(self, input_data: dict) -> Schema:
        self._schema = Schema()
        self._process_dict(-1, 0, input_data)
        self._schema.done()
        return self._schema

    def _process_dict(self, n: int, depth: int, obj: dict):
        """Process contents of `obj`, at index `n` and depth `depth`.
        """
        for key, val in six.iteritems(obj):
            if key == '_id':
                continue
            t = self._type_name(val)
            i = self._schema.add(depth, key, t, n)
            # print('@@ {:d}->{:d}: key={} type={}'.format(n, i, key, t))
            if t == 'array':
                self._process_array(i, depth + 1, val)
            elif t == 'dict':
                self._process_dict(i, depth + 1, val)

    def _process_array(self, n: int, depth: int, arr: list):
        for val in arr:
            t = self._type_name(val)
            i = self._schema.add(depth, '', t, n)
            # print('@@ {:d}->{:d}: key=NA type={}'.format(n, i, t))
            if t in ('array', 'dict'):
                if t == 'array':
                    self._process_array(i, depth + 1, val)
                else:
                    self._process_dict(i, depth + 1, val)
                self._schema.check_arr_dup(n, i)

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

    def add(self, s, id_) -> bool:
        is_new = False
        try:
            self.schemas[s].append(id_)
        except KeyError:
            is_new = True
            self.schemas[s] = [id_]
        return is_new

    def items(self):
        return six.iteritems(self.schemas)

    def __iter__(self):
        return iter(self.schemas.keys())

    def __getitem__(self, key):
        return self.schemas[key]

    def __len__(self):
        return len(self.schemas)
