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
import hashlib
import os
import re
from collections import defaultdict, namedtuple
from copy import deepcopy
from lxml import etree

# Two supported change types are declared here.
# It indicates this module treats all sorts of xml element based changes are either an addition or removal.
# Same elements with simply different location at the same level are not counted as a difference.
ADDED = 'added'
REMOVED = 'removed'

# Data structure to pair an xml element and its hash.
HashElement = namedtuple('HashElement', ['hash', 'elem'])

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

def get_parent_path(element):
    """
    Retrive the absolute xpath of the parent of the provided element.
    e.g. <vr><vrId>1</vrId><vrId>2</vrId></vr> as the whole tree,
    for element <vrId>1</vrId>, the path to its parent should be '/vr'.

    Args:
       element: lxml.etree.Element

    Returns: String e.g. '/vr/vrId[1]'
    """
    parent_elem = element.getparent()
    if parent_elem is None:
        raise ValueError('Root element does not have a parent!')

    return element.getroottree().getpath(parent_elem)


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
    tree has an attribute of "change" as one of change types REMOVED or ADDED.

    Args:
        element: lxml.etree.ElementTree or lxml.etree.Element

    Returns: boolean
    """
    return bool(element.xpath('.//*[@change="%s"]' % REMOVED) or element.xpath('.//*[@change=%s]' % ADDED))


def has_children(element):
    """
    Find out whether a xml element contains any children.
    The lxml native approach with len is a bit confusing literaly.

    Args:
        element: lxml.etree.Element

    Returns: boolean
    """
    return bool(len(element))


def intersection(hashelemes_left, hashelemes_right):
    """
    Args:
        hashelemes_left: list of HashElement objects
        hashelemes_right: list of HashElement objects

    Returns: a dictionary like this
             {
                 'removed': [lxml.etree.Element],
                 'added': [lxml.etree.Element]
             }
    """
    tree_diff = defaultdict(list)
    hashes_left = [hashelem.hash for hashelem in hashelemes_left]
    hashes_right = [hashelem.hash for hashelem in hashelemes_right]

    for hash_ in set(hashes_left) & set(hashes_right):
        occurance_diff = hashes_left.count(hash_) - hashes_right.count(hash_)
        if occurance_diff > 0:
            tree_diff[REMOVED].extend([x.elem for x in
                                       [x for x in hashelemes_left if x.hash == hash_][:occurance_diff]])
        elif occurance_diff < 0:
            tree_diff[ADDED].extend([x.elem for x in
                                     [x for x in hashelemes_right if x.hash == hash_][occurance_diff:]])

    return tree_diff


def complement_left(hashelemes_left, hashelemes_right):
    """
    TBD
    """
    return [x.elem for x in hashelemes_left
            if x.hash in ({x.hash for x in hashelemes_left} - {x.hash for x in hashelemes_right})]


def complement_right(hashelemes_left, hashelemes_right):
    """
    TBD
    """
    return [x.elem for x in hashelemes_right
            if x.hash in ({x.hash for x in hashelemes_right} - {x.hash for x in hashelemes_left})]


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


def rdiff(hashelem_left, hashelem_right):
    """
    TBD
    """
    # Or right.values[0].tag, all elements have common tag anyway
    diffs = defaultdict(list)
    # Let's override + so that it can easily extend the list below

    hashed_elements_left = [HashElement(sha(elem), elem) for elem in hashelem_left.elem]
    hashed_elements_right = [HashElement(sha(elem), elem) for elem in hashelem_right.elem]

    for tag in ({elem.tag for elem in hashelem_left.elem} & {elem.tag for elem in hashelem_right.elem}):
        filtered_elems_left = [x for x in hashed_elements_left if x.elem.tag == tag]
        filtered_elems_right = [x for x in hashed_elements_right if x.elem.tag == tag]
        if len(filtered_elems_left) == 1 and len(filtered_elems_right) == 1:
            if has_children(filtered_elems_left[0].elem) and has_children(filtered_elems_right[0].elem):
                deeper_diff = rdiff(filtered_elems_left[0], filtered_elems_right[0])
                diffs[REMOVED].extend(deeper_diff[REMOVED])
                diffs[ADDED].extend(deeper_diff[ADDED])
                hashed_elements_left.remove(filtered_elems_left[0])
                hashed_elements_right.remove(filtered_elems_right[0])

    diffs[REMOVED].extend(complement_left(hashed_elements_left, hashed_elements_right))
    diffs[ADDED].extend(complement_right(hashed_elements_left, hashed_elements_right))
    inter_diff = intersection(hashed_elements_left, hashed_elements_right)
    diffs[REMOVED].extend(inter_diff[REMOVED])
    diffs[ADDED].extend(inter_diff[ADDED])

    return diffs


def build_diff_tree(tree_ref, diffs):
    """
    TBD
    """
    tree_diff = deepcopy(tree_ref)
    for elem in diffs[REMOVED]:
        tree_diff.xpath(get_path(elem))[0].set('change', REMOVED)

    for elem in diffs[ADDED]:
        found = tree_diff.xpath(get_path(elem))
        added_elem = deepcopy(elem)
        added_elem.set('change', ADDED)
        if found:
            found[0].addnext(added_elem)
        else:
            tree_diff.xpath(get_parent_path(elem))[0].append(added_elem)

    return tree_diff


def rrender(tree_diff, indent_initial=0):
    
    def collaps_factory(indent):
        elems = []

        def close_collaps():
            if len(elems) <= 2:
                collapsed_elems = list(elems)
            else:
                collapsed_elems = [elems[0], '{}...'.format(' '*indent), elems[-1]]

            elems[:] = []
            return collapsed_elems

        def collapse(elem):
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
            symbol = {ADDED: '+', REMOVED: '-'}[change_type]

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
    TBD
    """
    tree_left, tree_right = (normalize_tree(xmlstring) for xmlstring in (xmlstring_left, xmlstring_right))

    if tree_left.tag != tree_right.tag:
        raise ValueError('The root tags must be the same! '
                         'left: {}, right: {}'.format(tree_left.tag, tree_right.tag))

    if not has_children(tree_left) and not has_children(tree_right):
        raise ValueError('Comparing simple xml with no children elements is not supported.')

    hash_left = sha(tree_left)
    hash_right = sha(tree_right)
    if hash_left == hash_right:
        print('These two xml are identical.')
        return

    diffs = rdiff(HashElement(hash_left, tree_left), HashElement(hash_right, tree_right))
    # Two xml can be identical, even their hash are different, when they contain same elements with simply different
    # order. Stop here to void rrender rendering a tree identical as tree_left.
    if not diffs[REMOVED] and not diffs[ADDED]:
        print('These two xml are identical.')
        return

    tree_diff = build_diff_tree(tree_left, diffs)
    rendered_diffs = rrender(tree_diff)

    # Till here we have a xml tree with indication of diff and collaps of same elements. Prettify the result and return.
    return '{}'.format(os.linesep).join(rendered_diffs)
