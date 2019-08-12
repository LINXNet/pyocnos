"""
This test module covers tests cases for function pyocnos.diff.rdiff()
"""
# pylint: disable=invalid-name

from lxml import etree
from pyocnos.diff import HashElement, sha, rdiff, normalize_tree


def build_hashelement(xmlstring):
    """
    Helper function to build a HashElement object from an xml string.
    """
    elem = normalize_tree(xmlstring)
    return HashElement(sha(elem), elem)


def text_repr(diffs):
    """
    Helper function to dump xml elements into plain string form for the sake of comparison.
    """
    return {change_type:[etree.tostring(elem) for elem in elems]
            for change_type, elems in diffs.items()}


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


def test_rdiff_simple_intersection_only_with_some_differences():
    """
    Simple case: Each tree contains some grandchildren with differences.
    Sinario:
        set(left) - set(right) = 0
        set(left) & set(right) = 2
        set(right) - set(left) = 0
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data>
          <foo>
            <bar>1</bar>
          </foo>
          <roh>100</roh>
        </data>
    """
    right_tree = """
        <data>
          <roh>100</roh>
          <foo>
            <bar>2</bar>
          </foo>
        </data>
    """

    expected = {
        'removed': ['<bar>1</bar>'],
        'added': ['<bar>2</bar>']
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


def test_rdiff_unique_tags():
    """
    This is a comprehensive case where some elements are the same and some are differnt in either way. The difference
    occurs at different level.
    The point here, however, is no two elements have the same tag.
    Sinario:
        set(left) - set(right) > 0
        set(left) & set(right) > 0
        set(right) - set(left) > 0
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data>
          <A>1</A>
          <B><B_>2</B_></B>
          <C>3</C>
          <D><D_>4</D_></D>
          <E>
            <F>5</F>
            <G><G_>6</G_></G>
            <H>7</H>
            <I><I_>8</I_></I>
            <L>
              <M>
                <N>9</N>
                <O>10</O>
                <P><P_>11</P_></P>
              </M>
            </L>
          </E>
        </data>
    """
    right_tree = """
        <data>
          <C>3</C>
          <D><D_>4</D_></D>
          <E>
            <H>7</H>
            <I><I_>8</I_></I>
            <J>1</J>
            <K><K_>2</K_></K>
            <L>
              <M>
                <N/>
                <P>110</P>
                <O>10</O>
              </M>
            </L>
            <Q><Q_>12</Q_></Q>
            <R>13</R>
          </E>
          <S>14</S>
          <T>
            <U>15</U>
            <V>16</V>
            <W><W_>17</W_></W>
            <X/>
          </T>
        </data>
    """

    expected = {
        'removed': [
            '<N>9</N>',
            '<P><P_>11</P_></P>',
            '<F>5</F>',
            '<G><G_>6</G_></G>',
            '<A>1</A>',
            '<B><B_>2</B_></B>'
        ],
        'added': [
            '<N/>',
            '<P>110</P>',
            '<J>1</J>',
            '<K><K_>2</K_></K>',
            '<Q><Q_>12</Q_></Q>',
            '<R>13</R>',
            '<S>14</S>',
            '<T><U>15</U><V>16</V><W><W_>17</W_></W><X/></T>'
        ]
    }
    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected


def test_rdiff_same_tag_different_content():
    """
    Simple case: only one child element is involvde with no grandchildren elements.
    Sinario:
        set(left) - set(right) = 0
        set(left) & set(right) = 3
        set(right) - set(left) = 0
    Note, in the above pseudo code, set() describes an operation to get the collection of tags of all child elements
    with no duplication.
    """
    left_tree = """
        <data>
          <foo>42</foo>
          <foo>
            <bar>1</bar>
            <doo>2</doo>
          </foo>
        </data>
    """
    right_tree = """
        <data>
          <foo>
            <bar>1</bar>
            <doo>20</doo>
            <pub>3</pub>
          </foo>
        </data>
    """

    expected = {
        'removed': [
            '<foo>42</foo>',
            '<foo><bar>1</bar><doo>2</doo></foo>'
        ],
        'added': [
            '<foo><bar>1</bar><doo>20</doo><pub>3</pub></foo>'
        ]
    }

    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected


def test_rdiff_same_tag_same_content():
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
          <foo>
            <bar>1</bar>
            <doo>2</doo>
          </foo>
          <foo>
            <bar>1</bar>
            <doo>2</doo>
          </foo>
        </data>
    """
    right_tree = """
        <data>
          <foo>
            <bar>1</bar>
            <doo>2</doo>
          </foo>
        </data>
    """

    expected = {
        'removed': [
            '<foo><bar>1</bar><doo>2</doo></foo>'
        ],
        'added': []
    }

    assert text_repr(rdiff(build_hashelement(left_tree), build_hashelement(right_tree))) == expected
