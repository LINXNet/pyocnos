"""
This suites describes the baviour of pyocnos.diff module. Thus it is named with "feature" though
all tests are built with pyocnos.diff.build_xml_diff() which is the only entry of the module.
"""
# pylint: disable=invalid-name

import os
import pytest
from pyocnos.diff import build_xml_diff


def test_diff_cannot_compare_simple_xml():
    """
    The module does not support diff for two simple elements which contains no children elements.
    """
    with pytest.raises(ValueError):
        build_xml_diff("<data>100</data>", "<data>200</data>")

    with pytest.raises(ValueError):
        build_xml_diff("<data>100</data>", "<data><foo>200</foo></data>")


def test_diff_mismatched_root_tag():
    """
    The module does not support diff for two tree with same root tag.
    """
    with pytest.raises(ValueError):
        build_xml_diff("<data><foo>100</foo></data>", "<config><foo>200</foo></config>")


def test_diff_identical_xml():
    """
    When the compared xml are identical, the module should return empty string, and tell stdout this fact.
    """
    # When two xml are exactly the same
    assert not build_xml_diff("<data><foo>100</foo></data>", "<data><foo>100</foo></data>")

    assert not build_xml_diff("""
            <data>
              <foo>100</foo>
              <bar>200</bar>
            </data>
        """, """
            <data>
              <foo>100</foo>
              <bar>200</bar>
            </data>
        """)

    # Same case as above with deeper childeren
    assert not build_xml_diff("""
          <data>
            <foo>
              <col>100</col>
              <loh>200</loh>
            </foo>
            <bar>300</bar>
          </data>
        """, """
          <data>
            <foo>
              <col>100</col>
              <loh>200</loh>
            </foo>
            <bar>300</bar>
          </data>
        """)


def test_diff_reordered_xml():
    """
    When the compared xml are identical, the module should return empty string, and tell stdout this fact.
    """
    # When two xml vary only about order

    assert build_xml_diff("""
            <data>
              <foo>100</foo>
              <bar>200</bar>
            </data>
        """, """
            <data>
              <bar>200</bar>
              <foo>100</foo>
            </data>
        """) == os.linesep.join([
            '[data]',
            '! <foo>100</foo>',
            '! <bar>200</bar>',
        ])


    assert build_xml_diff("""
          <data>
            <foo>
              <loh>200</loh>
              <col>100</col>
            </foo>
            <bar>300</bar>
          </data>
        """, """
            <data>
              <bar>300</bar>
              <foo>
                <col>100</col>
                <loh>200</loh>
              </foo>
            </data>
        """) == os.linesep.join([
            '[data]',
            '  [foo]',
            '!   <loh>200</loh>',
            '!   <col>100</col>',
            '! <bar>300</bar>',
        ])


