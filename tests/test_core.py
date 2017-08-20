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


def _format_schema(output=False):
    strm = StringIO()
    txt = report.SimpleText(strm, 'test', 'test')
    txt.write_schema(s1)
    s = strm.getvalue()
    if output:
        print(s)
    return s