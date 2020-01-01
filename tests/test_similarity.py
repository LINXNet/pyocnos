from lxml import etree
from pytest import approx

from pyocnos.similarity import *


def test_similarity_simple():
    assert similarity_element(etree.XML('<foo>1</foo>'),
                      etree.XML('<bar>1</bar>')) == 0

    assert similarity_element(etree.XML('<foo>1</foo>'),
                      etree.XML('<foo>2</foo>')) == A_INFINITESIMAL_SIMILARITY

    assert similarity_element(etree.XML('<foo>1</foo>'),
                      etree.XML('<foo>1</foo>')) == 1
    
    assert similarity_element(etree.XML('<foo>1</foo>'),
                      etree.XML('<foo><tar></tar></foo>')) == A_INFINITESIMAL_SIMILARITY

    elem_lists = ([
        etree.XML('<foo>100</foo>'),
        etree.XML('<foo>200</foo>'),
    ], [
        etree.XML('<foo>0</foo>'),
        etree.XML('<foo>100</foo>'),
        etree.XML('<foo>200</foo>'),
    ]),
    ([
        etree.XML('<foo>100</foo>'),
        etree.XML('<foo>200</foo>'),
        etree.XML('<foo><tar>unknown</tar></foo>'),
    ], [
        etree.XML('<foo>200</foo>'),
        etree.XML('<bar>xyz</bar>'),
        etree.XML('<foo>100</foo>'),
    ])

    for elem_a, elem_b in elem_lists:
        # similarity_element = (1 + 1)/3 = 0.6666...
        assert similarity_array(elem_a, elem_b) == approx(0.67, 0.01)
        for index_a, index_b in similarity_indexes(elem_a, elem_b):
            assert elem_a[index_a].text == elem_b[index_b].text


def test_similarity_recursion():
    elem_a = etree.XML("""
    <data>
      <foo>
        <tar>100</tar>
      </foo>
      <foo>
        <tar>200</tar>
      </foo>
    </data>
    """)
    elem_b = etree.XML("""
    <data>
      <foo>
        <tar>0</tar>
      </foo>,
      <foo>
        <tar>100</tar>
      </foo>
      <foo>
        <tar>200</tar>
      </foo>
    </data>
    """)

    assert similarity_array(elem_a, elem_b) == approx(0.67, 0.01)
    for index_a, index_b in similarity_indexes(elem_a, elem_b):
        assert elem_a[index_a][0].text == elem_b[index_b][0].text

    elem_a = etree.XML("""
    <data>
      <foo>
        <tar>100</tar>
        <kil>abc</kil>
      </foo>
      <foo>
        <tar>200</tar>
      </foo>
      <foo>
        <tar>300</tar>
      </foo>
    </data>
    """)
    elem_b = etree.XML("""
    <data>
      <foo>
        <tar>0</tar>
      </foo>,
      <foo>
        <tar>100</tar>
        <kil>xyz</kil>
      </foo>
      <foo>
        <tar>100</tar>
        <kil>abc</kil>
        <toa>xyz</toa>
        <tea>xyz</tea>
        <zab>xyz</zab>
      </foo>
      <foo>
        <tar>300</tar>
      </foo>
    </data>
    """)

    print([[similarity_element(a, b) for b in elem_b] for a in elem_a])
    assert list(similarity_indexes(elem_a, elem_b)) == [
              (0, 1),
              (1, 0),
              (2, 3)
    ]
