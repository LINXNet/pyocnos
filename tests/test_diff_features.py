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
        '- <foo>100</foo>',
        '  [bar]',
        '    [lar]',
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
          <foo>
            <loo>20</loo>
          </foo>
          <foo>100</foo>
          <bar>
            <lar>
              <col>
                <roh>500</roh>
              </col>
              <col>
                <roh>600</roh>
              </col>
            </lar>
          </bar>
        </data>
    """

    expected = os.linesep.join([
      '[data]',
      '! <foo>100</foo>',
      '  [foo]',
      '-   <loo>200</loo>',
      '+   <loo>20</loo>',
      '  [bar]',
      '    [lar]',
      '      [col]',
      '-       <roh>400</roh>',
      '+       <roh>600</roh>',
      '!     <col>',
      '!       <roh>500</roh>',
      '!     </col>'
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected


def test_diff_elements_same_tag_simple():
    """
    When comparing two elements with child elements all in the same tag, it
    is required to picked up the most similar pair to generate the diff.
    """
    # When two xml vary only about order
    from lxml import etree
    xmlstring_left = """
      <data>
        <baj>
          <xin>
            <hos>10.10.10.10</hos>
          </xin>
          <xin>
            <hos>20.20.20.20</hos>
          </xin>
          <xin>
            <hos>30.30.30.30</hos>
          </xin>
        </baj>
      </data>
    """
    xmlstring_right = """
      <data>
        <baj>
          <xin>
            <hos>1.1.1.1</hos>
          </xin>
          <xin>
            <hos>10.10.10.10</hos>
            <foo>xyz</foo>
          </xin>
          <xin>
            <hos>20.20.20.20</hos>
          </xin>
          <xin>
            <hos>30.30.30.30</hos>
          </xin>
        </baj>
      </data>
    """

    expected = os.linesep.join([
      '[data]',
      '  [baj]',
      '    [xin]',
      '+     <foo>xyz</foo>',
      '!   <xin>',
      '!     <hos>20.20.20.20</hos>',
      '!   </xin>',
      '!   <xin>',
      '!     <hos>30.30.30.30</hos>',
      '!   </xin>',
      '+   <xin>',
      '+     <hos>1.1.1.1</hos>',
      '+   </xin>'
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected


def test_diff_elements_same_tag_advanced():
    """
      When comparing two elements with child elements all in the same tag, it
    is required to picked up the most similar pair to generate the diff.
    """
    # When two xml vary only about order

    xmlstring_left = """
      <data>
        <baj>
          <xin>
            <hos>10.10.10.10</hos>
            <foo>abc</foo>
          </xin>
          <xin>
            <hos>20.20.20.20</hos>
          </xin>
          <xin>
            <hos>30.30.30.30</hos>
          </xin>
        </baj>
      </data>
    """
    xmlstring_right = """
      <data>
        <baj>
          <xin>
            <hos>1.1.1.1</hos>
          </xin>
          <xin>
            <hos>10.10.10.10</hos>
            <foo>xyz</foo>
          </xin>
          <xin>
            <hos>10.10.10.10</hos>
            <foo>abc</foo>
            <bar>xyz</bar>
            <toa>xyz</toa>
            <tea>xyz</tea>
            <zab>xyz</zab>
            <kar>xyz</kar>
          </xin>
          <xin>
            <hos>30.30.30.30</hos>
          </xin>
        </baj>
      </data>
    """

    expected = os.linesep.join([
      '[data]',
      '  [baj]',
      '    [xin]',
      '-     <foo>abc</foo>',
      '+     <foo>xyz</foo>',
      '    [xin]',
      '-     <hos>20.20.20.20</hos>',
      '+     <hos>1.1.1.1</hos>',
      '!   <xin>',
      '!     <hos>30.30.30.30</hos>',
      '!   </xin>',
      '+   <xin>',
      '+     <hos>10.10.10.10</hos>',
      '+     <foo>abc</foo>',
      '+     <bar>xyz</bar>',
      '+     <toa>xyz</toa>',
      '+     <tea>xyz</tea>',
      '+     <zab>xyz</zab>',
      '+     <kar>xyz</kar>',
      '+   </xin>'
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


def test_diff_same_tag_move_addition():
    """
    Test situation when a tag was moved and a tag with the same name was added.
    """
    xmlstring_left = """
        <data>
            <foo>100</foo>
            <lat>100</lat>
            <loo>
              <dob>300</dob>
              <lat>400</lat>
            </loo>
        </data>
    """
    xmlstring_right = """
        <data>
          <foo>100</foo>
          <bar>200</bar>
          <lat>100</lat>
          <loo>
            <dob>200</dob>
            <lat>400</lat>
            <dob>300</dob>
          </loo>
        </data>
    """
    expected = os.linesep.join([
        '[data]',
        '! <lat>100</lat>',
        '  [loo]',
        '!   <dob>300</dob>',
        '+   <dob>200</dob>',
        '+ <bar>200</bar>',
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
        '- <bar>200</bar>',
        '+ <bar>20</bar>',
        '  [fan]',
        '    [lol]',
        '      [mia]',
        '-       <qre>3000</qre>',
        '+       <qre>30</qre>',
    ])

    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected

def test_diff_fixes_keys():
    """
    When xml elements which are supposed to  whole branch of xml is involved in the diff, the diff does not collapse it but show all children
    and leaf elements.
    """
    xmlstring_left = """
        <data>
          <vr>0</vr>
          <interface>
            <ifName>200</ifName>
          </interface>
          <interface>
            <ifName>100</ifName>
          </interface>
          <interface>
            <ifName>500</ifName>
            <eol>
              <fen>200</fen>
            </eol>
            <elk>500</elk>
          </interface>
          <interface>
            <ifName>300</ifName>
          </interface>
        </data>
    """
    xmlstring_right = """
        <data>
          <interface>
            <ifName>500</ifName>
            <elk>500</elk>
          </interface>
          <interface>
            <ifName>100</ifName>
          </interface>
          <interface>
            <ifName>400</ifName>
          </interface>
          <interface>
            <ifName>300</ifName>
            <mia>
              <nil>400</nil>
            </mia>
          </interface>
        </data>
    """
    expected = os.linesep.join([
        '[data]',
        '- <vr>0</vr>',
        '- <interface>',
        '-   <ifName>200</ifName>',
        '- </interface>',
        '! <interface>',
        '!   <ifName>100</ifName>',
        '! </interface>',
        '  [interface]',
        '    <ifName>500</ifName>',
        '-   <eol>',
        '-     <fen>200</fen>',
        '-   </eol>',
        '!   <elk>500</elk>',
        '  [interface]',
        '    <ifName>300</ifName>',
        '+   <mia>',
        '+     <nil>400</nil>',
        '+   </mia>',
        # Any added element is put at the tail of the diff.
        '+ <interface>',
        '+   <ifName>400</ifName>',
        '+ </interface>',
    ])
    assert build_xml_diff(xmlstring_left, xmlstring_right) == expected
