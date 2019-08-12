"""
TBD
"""

from __future__ import print_function
import os
import hashlib
import re
from collections import defaultdict, namedtuple
from copy import deepcopy
from lxml import etree


ADDED = 'added'
REMOVED = 'removed'
HashElement = namedtuple('HashElement', ['hash', 'elem'])

def get_path(element):
    """
    Take an element as input and gives back
    the path
    e.g. <vr><vrId>1</vrId><vrId>2</vrId></vr>
    for <vrId>1</vrId> element '/vr/vrId[1]'
    will be returned
    Args:
       element: lxml.Element

    Returns: String e.g. '/vr/vrId[1]'
   """
    return element.getroottree().getpath(element)

def get_parent_path(element):
    """
    TBD
    """
    return element.getroottree().getpath(element.getparent())


def sha(tree):
    """
    TBD
    """
    return hashlib.sha224(etree.tostring(tree)).hexdigest()


def has_changed_children(element):
    """
    TBD
    """
    return element.xpath('.//*[@change="%s"]' % REMOVED) or element.xpath('.//*[@change=%s]' % ADDED)


def has_children(elem):
    """
    TBD
    """
    return len(elem)


def intersection(hashelemes_left, hashelemes_right):
    """
    TBD
    """
    tree_diff = defaultdict(list)
    hashes_left = [hashelem.hash for hashelem in hashelemes_left]
    hashes_right = [hashelem.hash for hashelem in hashelemes_right]

    for hash_ in {x.hash for x in hashelemes_left} & {x.hash for x in hashelemes_right}:
        occurance_diff = hashes_left.count(hash_) - hashes_right.count(hash_)
        if occurance_diff > 0:
            tree_diff[REMOVED].extend([x.elem for x in
                                       (x for x in hashelemes_left if x.hash == hash_)[:occurance_diff]])
        elif occurance_diff < 0:
            tree_diff[ADDED].extend([x.elem for x in
                                     (x for x in hashelemes_right if x.hash == hash_)[occurance_diff:]])

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
        if list(elem):
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


def rrender(tree_diff, count_spaces=0):
    """
    TBD
    """
    result = ['{}[{}]'.format(' '*count_spaces, tree_diff.tag)]
    num_continuous_unchanged_elems = 0
    collapsed = None
    for elem in tree_diff:
        if elem.get('change'):
            if num_continuous_unchanged_elems > 1:
                result.extend([collapsed] if num_continuous_unchanged_elems == 2
                              else ['{}...'.format(' '*(count_spaces+2)), collapsed])
                num_continuous_unchanged_elems = 0

            # Such attribute is not needed any more.
            del elem.attrib['change']

            symbol = {ADDED: '+', REMOVED: '-'}[elem.get('change')]
            xml_string_list = etree.tostring(elem, pretty_print=True) \
                                   .decode('utf-8')                   \
                                   .rstrip(os.linesep)                \
                                   .split(os.linesep)
            result.extend(['{}{} {}'.format(symbol, ' ' * count_spaces, xml) for xml in xml_string_list])

        elif has_changed_children(elem):
            if num_continuous_unchanged_elems > 1:
                result.extend([collapsed] if num_continuous_unchanged_elems == 2
                              else ['{}...'.format(' '*(count_spaces+2)), collapsed])
                num_continuous_unchanged_elems = 0
            for child in elem:
                result.extend(rrender(child, count_spaces+2))
        else:
            if has_children(elem):
                collapsed_elem = '{0}<{1}>...</{1}>'.format(' ' * count_spaces, elem.tag)
            else:
                collapsed_elem = '{}{}'.format(' ' * count_spaces, etree.tostring(elem).decode('utf-8'))

            if num_continuous_unchanged_elems == 0:
                result.append(collapsed_elem)
            num_continuous_unchanged_elems += 1

    if num_continuous_unchanged_elems > 1:
        result.extend([collapsed] if num_continuous_unchanged_elems == 2
                      else ['{}...'.format(' '*(count_spaces+2)), collapsed])
        num_continuous_unchanged_elems = 0
    return result


def build_xml_diff(xmlstring_left, xmlstring_right):
    """
    TBD
    """
    tree_left = normalize_tree(xmlstring_left)
    tree_right = normalize_tree(xmlstring_right)

    tree_left, tree_right = (normalize_tree(xmlstring) for xmlstring in (xmlstring_left, xmlstring_right))

    hash_left = sha(tree_left)
    hash_right = sha(tree_right)
    if hash_left == hash_right:
        # say something about they are identical
        pass
    else:
        diffs = rdiff(HashElement(hash_left, tree_left), HashElement(hash_right, tree_right))

    tree_diff = build_diff_tree(tree_left, diffs)
    rendered_diffs = rrender(tree_diff)
    return '{}'.format(os.linesep).join(rendered_diffs)
