"""
Class for diffing Elements
"""
import hashlib
import os
from collections import defaultdict
from copy import deepcopy

from future.backports import OrderedDict
from lxml import etree
from lxml.etree import cleanup_namespaces
from pyocnos.diff import SAME, MOVED, ADDED, REMOVED
from pyocnos.diff import get_element_path


class Block(object):
    """
    Class takes running element and candidate element
    and a diff can be produced in lxml.Element object or a list of
    strings showing diff for example ['[vr]','- <vrId>2</vrId>','- <foo>1</foo>']
    """

    def __init__(self, running, candidate):
        """
        Args:
            running: lxml.Element
            candidate: lxml.Element
        """
        self.running = running
        self.candidate = candidate
        self.final_diff = None
        self.added_or_removed_running_ele = None
        self.added_or_removed_candidate_ele = None
        self.elements_for_diff_on_running = self._get_elements_for_diff(self.running)
        self.elements_for_diff_on_candidate = self._get_elements_for_diff(self.candidate)

    def get_name(self):
        """
        Get name of the block
        Returns: (String) for example 'vr'

        """
        if self.running is not None:
            element = self.running
        else:
            element = self.candidate
        element_path = get_element_path(element)
        return ' '.join(element_path.strip('/').split('/'))

    def get_diff(self):
        """
        Create the diff
        Returns: (lxml.Element) showing diff in Element form
            for example <vr><same><vrId><mac>1</mac></vrId></same><added><vrId><mac>3</mac></vrId></added></vr>

        """
        # if any one is none return added or removed accordingly
        if self.candidate is None:
            return self._surround_element_with_tag(self.running, REMOVED)
        elif self.running is None:
            return self._surround_element_with_tag(self.candidate, ADDED)
        else:
            self._add_same_and_moved_diff()
            seen_candidate_elements = self._update_final_diff_for_running()
            self._update_final_diff_for_candi(seen_candidate_elements)
        return self.final_diff

    def get_printable_diff(self):
        """
        Get the diff in printable format including spaces and symbols

        Returns: List of strings for example ['[vr]','- <vrId>2</vrId>','- <foo>1</foo>']

        """
        diff_xml = self.get_diff()
        block_name = self.get_name()
        result = ['[{}]'.format(block_name)]
        if diff_xml.tag != block_name:
            # whole block got changed someway
            result.extend(
                [self._format_element_with_symbols(ele_as_string) for ele_as_string in etree.tostringlist(diff_xml)]
            )
        else:
            if diff_xml.xpath('.//removed | .//added | .//moved'):
                for element in diff_xml:
                    print_same = (element.tag == SAME and len(element) == 1 and
                                  len(diff_xml.xpath('.//{}'.format(element[0].tag))) == 1)

                    self._append_element_as_string(element, result, print_same=print_same)
        return result if len(result) > 1 else []

    def _append_element_as_string(self, element, result, spaces=0, print_same=False):
        """
        If element has same tag than check if any siblings were changed or
        print_same is true then print and collapse.

        if have moved removed or added tag the print everything
        else
        print the element startibg tag and call itself and append closing tag
        Args:
            element: (lxml.Element) Actual element which is being converted to list if strings
            result: (List) A list of string which is being updated
                and element representation as string is being added
            spaces: (Integer) How many space to move the tags when converting to string
            print_same: (Boolean) Should the elements which have the same tag be converted to string or not

        Returns: None

        """
        if element.tag == SAME:
            spaces += 2
            if print_same:
                for child in element.getchildren():
                    result.append(self._collapse_element(child, spaces))
        elif element.tag in [MOVED, ADDED, REMOVED]:
            symbol_map = {MOVED: '!', ADDED: '+', REMOVED: '-'}
            symbol = symbol_map[element.tag]
            for child in element:
                result.extend(self._append_symbol(child, symbol, spaces))
        else:
            spaces += 2
            changed_elements = element.xpath('.//removed | .//added | .//moved')
            if list(changed_elements):
                result.append('{}<{}>'.format(' ' * spaces, element.tag))
                for child in element:
                    self._append_element_as_string(child, result, spaces=spaces, print_same=True)
                result.append('{}</{}>'.format(' ' * spaces, element.tag))
            else:
                result.append(self._collapse_element(element, spaces))

    def _add_same_and_moved_diff(self):
        """
        Loop over running elements for diff and see if hashes match with candidates
        Structure looks like this
        {
            'VrId':
                OrderedDict(
                    [('fc53984049a587e9669a83a8b677d462bd1de5b08ca6b0a96016ebde', < Element VrId at 0x107880e88 >)]),
            'vrf': OrderedDict(
                    [('80825a252287dfba434456e35431f5699db61043ebf70067d42135ba', < Element vrf at 0x107892308 >)])
        }
        Returns: None


        """
        running_elements_to_diff = defaultdict(list)
        candidate_elements_to_diff = defaultdict(list)
        candidate_elements = {}

        hashes_seen = []
        self.final_diff = etree.Element(self.get_name())
        for ele_name, running_elements in self.elements_for_diff_on_running.items():
            for index, (running_elem_hash, running_element) in enumerate(running_elements.items()):
                try:
                    candidate_elements = self.elements_for_diff_on_candidate[ele_name]
                except KeyError:
                    running_elements_to_diff[ele_name].append(running_element)
                else:
                    candidate_hash_list = list(candidate_elements.keys())
                    if running_elem_hash in candidate_elements:
                        hashes_seen.append(running_elem_hash)
                        try:
                            candidate_elem_hash = candidate_hash_list[index]
                        except IndexError:
                            candidate_elem_hash = None
                        if running_elem_hash == candidate_elem_hash:
                            etree.SubElement(self.final_diff, SAME).append(deepcopy(running_element))
                        else:
                            etree.SubElement(self.final_diff, MOVED).append(deepcopy(running_element))
                    else:
                        running_elements_to_diff[running_element.tag].append(running_element)

        for ele_name, candidate_elements in self.elements_for_diff_on_candidate.items():
            for candidate_element_hash, candidate_element in candidate_elements.items():
                if candidate_element_hash not in hashes_seen:
                    candidate_elements_to_diff[candidate_element.tag].append(candidate_element)

        self.added_or_removed_running_ele = running_elements_to_diff
        self.added_or_removed_candidate_ele = candidate_elements_to_diff

    def _update_final_diff_for_candi(self, seen_candidate_elements):
        """
        Loop over candidate elements if not in the seen_candidate_elements list
        than add added tag and append to the final_diff
        Args:
            seen_candidate_elements:

        Returns: None

        """
        for candidate_elements in self.added_or_removed_candidate_ele.values():
            for candidate_element in candidate_elements:
                if candidate_element not in seen_candidate_elements:
                    self.final_diff.append(Block._surround_element_with_tag(candidate_element, ADDED))

    def _update_final_diff_for_running(self):
        """
        self.added_or_removed_running_elements example
        {
            'VrId':
                OrderedDict(
                    [('fc53984049a587e9669a83a8b677d462bd1de5b08ca6b0a96016ebde', < Element VrId at 0x107880e88 >)]),
            'vrf': OrderedDict(
                    [('80825a252287dfba434456e35431f5699db61043ebf70067d42135ba', < Element vrf at 0x107892308 >)])
        }
        loop over the above structure and try diff one individual running and
        candidate elements and add it to final diff
        Returns: List of candidate elements already seen

        """
        seen_candidate_elements = []
        for element_tag, running_elements in self.added_or_removed_running_ele.items():
            for index, running_element in enumerate(running_elements):
                candidates_under_same_tag = self.added_or_removed_candidate_ele.get(element_tag)
                candidate_element = None
                if candidates_under_same_tag:
                    try:
                        candidate_element = candidates_under_same_tag[index]
                    except IndexError:
                        pass
                seen_candidate_elements.append(candidate_element)
                for diff in self._get_diff_on_two_elements(running_element, candidate_element):
                    self.final_diff.append(diff)
        return seen_candidate_elements

    @staticmethod
    def _get_diff_on_two_elements(running, candidate):
        """
        If
            candidate element is None than just add removed tag
            around the whole running element
        else
            if
                running element has no children add removed(on running) and
                added (on candidate) tags and append to the diff
            else
                iterate over running elements until find one with no child and compare
                if text are not equal add removed and added tags else
                add same tags
        Args:
            running: lxml.Element
            candidate: lxml.Element

        Returns: List of lxml.Element representing the diff
            for example ['<same><vrId><mac>1</mac></vrId></same>', '<added><vrId><mac>3</mac></vrId></added>']
            if element converted to string.

        """
        diffs = []
        # make a copy to have no hierarchy and can compare elements
        running = deepcopy(running)
        candidate = deepcopy(candidate)
        if candidate is not None:
            if list(running):
                diffs.append(Block._get_diff_on_children(running, candidate))
            else:
                diffs.append(Block._surround_element_with_tag(running, REMOVED))
                diffs.append(Block._surround_element_with_tag(candidate, ADDED))
        else:
            diffs.append(Block._surround_element_with_tag(running, REMOVED))

        return diffs

    @staticmethod
    def _get_diff_on_children(running_element, candidate_element):
        """

        Args:
            candidate_element: lxml.Element <vrId><mac>1</mac></vrId>
            running_element: lxml.Element <vrId><mac>2</mac></vrId>

        Returns: lxml.Element representing the diff as Element
            For example <vrId><removed><mac>1</mac></removed><added><mac>2</mac></added></vrId> if element
            converted to string

        """
        seen_path = []
        diff = deepcopy(running_element)
        for running_child in running_element.iter():
            running_child_path = get_element_path(running_child)
            if not list(running_child):
                seen_path.append(running_child_path)
                try:
                    running_child_on_diff = diff.xpath(running_child_path)[0]
                except IndexError:
                    continue
                running_child_parent_on_diff = running_child_on_diff.getparent()
                try:
                    candidate_child = candidate_element.xpath(running_child_path)[0]
                except IndexError:
                    running_child_parent_on_diff.remove(running_child_on_diff)
                    running_child_parent_on_diff.append(Block._surround_element_with_tag(running_child, REMOVED))
                else:
                    if running_child.text != candidate_child.text:
                        running_child_parent_on_diff.remove(running_child_on_diff)

                        running_child_parent_on_diff.append(Block._surround_element_with_tag(running_child, REMOVED))
                        running_child_parent_on_diff.append(Block._surround_element_with_tag(candidate_child, ADDED))
                    else:
                        running_child_parent_on_diff.remove(running_child_on_diff)
                        running_child_parent_on_diff.append(Block._surround_element_with_tag(running_child, SAME))

        for candidate_child in candidate_element.iter():
            if candidate_child.getparent() is not None:
                candidate_child_path = get_element_path(candidate_child)
                if candidate_child_path not in seen_path:
                    candidate_child_parent_path = get_element_path(candidate_child.getparent())
                    running_child = running_element.xpath(candidate_child_path)
                    if not list(running_child) and candidate_child_parent_path not in seen_path:
                        try:
                            candidate_child_parent_on_diff = diff.xpath(candidate_child_parent_path)[0]
                        except IndexError:
                            continue
                        candidate_child_parent_on_diff.append(Block._surround_element_with_tag(candidate_child, ADDED))
                        seen_path.append(candidate_child_path)
        return diff

    @staticmethod
    def _get_elements_for_diff(element):
        """
        Cleanup namespaces and remove text when have children
        and tail. For all the children create hashes and create an ordered Dict
        where key is the element tag followed by element hash and element itself as the
        value.
        Args:
            element: lxml.Element

        Returns: Dict For example
            {
                'Vrd':
                    OrderedDict(
                        [('fc53984049a587e9669a83a8b677d462bd1de5b08ca6b0a96016ebde', < Element Vrd at 0x107880e88 >)]),
                'vrf': OrderedDict(
                        [('80825a252287dfba434456e35431f5699db61043ebf70067d42135ba', < Element vrf at 0x107892308 >)])
            }
        """
        # there is no default ordered dict hance using Ordered dict and then checking
        # for the key below
        elements_for_diff = OrderedDict()
        if element is not None:
            cleanup_namespaces(element)
            for child in element.iter():
                if list(child):
                    child.text = None
                child.tail = None

            for child_element in element:
                ele_hash = hashlib.sha224(etree.tostring(child_element)).hexdigest()
                if child_element.tag not in elements_for_diff:
                    elements_for_diff[child_element.tag] = OrderedDict()
                elements_for_diff[child_element.tag][ele_hash] = child_element
        return elements_for_diff

    @staticmethod
    def _format_element_with_symbols(element_string):
        """
        Replace removed added tags with symbols
        Args:
            element_string: (String) '<removed><vr>1234</vr></removed>'

        Returns: (String) '- <vr>1234</vr>'

        """
        element_as_string = element_string.decode('utf-8')
        element_as_string = element_as_string.replace('<added>', '+ ').replace('</added>', '')
        element_as_string = element_as_string.replace('<removed>', '- ').replace('</removed>', '')
        return element_as_string

    @staticmethod
    def _surround_element_with_tag(element, tag):
        """
        Get an element and surround it with given tag name
        Args:
            element: lxml.Element '<enabled>false</enabled>'
            tag: String 'removed'

        Returns: lxml.Element For example <removed><enabled>false</enabled></removed>

        """
        tag_element = etree.Element(tag)
        tag_element.append(deepcopy(element))
        return tag_element

    @staticmethod
    def _collapse_element(element, spaces):
        """
        Collapse an element to string
        Args:
            element: (lxml.Element) '<ifName>po1</ifName>'
            result: (List) ['[vr]', '  <interface>',]
            spaces: (Integer) 2

        Returns: (String) '    <ifName>po1</ifName>'

        """
        if list(element):
            result = '{0}<{1}>...</{1}>'.format(' ' * spaces, element.tag)
        else:
            result = '{}{}'.format(' ' * spaces, etree.tostring(element).decode('utf-8'))
        return result

    @staticmethod
    def _append_symbol(element, symbol, spaces):
        """
        Create list of elements with pretty print appending symbol to each line
        If it has children spaces are ignored
        Args:
            element: (lxml.Element) <vrf><vrfName>FOO-LON3</vrfName><macVrf>true</macVrf></vrf>
            symbol: (String) '!'

        Returns: (List of string)
            For example ['! <vrf>', '!   <vrfName>FOO-LON3</vrfName>', '!   <macVrf>true</macVrf>', '! </vrf>']

        """
        if list(element):
            spaces = 0
        formatted_xml = etree.tostring(element, pretty_print=True).decode('utf-8').rstrip(os.linesep)
        formatted_xml_list = formatted_xml.split(os.linesep)
        return ['{}{} {}'.format(symbol, ' ' * spaces, xml) for xml in formatted_xml_list]
