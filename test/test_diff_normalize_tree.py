"""
This test module covers tests cases for function pyocnos.diff.normalize_tree()
"""

from lxml import etree

from pyocnos.diff import normalize_tree


def test_normalize_tree():
    """
    Ensure normalize_tree() wipe off name spaces, prefixes, redundant white spaces and new lines.
    """
    string = """
      <data xmlns="http://www.company.com/TOOSchema/BarOS"
            xmlns:a="http://www.company.com/TOOSchema/BarOS"
            xmlns:b="http://www.company.com/TOOSchema/BarOS">
        <snmp xmlns="http://www.company.com/TOOSchema/BarOS">  foo
              </snmp>


        <vr xmlns="http://www.company.com/TOOSchema/BarOS"></vr>
        <a:logginglevel><loggingmodule>
          bgp</loggingmodule>  </a:logginglevel>
        <interface>
            </interface>

      </data>
    """
    tree_raw = etree.fromstring(string)
    assert tree_raw.tag == '{http://www.company.com/TOOSchema/BarOS}data'
    assert tree_raw[2].tag == '{http://www.company.com/TOOSchema/BarOS}logginglevel'
    assert tree_raw[3].text == '\n            '

    tree_normalised = normalize_tree(string)
    assert etree.tostring(tree_normalised) == \
      '<data><snmp>foo</snmp><vr/><logginglevel><loggingmodule>bgp</loggingmodule></logginglevel><interface/></data>'
    assert tree_normalised.tag == 'data'
    assert tree_normalised[0].tag == 'snmp'
    assert tree_normalised[1].tag == 'vr'
    assert tree_normalised[2].tag == 'logginglevel'
