"""
This module allows comparison between two xml trees. The generated diff shows all added or removed xml elements, from a
"right" tree against a "left" tree. It ignores identical elements in different order with siblings. The module also
does not count a lot aspects, e.g. name spaces, attributes, white spaces and any invisible characters, etc.

Usage:
 > from pyocnos.diff import build_xml_diff
 > xmlstring_left = "<data><foo>100</foo></data>"
 > xmlstring_right = "<data><foo>10</foo></data>"
 > print(build_xml_diff(xmlstring_left, xmlstring_right))
 [data]
 - <foo>100</foo>
 + <foo>10</foo>

"""

from __future__ import print_function

from collections import defaultdict, namedtuple
from copy import deepcopy
import hashlib
import os
import re

from lxml import etree

# Four supported change types are declared here.
# It indicates this module treats all sorts of xml element based changes are either an added, moved or removed.
ADDED = 'added'
MOVED = 'moved'
REMOVED = 'removed'
SAME = 'same'
DIFF_SYMBOLS = {MOVED: '!', ADDED: '+', REMOVED: '-'}

# Data structure to pair an xml element and its hash.
HashElement = namedtuple('HashElement', ['hash', 'elem'])


def utf8(obj):
    """
    This helper function attempts to decode a string like object to utf-8 encoding.
    For Python2 it just works.
    For Python3 a string object does not have decode mehtod whilst a byte object does.
    """
    try:
        value = obj.decode('utf-8')
    except AttributeError:
        value = obj

    return value


def get_path(element):
    """
    Retrive the absolute xpath of the provided element.
    e.g. <vr><vrId>1</vrId><vrId>2</vrId></vr> as the whole tree,
    for element <vrId>1</vrId>, its path should be '/vr/vrId[1]'.

    Args:
       element: lxml.etree.Element

    Returns: String e.g. '/vr/vrId[1]'
    """
    return element.getroottree().getpath(element)


def sha(tree):
    """
    Generate a hash to a xml tree from its string presentation.

    Args:
        tree: lxml.etree.ElementTree or lxml.etree.Element.
              Named tree here to emphasize the hash counts its children if any

    Returns: None
    """
    return hashlib.sha224(etree.tostring(tree)).hexdigest()


def has_changed_children(element):
    """
    Find out whether a xml element in a xml diff tree contains any changed children. A changed element in a xml diff
    tree has an attribute of "change" as one of change types REMOVED, MOVED or ADDED.

    Args:
        element: lxml.etree.ElementTree or lxml.etree.Element

    Returns: boolean
    """
    return any(element.xpath('.//*[@change="%s"]' % type) for type in [ADDED, MOVED, REMOVED])


def has_children(element):
    """
    Find out whether a xml element contains any children.
    The lxml native approach with len is a bit confusing literaly.

    Args:
        element: lxml.etree.Element

    Returns: boolean
    """
    return bool(len(element))


def ordering_intersection(hashelements_left, hashelements_right):
    """
    Collects elements that belongs to hashelements_a and also to hashelements_b
    (respecting the counts of same elements in both lists). For those elemets
    returns lists of elements on the same position and reordered elements.

    Args:
        hashelements_left: [HashElement]
        hashelements_right: [HashElement]

    Returns: a dictionary like this
             {
                 'moved': [HashElement],
                 'same': [HashElement]
             }
    """
    tree_diff = defaultdict(list)
    hashes_left = [hashelem.hash for hashelem in hashelements_left]
    hashes_right = [hashelem.hash for hashelem in hashelements_right]

    common_hashes = set(hashes_left) & set(hashes_right)
    for hash_ in sorted(common_hashes):
        left_indexes = {i for i, elem in enumerate(hashelements_left) if elem.hash == hash_}
        right_indexes = {i for i, elem in enumerate(hashelements_right) if elem.hash == hash_}
        same_indexes = left_indexes & right_indexes
        potential_moved_indexes = left_indexes - right_indexes
        tree_diff[SAME].extend(hashelements_left[i] for i in same_indexes)
        # number of (moved elements + same elements) can't be more than
        # number of those elements is in the right list
        moved_count = min(len(left_indexes), len(right_indexes)) - len(same_indexes)
        tree_diff[MOVED].extend(hashelements_left[i] for i in list(potential_moved_indexes)[:moved_count])

    return tree_diff


