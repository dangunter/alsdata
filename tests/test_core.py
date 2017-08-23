"""
Unit tests for .core
"""
from six import StringIO
from alsdata import core
from alsdata import report


def setup():
    pass


def teardown():
    pass


def test_same_schema():
    sf = core.SchemaFactory()
    d1 = {'_id': '001',
          'fruit': {'bananas': 1, 'apples': 3},
          'veggies': [
             {'pulses': {'lentils': 4.0, 'chickpeas': 1.2}},
             {'greens': {'kale': 3, 'chard': list(range(10))}},
             'organic',
             'local',
             8.2
         ],
}
    d2 = d1.copy()
    d2['_id'] = '002'
    #
    schemas = core.SchemaSet()
    s = None
    for data in d1, d2:
        s = sf.process(data)
        schemas.add(s, data['_id'])
    #
    assert len(schemas) == 1
    assert len(schemas[s]) == 2


def test_array_dedup():
    d = {
        "addresses": [
        {"street": "123 fake street", "city": "berkeley", "type": "home"},
        {"street": "123 fake street", "city": "martinez", "type": "work"},
        {"city": "dome city", "planet": "mars", "type": "sci-fi"},
        {"city": "mereen", "planet": "game of thrones", "type": "fantasy"},
        {"locations": [
            {"countries": [
                "France", "Spain", "Spain", "France"
            ]},
            {"altitudes": [
                "uno", "dos", "tres", "quatro", "cinco", "cinco", "seis",
                1, 2, 3, 4, 5, 5, 6
            ]}
        ]}
    ]}

    s = core.SchemaFactory().process(d)
    tbl = s.table

    # Debugging
    # print('\nIDX Dp Key                  Type        Parent')
    # for i, row in enumerate(tbl):
    #     print('{:3d} {:2d} {:20s} {:12s} {:2d}'
    #           .format(i, *row))

    # expected:
    #   (#) key        type    parent
    #    0  addresses  array   -1
    #    1  --         dict    0
    #    2  --         dict    0
    #    3  --         dict    0
    #    4  city       str     <1 - 3>
    #    5  city       str     <1 - 3>
    #    6  locations  array   <1 - 3>
    _key, _type = core.Schema.Column.KEY_IDX, core.Schema.Column.TYPE_IDX
    _parent = core.Schema.Column.PARENT_IDX
    assert tbl[0][_key] == 'addresses'
    assert tbl[0][_type] == 'array'
    for i in range(1, 4):
        assert tbl[i][_key] == ''
        assert tbl[i][_type] == 'dict'
    for i in 4, 5:
        assert tbl[i][_key] == 'city'
        assert tbl[i][_type] == 'str'
        assert tbl[i][_parent] in (1, 2, 3)
    assert tbl[6][_key] == 'locations'
    assert tbl[6][_type] == 'array'
    assert tbl[6][_parent] in (1, 2, 3, 4, 5)


def test_simple_array():
    d1 = {"numbers": [{"num": 1, "name": "one"}, {"num": 2, "name": "two"}]}
    d2 = {"numbers": [{"num": 3, "name": "three"}, {"num": 4, "name": "four"},
                      {"num": 5, "name": "five"}]}
    sf = core.SchemaFactory()
    s1 = sf.process(d1)
    s2 = sf.process(d2)
    cmp = s1.compare(s2)
    assert bool(cmp) is True


def _format_schema(s, output=False):
    strm = StringIO()
    txt = report.SimpleText(strm, 'test', 'test')
    txt.write_schema(s)
    s = strm.getvalue()
    if output:
        print(s)
    return s