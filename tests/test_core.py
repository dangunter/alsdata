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
                "France", "Spain", "Frain", "Spance"
            ]},
            {"altitudes": [
                20, 10, "high", "lowly"
            ]}
        ]}
    ]}

    s = core.SchemaFactory().process(d)
    tbl = s.table

    # expected:
    #   (#) key        type    parent
    #    0  addresses  array   -1
    #    1  --         dict    0
    #    2  --         dict    0
    #    3  --         dict    0
    #    4  city       str     <1,2, or 3>

    assert tbl[0]['key'] == 'addresses'
    assert tbl[0]['type'] == 'array'
    for i in range(1, 4):
        assert tbl[i]['key'] == ''
        assert tbl[i]['type'] == 'dict'
    assert tbl[4]['key'] == 'city'
    assert tbl[4]['type'] == 'str'
    assert tbl[4]['parent'] in (1, 2, 3)

def _format_schema(s, output=False):
    strm = StringIO()
    txt = report.SimpleText(strm, 'test', 'test')
    txt.write_schema(s)
    s = strm.getvalue()
    if output:
        print(s)
    return s