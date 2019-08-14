"""
This test module covers tests cases for function pyocnos.diff.rrender()
"""
# pylint: disable=invalid-name

import pytest
from lxml import etree
from pyocnos.diff import normalize_tree, rrender, ADDED, REMOVED





def test_rrender_invalid_input():
    tree_diff = normalize_tree("""
        <data change='removed'>100</data>
    """)

    with pytest.raises(ValueError):
        rrender(tree_diff)


def test_rrender_no_changes_at_all():
    tree_diff = normalize_tree("""
        <data>
          <foo>
            <bar>100</bar>
          </foo>
        </data>
    """)

    assert rrender(tree_diff) == \
        [
            '[data]',
            '  <foo>...</foo>'
        ]

    tree_diff = normalize_tree("""
        <data>
          <foo>
            <bar>100</bar>
          </foo>
          <loo>200</loo>
        </data>
    """)

    assert rrender(tree_diff) == \
        [
            '[data]',
            '  <foo>...</foo>',
            '  <loo>200</loo>'
        ]

    tree_diff = normalize_tree("""
        <data>
          <foo>
            <bar>100</bar>
          </foo>
          <loo>200</loo>
          <rah>300</rah>
          <rid>400</rid>
        </data>
    """)

    print(rrender(tree_diff))

    assert rrender(tree_diff) == \
        [
            '[data]',
            '  <foo>...</foo>',
            '  ...',
            '  <rid>400</rid>'
        ]


def test_rrender_multiple_changes():
    tree_diff = normalize_tree("""
        <data>
            <foo>100</foo>
            <bar>200</bar>
            <loo>
              <lit change='added'>300</lit>
              <pat>400</pat>
              <cad>500</cad>
              <nil>600</nil>
              <rah>
                <ght change='removed'>700</ght>
                <xla>800</xla>
              </rah>
            </loo>
            <qba>900</qba>
        </data>
    """)
    expected = [
        '[data]',
        '  <foo>100</foo>',
        '  <bar>200</bar>',
        '  [loo]',
        '+   <lit>300</lit>',
        '    <pat>400</pat>',
        '    ...',
        '    <nil>600</nil>',
        '    [rah]',
        '-     <ght>700</ght>',
        '      <xla>800</xla>',
        '  <qba>900</qba>',
    ]

    assert rrender(tree_diff) == expected
