from __future__ import unicode_literals

import hashlib
from collections import OrderedDict
from unittest import TestCase
from lxml import etree

from pyocnos.diff.block import Block


class TestBlock(TestCase):
    def test_success_get_name_when_running_and_candidate_present(self):
        running = self._get_element('vr', 'Interface', 'Interface text')
        candidate = self._get_element('vr', 'Interface', 'Interface new')

        block = Block(running, candidate)
        self.assertEqual('vr', block.get_name())

    def test_success_get_name_when_running_only_present(self):
        running = self._get_element('vr', 'Interface', 'Interface text')

        block = Block(running, None)
        self.assertEqual('vr', block.get_name())

    def test_success_get_name_when_candidate_only_present(self):
        candidate = self._get_element('vr', 'Interface', 'Interface new')

        block = Block(None, candidate)
        self.assertEqual('vr', block.get_name())

    def test_set_child_elements_for_diff_on_running(self):
        vr_element = etree.Element('vr')
        vr_id = etree.SubElement(vr_element, 'VrId')
        vr_id.text = '1'
        vrf = etree.SubElement(vr_element, 'vrf')
        vrf_name = etree.SubElement(vrf, 'vrfName')
        vrf_name.text = 'FOO_TWO'
        mac_vrf = etree.SubElement(vrf, 'macVrf')
        mac_vrf.text = 'true'

        block = Block(vr_element, None)
        expected = {
            'VrId': OrderedDict(
                {hashlib.sha224(etree.tostring(vr_id)).hexdigest(): vr_id}
            ),
            'vrf': OrderedDict(
                {hashlib.sha224(etree.tostring(vrf)).hexdigest(): vrf}
            )

        }
        self.assertEqual(
            expected,
            block.elements_for_diff_on_running
        )

    def test_child_elements_for_diff_on_candidate(self):
        element = etree.Element('vr')
        vr_id = etree.SubElement(element, 'VrId')
        vr_id.text = '1'
        vrf = etree.SubElement(element, 'vrf')
        vrf_name = etree.SubElement(vrf, 'vrfName')
        vrf_name.text = 'FOO_TWO'
        mac_vrf = etree.SubElement(vrf, 'macVrf')
        mac_vrf.text = 'true'

        block = Block(None, element)
        expected = {
            'vrf': OrderedDict({hashlib.sha224(etree.tostring(vrf)).hexdigest(): vrf}),
            'VrId': OrderedDict({hashlib.sha224(etree.tostring(vr_id)).hexdigest(): vr_id})
        }
        self.assertEqual(
            expected,
            block.elements_for_diff_on_candidate
        )

    def test_get_diff_when_candidate_is_none(self):
        running = self._get_element('vr', 'Interface', 'Interface text')

        block = Block(running, None)

        added_element = etree.Element('removed')
        added_element.append(running)
        expected = etree.tostring(added_element)
        self.assertEqual(expected, etree.tostring(block.get_diff()))

    def test_get_diff_when_running_is_none(self):
        candidate = self._get_element('vr', 'Interface', 'Interface text')

        block = Block(None, candidate)

        added_element = etree.Element('added')
        added_element.append(candidate)
        expected = etree.tostring(added_element)
        self.assertEqual(expected, etree.tostring(block.get_diff()))

    def test_get_diff_when_elements_same(self):
        running = self._get_element('vr', 'vrId', '1')
        candidate = self._get_element('vr', 'vrId', '1')

        block = Block(running, candidate)

        self.assertEqual(
            b'<vr><same><vrId>1</vrId></same></vr>',
            etree.tostring(block.get_diff())
        )

    def test_get_diff_when_elements_moved(self):
        running = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>2</vrId><vrId>1</vrId></vr>')

        block = Block(running, candidate)

        self.assertEqual(
            b'<vr><moved><vrId>1</vrId></moved><moved><vrId>2</vrId></moved></vr>',
            etree.tostring(block.get_diff())
        )

    def test_get_diff_when_root_have_no_children(self):
        running = etree.fromstring('<vr><vrId><name>1</name></vrId><vrId><name>3</name></vrId></vr>')
        candidate = etree.fromstring('<vr><vrId><name>2</name></vrId><vrId><name>4</name></vrId></vr>')

        block = Block(running, candidate)

        expected = (
            b'<vr><vrId><removed><name>1</name></removed><added><name>2</name></added></vrId>'
            b'<vrId><removed><name>3</name></removed><added><name>4</name></added></vrId></vr>'
        )
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_when_root_have_no_children_and_added_candidate(self):
        running = etree.fromstring('<vr><vrId>1</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')

        block = Block(running, candidate)
        expected = b'<vr><same><vrId>1</vrId></same><added><vrId>2</vrId></added></vr>'
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_when_root_have_no_children_and_removed_from_candidate(self):
        running = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId></vr>')

        block = Block(running, candidate)
        expected = b'<vr><same><vrId>1</vrId></same><removed><vrId>2</vrId></removed></vr>'
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_when_root_have_no_children_and_new_ele_in_candidate(self):
        running = etree.fromstring('<vr><vrId>1</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')

        block = Block(running, candidate)
        self.assertEqual(
            b'<vr><same><vrId>1</vrId></same><added><vrId>2</vrId></added></vr>',
            etree.tostring(block.get_diff())
        )

    def test_get_diff_when_text_changed(self):
        running = etree.fromstring('<logging_cli><logging>false</logging></logging_cli>')
        candidate = etree.fromstring('<logging_cli><logging>true</logging></logging_cli>')

        block = Block(running, candidate)
        expected = (
            b'<logging_cli><removed><logging>false</logging></removed>'
            b'<added><logging>true</logging></added></logging_cli>'
        )
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_when_text_changed_but_have_other_children(self):
        running = etree.fromstring('<nsmsnmp><enabled>false</enabled><vrfName>management</vrfName></nsmsnmp>')
        candidate = etree.fromstring('<nsmsnmp><enabled>true</enabled><vrfName>management</vrfName></nsmsnmp>')

        block = Block(running, candidate)
        expected = (
            b'<nsmsnmp>'
            b'<same><vrfName>management</vrfName></same>'
            b'<removed><enabled>false</enabled></removed>'
            b'<added><enabled>true</enabled></added>'
            b'</nsmsnmp>'
        )
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_with_multiple_children_changed(self):
        running_string = """
        <vr>
            <interface>
                <ifName>lo.management</ifName>
                <vrfName>management</vrfName>
                <ipAddr>127.0.0.1/9</ipAddr>
                <mtu>1501</mtu>
                <ipv6Addr>
                    <ipv6Addr>::1/128</ipv6Addr>
                </ipv6Addr>
            </interface>
        </vr>
        """
        candidate_string = """
        <vr>
            <interface>
                <ifName>lo.management</ifName>
                <vrfName>management</vrfName>
                <ipAddr>127.0.0.1/10</ipAddr>
                <mtu>1500</mtu>
                <ipv6Addr>
                    <ipv6Addr>::1/129</ipv6Addr>
                </ipv6Addr>
            </interface>
        </vr>
        """
        running = etree.fromstring(running_string)
        candidate = etree.fromstring(candidate_string)

        block = Block(running, candidate)
        expected = (
            b'<vr>'
            b'<interface>'
            b'<ipv6Addr>'
            b'<removed><ipv6Addr>::1/128</ipv6Addr></removed>'
            b'<added><ipv6Addr>::1/129</ipv6Addr></added>'
            b'</ipv6Addr>'
            b'<same><ifName>lo.management</ifName></same>'
            b'<same><vrfName>management</vrfName></same>'
            b'<removed><ipAddr>127.0.0.1/9</ipAddr></removed>'
            b'<added><ipAddr>127.0.0.1/10</ipAddr></added>'
            b'<removed><mtu>1501</mtu></removed>'
            b'<added><mtu>1500</mtu></added>'
            b'</interface>'
            b'</vr>'
        )

        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_when_candidate_has_deep_new_elements(self):
        running = etree.fromstring('<vr><vrId><mac>1</mac></vrId></vr>')
        candidate = etree.fromstring('<vr><vrId><mac>1</mac></vrId><vrId><mac>3</mac></vrId></vr>')

        block = Block(running, candidate)
        expected = b'<vr><same><vrId><mac>1</mac></vrId></same><added><vrId><mac>3</mac></vrId></added></vr>'
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_element_with_two_children_and_moved(self):
        running = etree.fromstring('<a><b><n>r1</n><c>true</c></b><b><n>r2</n><c>true</c></b></a>')
        candidate = etree.fromstring('<a><b><n>r2</n><c>true</c></b><b><n>r1</n><c>true</c></b></a>')

        block = Block(running, candidate)
        expected = b'<a><moved><b><n>r1</n><c>true</c></b></moved><moved><b><n>r2</n><c>true</c></b></moved></a>'
        actual = etree.tostring(block.get_diff())
        self.assertEqual(expected, actual)

    def test_get_diff_with_deep_children_and_formatted(self):
        running_string = """
        <vr>
            <vrId>0</vrId>
            <vrId>1</vrId>
            <vrId>2</vrId>
            <vrf>
                <vrfName>FOO_THREE</vrfName>
                <macVrf>true</macVrf>
            </vrf>
            <vrf>
                <vrfName>FOO_TWO</vrfName>
                <macVrf>true</macVrf>
            </vrf>
        </vr>"""
        candidate_string = """
        <vr>
            <vrId>0</vrId>
            <vrId>1</vrId>
            <vrf>
                <vrfName>FOO_TWO</vrfName>
                <macVrf>true</macVrf>
            </vrf>
            <vrf>
                <vrfName>FOO_THREE</vrfName>
                <macVrf>true</macVrf>
            </vrf>
        </vr>"""
        running = etree.fromstring(running_string)
        candidate = etree.fromstring(candidate_string)
        block = Block(running, candidate)
        actual = block.get_diff()

        self.assertEqual(actual.tag, 'vr')

        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<same><vrId>0</vrId></same>' in actual_as_string)
        self.assertTrue('<same><vrId>1</vrId></same>' in actual_as_string)
        self.assertTrue(
            '<moved><vrf><vrfName>FOO_THREE</vrfName><macVrf>true</macVrf></vrf></moved>' in actual_as_string
        )
        self.assertTrue('<moved><vrf><vrfName>FOO_TWO</vrfName><macVrf>true</macVrf></vrf></moved>' in actual_as_string)
        self.assertTrue('<removed><vrId>2</vrId></removed>' in actual_as_string)

    def test_get_printable_diff_for_moved_tags(self):
        running = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>2</vrId><vrId>1</vrId></vr>')

        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '! <vrId>1</vrId>',
            '! <vrId>2</vrId>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_diff_for_added_tags(self):
        running = etree.fromstring('<vr><vrId>1</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')

        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '+ <vrId>2</vrId>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_diff_for_removed_tags(self):
        running = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId></vr>')

        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '- <vrId>2</vrId>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_diff_for_removed_and_added_tags(self):
        running = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId><foo>1</foo></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId></vr>')

        block = Block(running, candidate)

        actual = block.get_printable_diff()

        self.assertTrue('[vr]' in actual)
        self.assertTrue('- <vrId>2</vrId>' in actual)
        self.assertTrue('- <foo>1</foo>' in actual)

    def test_get_printable_diff_for_same_removed_and_added_tags(self):
        running = etree.fromstring('<vr><vrId>1</vrId><vrId>2</vrId></vr>')
        candidate = etree.fromstring('<vr><vrId>1</vrId><vrId>3</vrId><vrId>4</vrId></vr>')

        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '- <vrId>2</vrId>',
            '+ <vrId>3</vrId>',
            '+ <vrId>4</vrId>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_diff_whole_block_removed(self):
        running = etree.fromstring('<vr>1234</vr>')

        block = Block(running, None)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '- <vr>1234</vr>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_diff_whole_block_added(self):
        candidate = etree.fromstring('<vr>1234</vr>')

        block = Block(None, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '+ <vr>1234</vr>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_with_deep_changes(self):
        running_str = """
        <vr>
            <interface>
                <ifName>po1</ifName>
                <loadInterval>30</loadInterval>
                <ipAddr>10.32.49.1/30</ipAddr>
                <description>to foo.net</description>
                <mtu>1600</mtu>
                <portChannelLoadBal>rtag7</portChannelLoadBal>
                <ospfInterface>
                    <ifNetworkType>point-to-points</ifNetworkType>
                    <ipOspfInterface>
                        <ifCostAddr>100000</ifCostAddr>
                    </ipOspfInterface>
                </ospfInterface>
            </interface>
        </vr>
        """
        candidate_str = """
        <vr>
            <interface>
                <ifName>po1</ifName>
                <loadInterval>30</loadInterval>
                <ipAddr>10.32.49.1/30</ipAddr>
                <description>to foo.net</description>
                <mtu>1600</mtu>
                <portChannelLoadBal>rtag7</portChannelLoadBal>
                <ospfInterface>
                    <ifNetworkType>point-to-point</ifNetworkType>
                    <ipOspfInterface>
                        <ifCostAddr>10000</ifCostAddr>
                    </ipOspfInterface>
                </ospfInterface>
            </interface>
        </vr>
        """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '  <interface>',
            '    <ospfInterface>',
            '      <ipOspfInterface>',
            '-       <ifCostAddr>100000</ifCostAddr>',
            '+       <ifCostAddr>10000</ifCostAddr>',
            '      </ipOspfInterface>',
            '-     <ifNetworkType>point-to-points</ifNetworkType>',
            '+     <ifNetworkType>point-to-point</ifNetworkType>',
            '    </ospfInterface>',
            '    <ifName>po1</ifName>',
            '    <loadInterval>30</loadInterval>',
            '    <ipAddr>10.32.49.1/30</ipAddr>',
            '    <description>to foo.net</description>',
            '    <mtu>1600</mtu>',
            '    <portChannelLoadBal>rtag7</portChannelLoadBal>',
            '  </interface>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_with_deep_collapse(self):
        running_str = """
        <vr>
            <interface>
                <ifName>po1</ifName>
                <loadInterval>30</loadInterval>
                <ipAddr>10.32.49.1/30</ipAddr>
                <description>to foo.net</description>
                <mtu>1600</mtu>
                <portChannelLoadBal>rtag8</portChannelLoadBal>
                <ospfInterface>
                    <ifNetworkType>point-to-point</ifNetworkType>
                    <ipOspfInterface>
                        <ifCostAddr>10000</ifCostAddr>
                    </ipOspfInterface>
                </ospfInterface>
            </interface>
        </vr>
        """
        candidate_str = """
        <vr>
            <interface>
                <ifName>po1</ifName>
                <loadInterval>30</loadInterval>
                <ipAddr>10.32.49.1/30</ipAddr>
                <description>to foo.net</description>
                <mtu>1600</mtu>
                <portChannelLoadBal>rtag7</portChannelLoadBal>
                <ospfInterface>
                    <ifNetworkType>point-to-point</ifNetworkType>
                    <ipOspfInterface>
                        <ifCostAddr>10000</ifCostAddr>
                    </ipOspfInterface>
                </ospfInterface>
            </interface>
        </vr>
        """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '  <interface>',
            '    <ospfInterface>...</ospfInterface>',
            '    <ifName>po1</ifName>',
            '    <loadInterval>30</loadInterval>',
            '    <ipAddr>10.32.49.1/30</ipAddr>',
            '    <description>to foo.net</description>',
            '    <mtu>1600</mtu>',
            '-   <portChannelLoadBal>rtag8</portChannelLoadBal>',
            '+   <portChannelLoadBal>rtag7</portChannelLoadBal>',
            '  </interface>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_with_deep_changes_and_added_on_candidate(self):
        running_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                   </switchportAllowedEthertypes>
               </interface>
           </vr>
           """
        candidate_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                       <arp>true</arp>
                   </switchportAllowedEthertypes>
               </interface>
           </vr>
           """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '  <interface>',
            '    <switchportAllowedEthertypes>',
            '      <ipv6>true</ipv6>',
            '      <ipv4>true</ipv4>',
            '+     <arp>true</arp>',
            '    </switchportAllowedEthertypes>',
            '  </interface>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_with_deep_changes_and_whole_tag_missing(self):
        running_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                   </switchportAllowedEthertypes>
               </interface>
               <interface>
                   <name>has</name>
               </interface>
           </vr>
           """
        candidate_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                       <arp>true</arp>
                   </switchportAllowedEthertypes>
               </interface>
           </vr>
           """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)

        actual = block.get_printable_diff()
        expected = [
            '[vr]',
            '  <interface>',
            '    <switchportAllowedEthertypes>',
            '      <ipv6>true</ipv6>',
            '      <ipv4>true</ipv4>',
            '+     <arp>true</arp>',
            '    </switchportAllowedEthertypes>',
            '  </interface>',
            '- <interface>',
            '-   <name>has</name>',
            '- </interface>',
        ]
        self.assertEqual(expected, actual)

    def test_get_diff_on_two_elements_when_candidate_is_none(self):
        actual = Block._get_diff_on_two_elements(
            etree.fromstring('<vrId><name>1</name></vrId>'),
            None
        )
        self.assertEqual('<removed><vrId><name>1</name></vrId></removed>', etree.tostring(actual[0]).decode('utf-8'))

    def test_get_diff_on_children_when_candidate_child_not_present(self):
        actual = Block._get_diff_on_children(
            etree.fromstring('<vrId><name>2</name><foo>text</foo></vrId>'),
            etree.fromstring('<vrId><name>2</name></vrId>')
        )
        self.assertEqual(actual.tag, 'vrId')
        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<same><name>2</name></same>' in actual_as_string)
        self.assertTrue('<removed><foo>text</foo></removed>' in actual_as_string)

    def test_get_diff_on_children_when_single_child_changed(self):
        actual = Block._get_diff_on_children(
            etree.fromstring('<vrId><name>2</name></vrId>'),
            etree.fromstring('<vrId><name>1</name></vrId>')
        )
        self.assertEqual(actual.tag, 'vrId')
        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<removed><name>2</name></removed>' in actual_as_string)
        self.assertTrue('<added><name>1</name></added>' in actual_as_string)

    def test_get_diff_on_children_when_sub_element_same(self):
        actual = Block._get_diff_on_children(
            etree.fromstring('<vrId><name>1</name></vrId>'),
            etree.fromstring('<vrId><name>1</name></vrId>')
        )
        self.assertEqual(actual.tag, 'vrId')
        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<same><name>1</name></same>' in actual_as_string, actual_as_string)

    def test_get_diff_on_children_when_many_sub_elements_changed(self):
        running_xml_str = (
            '<interface>'
            '<ifName>lo.management</ifName>'
            '<vrfName>management</vrfName>'
            '<ipAddr>127.0.0.1/9</ipAddr>'
            '<mtu>1501</mtu>'
            '<ipv6Addr><ipv6Addr>::1/128</ipv6Addr></ipv6Addr>'
            '</interface>'
        )
        actual = Block._get_diff_on_children(
            etree.fromstring(running_xml_str),
            etree.fromstring(running_xml_str.replace('127.0.0.1/9', '127.0.0.1/16').replace('::1/128', '::1/127'))
        )
        self.assertEqual(actual.tag, 'interface')
        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<same><ifName>lo.management</ifName></same>' in actual_as_string, actual_as_string)
        self.assertTrue('<same><vrfName>management</vrfName></same>' in actual_as_string, actual_as_string)

        self.assertTrue('<removed><ipAddr>127.0.0.1/9</ipAddr></removed>' in actual_as_string, actual_as_string)
        self.assertTrue('<added><ipAddr>127.0.0.1/16</ipAddr></added>' in actual_as_string, actual_as_string)

        self.assertTrue('<same><mtu>1501</mtu></same>' in actual_as_string, actual_as_string)

        self.assertTrue('<removed><ipv6Addr>::1/128</ipv6Addr></removed>' in actual_as_string, actual_as_string)
        self.assertTrue('<added><ipv6Addr>::1/127</ipv6Addr></added>' in actual_as_string, actual_as_string)

    def test_get_diff_on_children_when_candidate_has_extract_elements(self):
        actual = Block._get_diff_on_children(
            etree.fromstring('<vrId><name>2</name></vrId>'),
            etree.fromstring('<vrId><name>2</name><foo>text</foo></vrId>')
        )
        self.assertEqual(actual.tag, 'vrId')
        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<same><name>2</name></same>' in actual_as_string, actual_as_string)
        self.assertTrue('<added><foo>text</foo></added>' in actual_as_string, actual_as_string)

    def test_get_diff_on_children_when_running_has_extract_elements(self):
        actual = Block._get_diff_on_children(
            etree.fromstring('<vrfT><dns><ser>1233</ser><ser>1244</ser><ser>1245</ser></dns></vrfT>'),
            etree.fromstring('<vrfT><dns><ser>2</ser></dns></vrfT>'),

        )
        self.assertEqual(actual.tag, 'vrfT')
        actual_as_string = etree.tostring(actual).decode('utf-8')
        self.assertTrue('<removed><ser>1244</ser></removed>' in actual_as_string, actual_as_string)
        self.assertTrue('<removed><ser>1233</ser></removed>' in actual_as_string, actual_as_string)
        self.assertTrue('<added><ser>2</ser></added>' in actual_as_string, actual_as_string)

    def test_get_elements_for_diff(self):
        vr_element = etree.Element('vr')
        first_interface_str = """
              <interface>
                  <ifName>po1</ifName>
                  <samplingEnable>
                      <samplingEnable>true</samplingEnable>
                  </samplingEnable>
              </interface>
          """
        second_interface_str = """
              <interface>
                  <ifName>po3</ifName>
                  <samplingEnable>
                      <samplingEnable>true</samplingEnable>
                  </samplingEnable>
              </interface>
          """
        vr_element.append(etree.fromstring(first_interface_str))
        vr_element.append(etree.fromstring(second_interface_str))
        actual = Block._get_elements_for_diff(vr_element)
        self.assertEqual(2, len(actual['interface']))

    def test_format_element_with_symbols(self):
        actual = Block._format_element_with_symbols(b'<removed><vr>1234</vr></removed>')
        expected = '- <vr>1234</vr>'
        self.assertEqual(expected, actual)

    def test_surround_element_with_tag(self):
        element = etree.fromstring('<vrf><vrfName>COMPANY_ONE</vrfName><macVrf>true</macVrf></vrf>')
        tag = 'added'
        actual = Block._surround_element_with_tag(element=element, tag=tag)
        expected = '<{0}>{1}</{0}>'.format(tag, etree.tostring(element).decode('utf-8'))
        self.assertEqual(expected, etree.tostring(actual).decode('utf-8'))

    def test_collapse_element_with_no_children(self):
        actual = Block._collapse_element(element=etree.fromstring('<vrf>true</vrf>'), spaces=2)
        expected = '  <vrf>true</vrf>'
        self.assertEqual(expected, actual)

    def test_collapse_element_with_children(self):
        actual = Block._collapse_element(
            element=etree.fromstring('<vrf><vrfName>COMPANY_ONE</vrfName><macVrf>true</macVrf></vrf>'),
            spaces=2
        )
        expected = '  <vrf>...</vrf>'
        self.assertEqual(expected, actual)

    def test_append_symbol_with_element_with_no_child(self):
        actual = Block._append_symbol(
            element=etree.fromstring('<vrf>true</vrf>'),
            symbol='-',
            spaces=4
        )
        expected = ['-     <vrf>true</vrf>']
        self.assertEqual(expected, actual)

    def test_append_symbol_when_element_has_children_spaces_are_ignored(self):
        actual = Block._append_symbol(
            element=etree.fromstring('<vrf><vrfName>COMPANY_ONE</vrfName><macVrf>true</macVrf></vrf>'),
            symbol='+', spaces=8
        )
        expected = [
            '+ <vrf>',
            '+   <vrfName>COMPANY_ONE</vrfName>',
            '+   <macVrf>true</macVrf>',
            '+ </vrf>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_with_whole_tag_missing(self):
        self.maxDiff = None
        running_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                   </switchportAllowedEthertypes>
               </interface>
               <bgp>
                   <name>has</name>
               </bgp>
           </vr>
           """
        candidate_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                       <arp>true</arp>
                   </switchportAllowedEthertypes>
               </interface>
           </vr>
           """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)

        actual = block.get_printable_diff()
        self.assertTrue('[vr]' in actual)
        self.assertTrue('  <interface>' in actual)
        self.assertTrue('    <switchportAllowedEthertypes>' in actual)
        self.assertTrue('      <ipv6>true</ipv6>' in actual)
        self.assertTrue('      <ipv4>true</ipv4>' in actual)
        self.assertTrue('+     <arp>true</arp>' in actual)
        self.assertTrue('    </switchportAllowedEthertypes>' in actual)
        self.assertTrue('  </interface>' in actual)
        self.assertTrue('- <bgp>' in actual)
        self.assertTrue('-   <name>has</name>' in actual)
        self.assertTrue('- </bgp>' in actual)

    def test_when_whole_block_new_in_candidate(self):
        self.maxDiff = None
        running_str = """
           <vr>
                <bgp>
                    <bgpAs>65432</bgpAs>
                    <setLogNbrChanges>true</setLogNbrChanges>
                    <bgpAddressFamily>
                        <afi>l2vpn</afi>
                        <bgpSubAddressFamily>
                            <safi>evpn</safi>
                            <vrfAf>
                                <vrfName>default</vrfName>
                            </vrfAf>
                        </bgpSubAddressFamily>
                    </bgpAddressFamily>
                    <bgpPeer>
                        <peerAddr>10.0.2.129</peerAddr>
                        <peerActivate>true</peerActivate>
                        <sourceId>lo</sourceId>
                        <peerDesc>foo-bar</peerDesc>
                        <peerAs>65432</peerAs>
                        <bgpPeerAddressFamily>
                            <afi>l2vpn</afi>
                            <bgpPeerSubAddressFamily>
                                <safi>evpn</safi>
                                <peerActivateAf>true</peerActivateAf>
                            </bgpPeerSubAddressFamily>
                        </bgpPeerAddressFamily>
                    </bgpPeer>
                </bgp>
            </vr>
           """
        candidate_str = """
           <vr>
                <bgp>
                    <bgpAs>65432</bgpAs>
                    <setLogNbrChanges>true</setLogNbrChanges>
                    <bgpAddressFamily>
                        <afi>l2vpn</afi>
                        <bgpSubAddressFamily>
                            <safi>evpn</safi>
                            <vrfAf>
                                <vrfName>default</vrfName>
                            </vrfAf>
                        </bgpSubAddressFamily>
                    </bgpAddressFamily>
                    <bgpPeer>
                        <peerAddr>10.0.2.129</peerAddr>
                        <peerActivate>true</peerActivate>
                        <sourceId>lo</sourceId>
                        <peerDesc>foo-bar</peerDesc>
                        <peerAs>65432</peerAs>
                        <bgpPeerAddressFamily>
                            <afi>l2vpn</afi>
                            <bgpPeerSubAddressFamily>
                                <safi>evpn</safi>
                                <peerActivateAf>true</peerActivateAf>
                            </bgpPeerSubAddressFamily>
                        </bgpPeerAddressFamily>
                    </bgpPeer>
                    <bgpPeer>
                        <peerAddr>10.0.2.129</peerAddr>
                        <peerActivate>true</peerActivate>
                        <sourceId>lo</sourceId>
                        <peerDesc>foo-bar</peerDesc>
                        <peerAs>65432</peerAs>
                        <bgpPeerAddressFamily>
                            <afi>l2vpn</afi>
                            <bgpPeerSubAddressFamily>
                                <safi>evpn</safi>
                                <peerActivateAf>true</peerActivateAf>
                            </bgpPeerSubAddressFamily>
                        </bgpPeerAddressFamily>
                    </bgpPeer>
                </bgp>
            </vr>
           """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)
        actual = block.get_printable_diff()

        self.assertTrue('[vr]' in actual)
        self.assertTrue('  <bgp>' in actual)
        self.assertTrue('    <bgpAddressFamily>...</bgpAddressFamily>' in actual)
        self.assertTrue('    <bgpPeer>...</bgpPeer>' in actual)
        self.assertTrue('    <bgpAs>65432</bgpAs>' in actual)
        self.assertTrue('    <setLogNbrChanges>true</setLogNbrChanges>' in actual)
        self.assertTrue('+ <bgpPeer>' in actual)
        self.assertTrue('+   <peerAddr>10.0.2.129</peerAddr>' in actual)
        self.assertTrue('+   <peerActivate>true</peerActivate>' in actual)
        self.assertTrue('+   <sourceId>lo</sourceId>' in actual)
        self.assertTrue('+   <peerDesc>foo-bar</peerDesc>' in actual)
        self.assertTrue('+   <peerAs>65432</peerAs>' in actual)
        self.assertTrue('+   <bgpPeerAddressFamily>' in actual)
        self.assertTrue('+     <afi>l2vpn</afi>' in actual)
        self.assertTrue('+     <bgpPeerSubAddressFamily>' in actual)
        self.assertTrue('+       <safi>evpn</safi>' in actual)
        self.assertTrue('+       <peerActivateAf>true</peerActivateAf>' in actual)
        self.assertTrue('+     </bgpPeerSubAddressFamily>' in actual)
        self.assertTrue('+ </bgpPeer>' in actual)
        self.assertTrue('  </bgp>' in actual)

    def test_when_root_elements_change(self):
        self.maxDiff = None
        running_str = """
           <logginglevel>
                <name>foo</name>
                <logginglevel>5</logginglevel>
                <bar>1</bar>
           </logginglevel>
           """
        candidate_str = """
            <logginglevel>
                <name>foo</name>
                <logginglevel>2</logginglevel>
                <bar>1</bar>
            </logginglevel>
           """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)
        actual = block.get_printable_diff()
        expected = [
            '[logginglevel]',
            '  <name>foo</name>',
            '  <bar>1</bar>',
            '- <logginglevel>5</logginglevel>',
            '+ <logginglevel>2</logginglevel>'
        ]
        self.assertEqual(expected, actual)

    def test_get_printable_with_whole_tag_missing(self):
        self.maxDiff = None
        running_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                   </switchportAllowedEthertypes>
               </interface>
               <bgp>
                   <name>has</name>
               </bgp>
           </vr>
           """
        candidate_str = """
           <vr>
               <interface>
                   <switchportAllowedEthertypes>
                       <ipv6>true</ipv6>
                       <ipv4>true</ipv4>
                       <arp>true</arp>
                   </switchportAllowedEthertypes>
               </interface>
           </vr>
           """
        running = etree.fromstring(running_str)
        candidate = etree.fromstring(candidate_str)
        block = Block(running, candidate)

        actual = block.get_printable_diff()
        self.assertTrue('[vr]' in actual)
        self.assertTrue('  <interface>' in actual)
        self.assertTrue('    <switchportAllowedEthertypes>' in actual)
        self.assertTrue('      <ipv6>true</ipv6>' in actual)
        self.assertTrue('      <ipv4>true</ipv4>' in actual)
        self.assertTrue('+     <arp>true</arp>' in actual)
        self.assertTrue('    </switchportAllowedEthertypes>' in actual)
        self.assertTrue('  </interface>' in actual)
        self.assertTrue('- <bgp>' in actual)
        self.assertTrue('-   <name>has</name>' in actual)
        self.assertTrue('- </bgp>' in actual)

    @staticmethod
    def _get_element(tag, child_tag, child_text):
        element = etree.Element(tag)
        running_child_one = etree.SubElement(element, child_tag)
        running_child_one.text = child_text
        return element