def normalize_tree(xmlstring):
    """
    Build xml tree from string in normalised form for the sake of comparison.
    Note, it does not mean to convert to canonical xml. For example, canonical
    xml requires explicit default values, which is not necessary for the
    purpose of xml diff.

    The "normalised" here means:
     * No name spaces
     * Element value contains no invisible characters like new line
     * Element value converted to None in case of empty string
    """
    # Stripe off all default name spaces.
    xmlstring = re.sub(r'\sxmlns="[^"]+"', '', xmlstring)

    # Remove pure white space string with customised xml parser
    parser = etree.XMLParser(remove_blank_text=True)

    tree = etree.XML(xmlstring, parser=parser)

    # Loop over all elements and do...
    for elem in tree.iter('*'):
        # Single tag is not supported
        elem.tail = None

        # Any element with children should just be a container with no settings
        if has_children(elem):
            elem.text = None

        if elem.text is not None:
            # ensure elem.text is None if its value is nothing but
            # invisible characters
            elem.text = elem.text.strip() or None
        if elem.prefix is not None:
            # Remove name space for any element if used
            elem.tag = etree.QName(elem).localname

    # Remove redundant name spaces. After this statement, all type of name
    # spaces have been removed.
    etree.cleanup_namespaces(tree)

    return tree


def mark_ref_path(path, elems):
    """
    Set attribute to the value of path for all elements in elems.

    Args:
        path: string
        elems: [lxml.etree.Element]

    Returns: a new list with same content
    """
    return [elem.attrib.update({'ref_path': path}) or elem for elem in elems]


def rdiff(hashelem_left, hashelem_right):
    """
    Recursively create diff information between two elements provided in arguments.
    It goes through each level of both xml trees, collects added, moved or removed elements,
    and only goes into deeper layer if two elements share the same tag and have children.

    Args:
        hashelem_left: HashElement object
        hashelem_right: HashElement object

    Returns: a dictionary like this
        {
            'removed': [lxml.etree.Element],
            'added': [lxml.etree.Element],
            'moved': [lxml.etree.Element],
        }

    """
    # Or right.values[0].tag, all elements have common tag anyway
    diffs = defaultdict(list)

    hashed_elements_left = [HashElement(sha(elem), elem) for elem in hashelem_left.elem]
    hashed_elements_right = [HashElement(sha(elem), elem) for elem in hashelem_right.elem]

    # Comparing elements with the same hash but reordered
    inter_diff = ordering_intersection(hashed_elements_left, hashed_elements_right)
    diffs[MOVED].extend([helem.elem for helem in inter_diff[MOVED]])
    for hashelem in inter_diff[MOVED] + inter_diff[SAME]:
        hashed_elements_left.remove(hashelem)
        for helem in hashed_elements_right:
            if helem.hash == hashelem.hash:
                hashed_elements_right.remove(helem)
                break

    # Comparing elements with the same tag name (and not completelly same)
    for tag in ({elem.tag for elem in hashelem_left.elem} & {elem.tag for elem in hashelem_right.elem}):
        filtered_elems_left = [x for x in hashed_elements_left if x.elem.tag == tag]
        filtered_elems_right = [x for x in hashed_elements_right if x.elem.tag == tag]

        for hashelem_l, hashelem_r in zip(filtered_elems_left, filtered_elems_right):
            if has_children(hashelem_l.elem) and has_children(hashelem_r.elem):
                deeper_diff = rdiff(hashelem_l, hashelem_r)
                for change_type in deeper_diff:
                    diffs[change_type].extend(deeper_diff[change_type])
                hashed_elements_left.remove(hashelem_l)
                hashed_elements_right.remove(hashelem_r)

    # Remaining elements
    diffs[REMOVED].extend(hashelem.elem for hashelem in hashed_elements_left)
    diffs[ADDED].extend(mark_ref_path(get_path(hashelem_left.elem),
                                      [hashelem.elem for hashelem in hashed_elements_right]))

    return diffs