def test_diff_duplicated_elements():
    """
    The module knows how to deal with duplicated elements.
    Extra duplications are marked in the diff as either removed or added.
    """
    xmlstring_left = """
        <data>
          <foo>100</foo>
          <foo>100</foo>
          <bar>
            <lar>
              <col>200</col>
            </lar>
          </bar>
        </data>
    """
    xmlstring_right = """
        <data>
          <foo>100</foo>
          <bar>
            <lar>
              <col>200</col>
              <col>200</col>
            </lar>
          </bar>
        </data>
    """

    # It is designed to treat the first duplicated element as the removed one.
    expected = os.linesep.join([
        '[data]',
        '  <foo>100</foo>',
        '- <foo>100</foo>',
        '  [bar]',
        '    [lar]',
        '      <col>200</col>',
        # and the last duplicated element as the added one.
        '+     <col>200</col>'
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected


def test_diff_elems_in_same_name():
    """
    The module knows how to deal with multiple elements with the same tag when diff occurs among them.
    Bear in mind the module does not look into any elements with such tag for further diffing due to the fact that
    there is no way to tell which two elements it can choose to compare.
    This scenorio remains no matter the involved elements have children or just a simple element.
    And any removed or added elements are not collapsed, for the reason to help user find out which is which.
    """
    xmlstring_left = """
        <data>
          <foo>100</foo>
          <foo>
            <loo>200</loo>
          </foo>
          <bar>
            <lar>
              <col>
                <roh>400</roh>
              </col>
              <col>
                <roh>500</roh>
              </col>
            </lar>
          </bar>
        </data>
    """
    xmlstring_right = """
        <data>
          <foo>100</foo>
          <foo>
            <loo>20</loo>
          </foo>
          <bar>
            <lar>
              <col>
                <roh>600</roh>
              </col>
            </lar>
          </bar>
        </data>
    """

    expected = os.linesep.join([
        '[data]',
        '  <foo>100</foo>',
        '  [foo]',
        '-   <loo>200</loo>',
        '+   <loo>20</loo>',
        '  [bar]',
        '    [lar]',
        '      [col]',
        '-       <roh>400</roh>',
        '+       <roh>600</roh>',
        '-     <col>',
        '-       <roh>500</roh>',
        '-     </col>'
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected


def test_diff_value_changes():
    """
    This is the most simple and common case, that a single value gets changed.
    The module will mark the diff as a deleted element and an added element at the same location in the
    left xml.
    """
    xmlstring_left = """
        <data>
          <foo>100</foo>
          <bar>
            <col>
              <dah>200</dah>
            </col>
          </bar>
        </data>
    """
    xmlstring_right = """
        <data>
          <foo>10</foo>
          <bar>
            <col>
              <dah>20</dah>
            </col>
          </bar>
        </data>
    """
    expected = os.linesep.join([
        '[data]',
        '- <foo>100</foo>',
        '+ <foo>10</foo>',
        '  [bar]',
        '    [col]',
        '-     <dah>200</dah>',
        '+     <dah>20</dah>',
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected


def test_diff_child_tree_changes():
    """
    When a whole branch of xml is involved in the diff, the module does not collapse it but show all children
    and leaf elements.
    """
    xmlstring_left = """
        <data>
          <foo>
            <bar>100</bar>
          </foo>
          <col>
            <dil>
              <eol>
                <fen>200</fen>
              </eol>
              <elk>500</elk>
            </dil>
          </col>
          <gen>
            <haa>300</haa>
          </gen>
        </data>
    """
    xmlstring_right = """
        <data>
          <kal>
            <lol>100</lol>
          </kal>
          <col>
            <dil>
              <elk>500</elk>
            </dil>
          </col>
          <gen>
            <haa>300</haa>
            <mia>
              <nil>400</nil>
            </mia>
          </gen>
          <gen>
            <haa>400</haa>
          </gen>
        </data>
    """
    expected = os.linesep.join([
        '[data]',
        '- <foo>',
        '-   <bar>100</bar>',
        '- </foo>',
        '  [col]',
        '    [dil]',
        '-     <eol>',
        '-       <fen>200</fen>',
        '-     </eol>',
        '!     <elk>500</elk>',
        '  [gen]',
        '    <haa>300</haa>',
        '+   <mia>',
        '+     <nil>400</nil>',
        '+   </mia>',
        # Any added element is put at the tail of the diff.
        '+ <gen>',
        '+   <haa>400</haa>',
        '+ </gen>',
        '+ <kal>',
        '+   <lol>100</lol>',
        '+ </kal>'
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected


def test_diff_collapse_same_elements_among_diff():
    """
    Within a diff, any elements without changes are collapsed for simplicity.
    An element with no children is not collapsed.
    An element with children is collapsed as <foo>...</foo>
    A list of unchanged elements is collapsed if the amount is larger than 2 in this way:
    <foo>...</foo>
    ...
    <bar>...</bar>
    """
    xmlstring_left = """
        <data>
          <foo>100</foo>
          <bar>200</bar>
          <coh>300</coh>
          <deb>400</deb>
          <fan>
            <lol>
              <mia>
                <noh>900</noh>
                <olo>1000</olo>
                <pee>2000</pee>
                <qre>3000</qre>
              </mia>
            </lol>
          </fan>
          <eol>500</eol>
          <hat>600</hat>
          <inn>700</inn>
          <jad>800</jad>
        </data>
    """
    xmlstring_right = """
    <data>
      <foo>100</foo>
      <bar>20</bar>
      <coh>300</coh>
      <deb>400</deb>
      <fan>
        <lol>
          <mia>
            <noh>900</noh>
            <olo>1000</olo>
            <pee>2000</pee>
            <qre>30</qre>
          </mia>
        </lol>
      </fan>
      <eol>500</eol>
      <hat>600</hat>
      <inn>700</inn>
      <jad>800</jad>
    </data>
"""
    expected = os.linesep.join([
        '[data]',
        '  <foo>100</foo>',
        '- <bar>200</bar>',
        '+ <bar>20</bar>',
        '  <coh>300</coh>',
        '  <deb>400</deb>',
        '  [fan]',
        '    [lol]',
        '      [mia]',
        '        <noh>900</noh>',
        '        ...',
        '        <pee>2000</pee>',
        '-       <qre>3000</qre>',
        '+       <qre>30</qre>',
        '  <eol>500</eol>',
        '  ...',
        '  <jad>800</jad>'
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected
