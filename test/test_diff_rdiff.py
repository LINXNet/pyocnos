"""
"""

from lxml import etree
from pyocnos.diff import HashElement, sha, rdiff, normalize_tree


def build_hashelement(xmlstring):
  elem = normalize_tree(xmlstring)
  return HashElement(sha(elem), elem)


def text_repr(diffs):
  return {change_type:[etree.tostring(elem) for elem in elems] for change_type,elems in diffs.items()}


def test_rdiff_simple_left_complement_only():
    """
    Simple case: only one child element is involvde with no grandchildren elements.
    Sinario:
        set(left) - set(right) = 1
        set(left) & set(right) = 0
        set(right) - set(left) = 0
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data>
          <foo>42</foo>
        </data>
    """
    right_tree = """
        <data/>
    """

    expected = {
        'removed': ['<foo>42</foo>'],
        'added': []
    }

    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected


def test_rdiff_simple_right_complement_only():
    """
    Simple case: only one child element is involvde with no grandchildren elements.
    Sinario:
        set(left) - set(right) = 0
        set(left) & set(right) = 0
        set(right) - set(left) = 1
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data/>
    """
    right_tree = """
        <data>
          <foo>42</foo>
        </data>
    """

    expected = {
        'removed': [],
        'added': ['<foo>42</foo>']
    }

    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected


def test_rdiff_simple_intersection_only_and_they_are_identical():
    """
    Simple case: only one child element is involvde with no grandchildren elements.
    Sinario:
        set(left) - set(right) = 0
        set(left) & set(right) = 1
        set(right) - set(left) = 0
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data>
          <foo>42</foo>
        </data>
    """
    right_tree = """
        <data>
          <foo>42</foo>
        </data>
    """

    expected = {
        'removed': [],
        'added': []
    }

    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected


def test_rdiff_simple_intersection_only_and_they_are_different():
    """
    Simple case: only one child element is involvde with no grandchildren elements.
    Sinario:
        set(left) - set(right) = 0
        set(left) & set(right) = 1
        set(right) - set(left) = 0
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data>
          <foo>42</foo>
        </data>
    """
    right_tree = """
        <data>
          <foo>47</foo>
        </data>
    """

    expected = {
        'removed': ['<foo>42</foo>'],
        'added': ['<foo>47</foo>']
    }

    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected