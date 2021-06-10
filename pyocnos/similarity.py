"""
This module defines the algorithm to calculate the similarity of two XML
elements. It provides a interface to let the user to match the pairs in two
list of XML elements most close to each other.
Ref:
J. Long, D. G. Schwartz, and S. Stoecklin, An XML Distance Measure, conference
paper on the 2005 International Conference on Data Mining, 2005
https://pdfs.semanticscholar.org/0d15/2846fd30a6898ac518d894c7070ba1ddc44a.pdf
"""
from __future__ import division

from munkres import Munkres

# A small enough value only to state for a similarity between XML elements
# like:
# <foo>100</foo>
# <foo>200</foo>
# or any two elements that contain totally different content with only the
# tag name in common.
A_INFINITESIMAL_SIMILARITY = 0.0001


def hungarian_algorithm(iter_a, iter_b):
    """
    This function utilise hungarian algrorithm to determin how to match
    entries in the given iterables to gain largest similarity. Due to the fact
    the algorithm must relies on metrics of cost, we have to calculate cost
    from similarity as:
    cost = 1 - similarity
    given the fact similarity sits in scope [0, 1]

    Args:
        iter_a: iterable of lxml elements
        iter_b: iterable of lxml elements
    Return:
        cost_matrix: matrix of cost according to row as elements from iter_a
                     and column as elements from iter_b
                     e.g.
                     [[0.1,  0,   0.5],
                      [1,    1,   0]]]
        indexes: list of tuple in the form of indexes to locate elements in
                 cost_matrix
                 e.g., for the above example, the indexes would be
                 [(0, 1), (1, 2)]
    """
    cost_matrix = [[(1 - similarity_element(elem_a, elem_b))
                    for elem_b in iter_b] for elem_a in iter_a]
    indexes = Munkres().compute(cost_matrix)
    return cost_matrix, indexes


def similarity_element(elem_a, elem_b):
    """
    Algorithm to calculate similarity of two XML elements, described in the
    paper quoted on top of this module.
    Basically:
    if two XML elements have different tag, they are different;
    if they are both leaf nodes, compare their value for similarity;
    if only one of them is leaf node and the other has deeper structure, they
    are different;
    if both of them are not leaf nodes, calculate the similarity based on
    their children elements.

    Two adjustments on top the conference paper:
      * calcuate similarity rather than distance
      * assign a very small similary even two elements are totally different
        different, as long as they share the same tag name.

    The reason for the first adjustment is to solve problem like this, try
    compare this XML element e1
      <snmphost>
        <host>10.1.1.1</host>
        <version>1</version>
      </snmphost>
    with e2
      <snmphost>
        <host>10.2.2.2</host>
        <version>2c</version>
      </snmphost>
    and e3
      <snmphost>
        <host>10.1.1.1</host>
        <version>1</version>
        <udp>1</udp>
      </snmphost>
    Using XML distance as metrics, the distance between e1 and e2 is
    1 + 0 / 2 = 0.5, whilst distance between e1 and e3 is
    0 + 0 + 1 / 3 = 0.3. It concludes e1 and e3 are closer, even from edition
    point of view they should be equivalent (one update and one addition).
    However, if we adjust e3 to add one more distinct children,
    so e4
      <snmphost>
        <host>10.1.1.1</host>
        <version>1</version>
        <udp>1</udp>
        <vrfName>management</vrfName>
      </snmphost>
    The distance between e1 and e4 becomes 0 + 0 + 1 + 1 / 4 = 0.5, which
    seems less sensible; and if we carry one and and one more distince element
    to e4, the distance will become 0.6. Now the algorithm concludes e1 and e2
    is closer. To serve the purpose of measuring two XML elements, i.e.
    creating a diff, such behavior reversal would confuse the end user.
    Using similarity as metrics solves this problem by voiding the accumulation
    of distances among different child elements.

    The reason for the other adjustment, i.e. defining a small similarity to
    describe XML elements with the same tag but different comes from this
    problem, for comparing e1
      <snmp>
        <snmphost>
          <host>10.1.1.1</host>
        </snmphost>
      </snmp>
    and e2
      <snmp>
        <snmphost>
          <host>10.2.2.2</host>
        </snmphost>
      </snmp>
    If we judge they are totally different, the presentation of the diff will
    be deletion of e1 and addition of e2, which is a quite large diff. However
    if we decide they are not totally different, after all they have quite the
    same structure, the diffing can go deeper layer and only compare the host
    element, and thus the diff result would be much clearer.
    """
    if elem_a.tag != elem_b.tag:
        return 0

    similarity_v = similarity_value(elem_a, elem_b)

    if len(elem_a) == 0 and len(elem_b) == 0:
        if similarity_v:
            return similarity_v
        return A_INFINITESIMAL_SIMILARITY

    if len(elem_a) == 0 or len(elem_b) == 0:
        return A_INFINITESIMAL_SIMILARITY

    return similarity_array(elem_a, elem_b)


def similarity_value(elem_a, elem_b):
    """This function compares the values of two XML elements """
    if isinstance(elem_a.text, str) and isinstance(elem_b.text, str):
        return elem_a.text.strip() == elem_b.text.strip()

    return elem_a.text == elem_b.text


def similarity_array(iter_a, iter_b):
    """
    This function calculate the total similarity of two list of XML elements,
    which generally are child elements of other nodes.
    This function and similarity_element recursively calles each other.
    """
    matrix, indexes = hungarian_algorithm(iter_a, iter_b)
    # Bear in mind the matrix returned from hungarian algorithm is distnacee
    # (i.e. cost actually) but we need similarity here.
    similarity_sum = (min(len(iter_a), len(iter_b))
                      - sum([matrix[row][column] for row, column in indexes]))
    return similarity_sum/max(len(iter_a), len(iter_b))


def isclose(float_a, float_b, rel_tol=1e-9, abs_tol=0.0):
    """
    Once Python3.5 is applicable this function can be replaced by math.isclose
    """
    return (abs(float_a - float_b)
            <= max(rel_tol * max(abs(float_a), abs(float_b)), abs_tol))


def similarity_indexes(iter_a, iter_b):
    """
    This function generates the index to locate the most similar pair of
    elements in the given XML nodes. It simply strip off entries with too
    small similarity, in case (not very rare) like one element from iter_a
    has nothing like all elements from iter_b, but it would have ended up with
    being yild here with the first element in iter_b even they are totally
    different, and the user will see their diff, and got confused.
    """
    matrix, indexes = hungarian_algorithm(list(iter_a), list(iter_b))
    for row, column in indexes:
        if isclose(matrix[row][column], 1, abs_tol=A_INFINITESIMAL_SIMILARITY/2):
            continue
        yield (row, column)
