"""
Class for diffing xmls
"""
from __future__ import print_function
from copy import deepcopy
from lxml import etree

from pyocnos.diff import get_element_path
from pyocnos.diff.block import Block


class XmlDiff(object):
    """
    Class given two xml produces a diff
    """

    def __init__(self, running_xml, candidate_xml):
        """
            XmlDiff constructor
        Args:
            running_xml: String
            candidate_xml: String
        Returns: None
        """
        self.running_xml = self._strip_ns_prefix(etree.fromstring(running_xml))
        self.candidate_xml = self._strip_ns_prefix(etree.fromstring(candidate_xml))
        self._diff = []
        self._seen_paths = set()

    def get_printable_diff(self):
        """
        Get blocks and call get_printable_diff on all
        Returns: (List) E.g. ['[vr]','- <vrId>2</vrId>','- <foo>1</foo>']

        """
        result = []
        for block in self._get_elements_blocks():
            result.extend(block.get_printable_diff())
        return result

    def print_diff(self):
        """
        Actually print the diff
        Returns: None

        """
        for line in self.get_printable_diff():
            print(line)

    def _get_elements_blocks(self):
        """
            Loop over candidate and running children and create blocks and
            do a diff one each block
            Returns: (List of Blocks) For example if we have running xml as
             <vr><vrId>1</vrId><vrId>2</vrId></vr><ssh>foo</ssh>
             and candidate xml as <vr><vrId>1</vrId><vrId>3</vrId></vr><ssh>foo</ssh>
             Two blocks will be created one for VR and one for SSH

        """
        blocks = []
        running_paths = []
        for running_child in self.running_xml:
            running_paths.append(get_element_path(running_child))
            blocks.append(
                Block(
                    running=deepcopy(running_child),
                    candidate=deepcopy(self._get_candidate_element(running_child))
                )
            )
        for candidate_child in self.candidate_xml:
            candidate_child_path = get_element_path(candidate_child)
            if candidate_child_path not in running_paths:
                blocks.append(Block(running=None, candidate=deepcopy(candidate_child)))
        return blocks

    def _get_candidate_element(self, running_element):
        """
        Get candidate element with the give running elements
        Args:
            running_element: lxml.Element

        Returns: (lxml.Element) or (None) Candidate element with same path

        """
        candidate_element = None
        path = get_element_path(running_element)
        candidate_elements = self.candidate_xml.xpath(path)
        if candidate_elements:
            candidate_element = candidate_elements[0]
        return candidate_element

    @staticmethod
    def _strip_ns_prefix(tree):
        """
        Remove namespaces
        Args:
            tree: lxml.Etree

        Returns: (lxml.Etree) Etree with no namespaces
            E.g. <snmp xmlns="http://www.company.com/TOOSchema/BarOS>foo</snmp>
            will be converted to <snmp>foo</snmp>

        """
        query = "descendant-or-self::*[namespace-uri()!='']"
        for element in tree.xpath(query):
            element.tag = etree.QName(element).localname
        return tree
