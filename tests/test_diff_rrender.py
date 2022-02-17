"""
This test module covers tests cases for function pyocnos.diff.rrender()
"""
# pylint: disable=invalid-name

import pytest
import pyocnos
from pyocnos.diff import normalize_tree, rrender


def test_rrender_invalid_input():
    """
    A diff tree without children is an invlid case. It is to align with the fact this module
    is to compare two xml tree rather than two simple element.
    """
    tree_diff = normalize_tree("""
        <data change='removed'>100</data>
    """)

    with pytest.raises(ValueError):
        rrender(tree_diff)


def test_rrender_no_changes_at_all():
    """
    Scenario: Given a diff tree with no diff marked, the output is the collapsed version of the tree.
    """
    tree_diff = normalize_tree("""
        <data>
          <foo>
            <bar>100</bar>
          </foo>
        </data>
    """)

    assert rrender(tree_diff) == []

    tree_diff = normalize_tree("""
        <data>
          <foo>
            <bar>100</bar>
          </foo>
          <loo>200</loo>
        </data>
    """)

    assert rrender(tree_diff) == []

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

    assert rrender(tree_diff) == []


def test_rrender_multiple_changes():
    """
    Scenario: in a diff tree, an added element has + decorated in the front whilst
    an removed element has - decorated. And unchanged elements are collapsed.
    """
    pyocnos.diff.ELEMENTS_WITH_FIXED_KEYS = {'data': [('foo',)]}
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
        '  [loo]',
        '+   <lit>300</lit>',
        '    [rah]',
        '-     <ght>700</ght>',
    ]

    assert rrender(tree_diff) == expected
