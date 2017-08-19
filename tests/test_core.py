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


def test_schema_factory():
    sf = core.SchemaFactory()
    d1 = {'fruit': {'bananas': 1, 'apples': 3},
         'veggies': [
             {'pulses': {'lentils': 4.0, 'chickpeas': 1.2}},
             {'greens': {'kale': 3, 'chard': list(range(10))}},
             'organic',
             'local',
             8.2
         ],
}
    d2 = d1.copy()
    #
    s1, s2 = map(sf.process, [d1, d2])
    strm = StringIO()
    txt = report.SimpleText(strm, 'test', 'test')
    txt.write_schema(s1)
    s = strm.getvalue()
    print(s)