def build_diff_tree(tree_ref, diffs):
    """
    Create a xml tree using provided diff information based on a reference xml tree.
    The tree_ref is generally the left tree to compare with.

    Args:
        tree_ref: lxml.etree.Element
        diffs: a dictionary like this
            {
                'removed': [lxml.etree.Element],
                'added': [lxml.etree.Element],
                'moved': [lxml.etree.Element],
            }

    Returns: lxml.etree.element
    """
    tree_diff = deepcopy(tree_ref)
    for elem in diffs[REMOVED]:
        tree_diff.xpath(get_path(elem))[0].set('change', REMOVED)
    for elem in diffs[MOVED]:
        tree_diff.xpath(get_path(elem))[0].set('change', MOVED)

    for elem in diffs[ADDED]:
        ref_path = elem.attrib.pop('ref_path')
        found = tree_diff.xpath('{}/{}'.format(ref_path, elem.tag))
        added_elem = deepcopy(elem)
        added_elem.set('change', ADDED)
        elem.set('ref_path', ref_path)
        if found:
            found[-1].addnext(added_elem)
        else:
            tree_diff.xpath(ref_path)[0].append(added_elem)

    return tree_diff


def rrender(tree_diff, indent_initial=0):
    """
    Recursively render a provided diff xml tree with a given indent.
    The tree_diff contains information about which element is added, moved or removed, which will be renderd with
    +, ! or - symbol in front with proper indent to have a pretty output.

    Args:
        tree_diff: lxml.etree.Element
        indent_initial: how many white spaces for indention to render this tree

    Returns: a string representation of the diff tree
    """
    def collaps_factory(indent):
        """
        This internal function maintains a list of unchanged elements before a change is hit.
        When this function is called, it provides two function to access this list, one to add element in and one to
        render the list into a collapsed form before it reset the list.

        Args:
            indent: number of white spaces as indention for all unchanged elements

        Returns:
            collapse: function to add an unchanged element
            close_collaps: function to collapse the element list so far
        """
        elems = []

        def close_collaps():
            """
            This function renders the element list in a collapsed form.

            Returns: collapsed element list
            """
            if len(elems) <= 2:
                collapsed_elems = list(elems)
            else:
                collapsed_elems = [elems[0], '{}...'.format(' '*indent), elems[-1]]

            elems[:] = []
            return collapsed_elems

        def collapse(elem):
            """
            This function adds the provided element into the list inside the closure.

            Args:
                elem: lxml.etree.Element

            Return: None
            """
            if has_children(elem):
                elems.append('{0}<{1}>...</{1}>'.format(' ' * indent, elem.tag))
            else:
                elems.append('{}{}'.format(' '*indent, etree.tostring(elem).decode('utf-8')))

        return collapse, close_collaps

    if not has_children(tree_diff):
        raise ValueError('A diff tree without any children is not supported.')

    result = ['{}[{}]'.format(' '*indent_initial, tree_diff.tag)]
    collaps_start, collapse_finish = collaps_factory(indent_initial+2)
    for elem in tree_diff:
        if elem.get('change'):
            result.extend(collapse_finish())

            change_type = elem.attrib.pop('change')
            symbol = DIFF_SYMBOLS[change_type]

            xml_string_list = etree.tostring(elem, pretty_print=True) \
                                   .decode('utf-8')                   \
                                   .rstrip(os.linesep)                \
                                   .split(os.linesep)
            result.extend(['{}{}{}'.format(symbol, ' ' * (indent_initial+1), xml) for xml in xml_string_list])
            elem.attrib['change'] = change_type

        elif has_changed_children(elem):
            result.extend(collapse_finish())
            result.extend(rrender(elem, indent_initial+2))

        else:
            collaps_start(elem)

    result.extend(collapse_finish())

    return result


def build_xml_diff(xmlstring_left, xmlstring_right):
    """
    Main entry of the module, which generates a string representation of the diff between two xml tree.

    Args:
        xmlstring_left: serialised xml
        xmlstring_right: serialised xml

    Returns: diff in string
    """
    tree_left, tree_right = (normalize_tree(xmlstring) for xmlstring in (utf8(xmlstring_left), utf8(xmlstring_right)))

    if tree_left.tag != tree_right.tag:
        raise ValueError('The root tags must be the same! '
                         'left: {}, right: {}'.format(tree_left.tag, tree_right.tag))

    if not (has_children(tree_left) and has_children(tree_right)):
        raise ValueError('Comparing simple xml with no children elements is not supported.')

    hash_left = sha(tree_left)
    hash_right = sha(tree_right)
    if hash_left == hash_right:
        return ''

    diffs = rdiff(HashElement(hash_left, tree_left), HashElement(hash_right, tree_right))
    tree_diff = build_diff_tree(tree_left, diffs)
    rendered_diffs = rrender(tree_diff)

    # Till here we have a xml tree with indication of diff and collaps of same elements. Prettify the result and return.
    return '{}'.format(os.linesep).join(rendered_diffs)
