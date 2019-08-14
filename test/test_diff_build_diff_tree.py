"""
This test module covers tests cases for function pyocnos.diff.build_diff_tree()
"""
# pylint: disable=invalid-name

from lxml import etree
from pyocnos.diff import normalize_tree, build_diff_tree, ADDED, REMOVED


def compact(xmlstring):
    """
    Helper function to remove redundant white spaces and new lines in xml string
    """
    tree = etree.fromstring(xmlstring)
    for elem in tree.iter('*'):
        if elem.text is not None:
            elem.text = elem.text.strip() or None
        elem.tail = None

    return etree.tostring(tree)


def test_build_diff_tree_empty_reference_tree():
    """
    Edge case: the reference tree has no children but a root only. In this case the diff is all about adding apparently
    """
    tree_left = normalize_tree('<data></data>')
    tree_right = normalize_tree("""
        <data>
          <foo>100</foo>
          <bar><bar_>200</bar_></bar>
        </data>
    """)
    diffs = {
        REMOVED: [],
        ADDED: list(tree_right)
    }

    expected = compact("""
        <data>
          <foo change='added'>100</foo>
          <bar change='added'><bar_>200</bar_></bar>
    </data>
    """)

    assert etree.tostring(build_diff_tree(tree_left, diffs)) == expected


def test_build_diff_tree_empty_diff():
    """
    Edge case: the change set is empty, applying which should not contain any side effects.
    """
    tree_left = normalize_tree('<data><foo>100</foo></data>')
    diffs = {
        REMOVED: [],
        ADDED: []
    }

    expected = '<data><foo>100</foo></data>'

    assert etree.tostring(build_diff_tree(tree_left, diffs)) == expected


def test_build_diff_tree_removal_and_update():
    """
    Scenario: when a change has its "original" element in the reference tree, the diff node should be put where the
    original element is located for clarity. Such case includes deleting an element, or change the element content.
    """
    tree_left = normalize_tree("""
        <data>
          <foo>100</foo>
          <bar>200</bar>
          <loo>
            <dob>300</dob>
            <lat>400</lat>
            <roh>500</roh>
          </loo>
          <kib>600</kib>
        </data>
    """)
    tree_right = normalize_tree("""
        <data>
          <bar>20</bar>
          <loo>
            <dob>30</dob>
            <roh>500</roh>
          </loo>
          <kib>600</kib>
        </data>
    """)
    diffs = {
        REMOVED: [tree_left.find('./foo'), tree_left.find('./bar'),
                  tree_left.find('./loo/dob'), tree_left.find('./loo/lat')],
        ADDED: [tree_right.find('./bar'), tree_right.find('./loo/dob')]
    }

    expected = compact("""
        <data>
            <foo change='removed'>100</foo>
            <bar change='removed'>200</bar>
            <bar change='added'>20</bar>
            <loo>
              <dob change='removed'>300</dob>
              <dob change='added'>30</dob>
              <lat change='removed'>400</lat>
              <roh>500</roh>
            </loo>
            <kib>600</kib>
        </data>
    """)

    assert etree.tostring(build_diff_tree(tree_left, diffs)) == expected


def test_build_diff_tree_addition():
    """
    Scenario: all added elements will be put at a tail position in the reference tree since there is no better position
    """
    tree_left = normalize_tree("""
        <data>
            <foo>100</foo>
            <loo>
              <dob>300</dob>
              <lat>400</lat>
            </loo>
        </data>
    """)
    tree_right = normalize_tree("""
        <data>
        <foo>100</foo>
        <bar>200</bar>
        <loo>
          <lat>500</lat>
          <dob>300</dob>
          <lat>400</lat>
        </loo>
    </data>
    """)
    diffs = {
        REMOVED: [],
        ADDED: [tree_right.find('./bar'), tree_right.find('./loo/lat')]
    }

    expected = compact("""
        <data>
        <foo>100</foo>
        <loo>
          <dob>300</dob>
          <lat>400</lat>
          <lat change='added'>500</lat>
        </loo>
        <bar change='added'>200</bar>
    </data>
    """)

    assert etree.tostring(build_diff_tree(tree_left, diffs)) == expected


def test_build_diff_tree_change_in_same_tag():
    """
    Scenario: When there are some diff between elements with the same tag, the comparison does not go deeper into any
    element, simply because there is no way to tell which two elements to compare. Therefore all elements with a same
    tag will be treated as a single node for the diff.
    """
    tree_left = normalize_tree("""
        <data>
          <foo>100</foo>
          <foo>
            <bar>200</bar>
          </foo>
        </data>
    """)
    tree_right = normalize_tree("""
        <data>
          <foo>
            <bar>20</bar>
          </foo>
        </data>
    """)
    diffs = {
        REMOVED: list(tree_left),
        ADDED: list(tree_right)
    }

    expected = compact("""
        <data>
          <foo change='removed'>100</foo>
          <foo change='added'>
            <bar>20</bar>
          </foo>
          <foo change='removed'>
            <bar>200</bar>
          </foo>
        </data>
    """)

    assert etree.tostring(build_diff_tree(tree_left, diffs)) == expected


def test_build_diff_tree_change_about_identical_elements():
    """
    Scenario: when there are some diff between identical elements, the diff is simply calculated by which side contains
    more. 
    """
    tree_left = normalize_tree("""
        <data>
          <foo>
            <bar>200</bar>
          </foo>
        </data>
    """)
    tree_right = normalize_tree("""
        <data>
          <foo>
            <bar>200</bar>
          </foo>
            <foo>
          <bar>200</bar>
            </foo>
        </data>
    """)
    diffs = {
        REMOVED: [],
        ADDED: [tree_right.find('./foo')]
    }

    expected = compact("""
        <data>
          <foo>
            <bar>200</bar>
          </foo>
          <foo change='added'>
            <bar>200</bar>
          </foo>
        </data>
    """)

    assert etree.tostring(build_diff_tree(tree_left, diffs)) == expected
