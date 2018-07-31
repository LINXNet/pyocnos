import os
from unittest import TestCase

from lxml.etree import XMLSyntaxError

from pyocnos.diff.xml_diff import XmlDiff

current_path = os.path.dirname(os.path.realpath(__file__))


class TestXmlDiff(TestCase):
    def test_fail_init_when_no_xml_passed(self):
        with self.assertRaises(XMLSyntaxError):
            XmlDiff('1', '2')

    def test_when_same_configs(self):
        running_config_str = """
            <data>
                <vr xmlns="http://www.company.com/TOOSchema/BarOS">
                    <vrId>0</vrId>
                    <vrId>1</vrId>
                    <vrId>2</vrId>
                    <vrf>
                        <vrfName>COMPANY_ONE</vrfName>
                        <macVrf>true</macVrf>
                    </vrf>
                    <interface>
                        <ifName>lo.management</ifName>
                        <vrfName>management</vrfName>
                        <ipAddr>127.0.0.1/10</ipAddr>
                        <mtu>1501</mtu>
                        <ipv6Addr>
                            <ipv6Addr>::1/127</ipv6Addr>
                        </ipv6Addr>
                    </interface>
                    <vrf>
                        <vrfName>COMPANY_TWO</vrfName>
                        <macVrf>true</macVrf>
                    </vrf>
                </vr>
                <mss>123</mss>
            </data>
        """

        xml_diff = XmlDiff(running_config_str, running_config_str)
        diff = xml_diff.get_printable_diff()
        self.assertListEqual([], diff)

    def test_success_simple(self):
        running_config_str = """
            <data>
                <vr xmlns="http://www.company.com/TOOSchema/BarOS">
                    <vrId>0</vrId>
                    <vrId>1</vrId>
                    <vrId>2</vrId>
                    <vrf>
                        <vrfName>COMPANY_ONE</vrfName>
                        <macVrf>true</macVrf>
                    </vrf>
                    <interface>
                        <ifName>lo.management</ifName>
                        <vrfName>management</vrfName>
                        <ipAddr>127.0.0.1/10</ipAddr>
                        <mtu>1501</mtu>
                        <ipv6Addr>
                            <ipv6Addr>::1/127</ipv6Addr>
                        </ipv6Addr>
                    </interface>
                    <vrf>
                        <vrfName>COMPANY_TWO</vrfName>
                        <macVrf>true</macVrf>
                    </vrf>
                </vr>
                <mss>123</mss>
            </data>
        """
        candidate_config_str = """
            <data>
                <vr xmlns="http://www.company.com/TOOSchema/BarOS">
                    <vrId>0</vrId>
                    <vrId>1</vrId>
                    <vrf>
                        <vrfName>COMPANY_TWO</vrfName>
                        <macVrf>true</macVrf>
                    </vrf>
                    <vrf>
                        <vrfName>COMPANY_ONE</vrfName>
                        <macVrf>true</macVrf>
                    </vrf>
                    <interface>
                        <ifName>lo.management</ifName>
                        <vrfName>management</vrfName>
                        <ipAddr>127.0.0.1/9</ipAddr>
                        <mtu>1500</mtu>
                        <ipv6Addr>
                            <ipv6Addr>::1/128</ipv6Addr>
                        </ipv6Addr>
                    </interface>
                </vr>
                <mss>123</mss>
                <bass>123</bass>
            </data>
        """

        xml_diff = XmlDiff(running_config_str, candidate_config_str)
        diff = xml_diff.get_printable_diff()
        expected = [
            '[vr]',
            '! <vrf>',
            '!   <vrfName>COMPANY_ONE</vrfName>',
            '!   <macVrf>true</macVrf>',
            '! </vrf>',
            '! <vrf>',
            '!   <vrfName>COMPANY_TWO</vrfName>',
            '!   <macVrf>true</macVrf>',
            '! </vrf>',
            '- <vrId>2</vrId>',
            '  <interface>',
            '    <ipv6Addr>',
            '-     <ipv6Addr>::1/127</ipv6Addr>',
            '+     <ipv6Addr>::1/128</ipv6Addr>',
            '    </ipv6Addr>',
            '    <ifName>lo.management</ifName>',
            '    <vrfName>management</vrfName>',
            '-   <ipAddr>127.0.0.1/10</ipAddr>',
            '+   <ipAddr>127.0.0.1/9</ipAddr>',
            '-   <mtu>1501</mtu>',
            '+   <mtu>1500</mtu>',
            '  </interface>',
            '[bass]',
            '+ <bass>123</bass>'
        ]

        self.assertEqual(sorted(expected), sorted(diff))

    def test_multiple_changes(self):
        self.maxDiff = None
        running_config_str = """
            <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <vr xmlns="http://www.company.com/TOOSchema/BarOS">
                    <interface>
                        <ifName>po1</ifName>
                        <loadInterval>30</loadInterval>
                        <ipAddr>10.32.49.1/30</ipAddr>
                        <description>to foo.bar.com</description>
                        <mtu>1600</mtu>
                        <portChannelLoadBal>rtag7</portChannelLoadBal>
                        <ospfInterface>
                            <ifNetworkType>point-to-point</ifNetworkType>
                            <ipOspfInterface>
                                <ifCostAddr>10000</ifCostAddr>
                            </ipOspfInterface>
                        </ospfInterface>
                        <samplingIngress>
                            <maxHeaderSizeIngress>20</maxHeaderSizeIngress>
                            <samplingRateIngress>16384</samplingRateIngress>
                        </samplingIngress>
                        <samplingEnable>
                            <samplingEnable>true</samplingEnable>
                        </samplingEnable>
                    </interface>
                </vr>
                <nsmsnmp xmlns="http://www.foo_conmpany.com/TOOSchema/BarOS">
                    <enabled>true</enabled>
                    <vrfName>management</vrfName>
                </nsmsnmp>
                <logging_cli xmlns="http://www.foo_company.com/TOOSchema/BarOS">
                    <logging>true</logging>
                </logging_cli>
            </data>
        """
        candidate_config_str = """
            <data xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
                <vr xmlns="http://www.foo_company.com/TOOSchema/BarOS">
                    <interface>
                        <ifName>po1</ifName>
                        <loadInterval>30</loadInterval>
                        <ipAddr>10.32.49.1/30</ipAddr>
                        <description>to foo.bar.com</description>
                        <mtu>1600</mtu>
                        <portChannelLoadBal>rtag7</portChannelLoadBal>
                        <ospfInterface>
                            <ifNetworkType>point-to-points</ifNetworkType>
                            <ipOspfInterface>
                                <ifCostAddr>100000</ifCostAddr>
                            </ipOspfInterface>
                        </ospfInterface>
                        <samplingIngress>
                            <maxHeaderSizeIngress>20</maxHeaderSizeIngress>
                            <samplingRateIngress>8192</samplingRateIngress>
                        </samplingIngress>
                        <samplingEnable>
                            <samplingEnable>true</samplingEnable>
                        </samplingEnable>
                    </interface>
                </vr>
                <nsmsnmp xmlns="http://www.foo_company.com/TOOSchema/BarOS">
                    <enabled>false</enabled>
                    <vrfName>management</vrfName>
                </nsmsnmp>
                <logging_cli xmlns="http://www.foo_company.com/TOOSchema/BarOS">
                    <logging>false</logging>
                </logging_cli>
            </data>
        """

        xml_diff = XmlDiff(running_config_str, candidate_config_str)
        actual = xml_diff.get_printable_diff()
        expected = [
            '[vr]',
            '  <interface>',
            '    <ospfInterface>',
            '      <ipOspfInterface>',
            '-       <ifCostAddr>10000</ifCostAddr>',
            '+       <ifCostAddr>100000</ifCostAddr>',
            '      </ipOspfInterface>',
            '-     <ifNetworkType>point-to-point</ifNetworkType>',
            '+     <ifNetworkType>point-to-points</ifNetworkType>',
            '    </ospfInterface>',
            '    <samplingIngress>',
            '      <maxHeaderSizeIngress>20</maxHeaderSizeIngress>',
            '-     <samplingRateIngress>16384</samplingRateIngress>',
            '+     <samplingRateIngress>8192</samplingRateIngress>',
            '    </samplingIngress>',
            '    <samplingEnable>...</samplingEnable>',
            '    <ifName>po1</ifName>',
            '    <loadInterval>30</loadInterval>',
            '    <ipAddr>10.32.49.1/30</ipAddr>',
            '    <description>to foo.bar.com</description>',
            '    <mtu>1600</mtu>',
            '    <portChannelLoadBal>rtag7</portChannelLoadBal>',
            '  </interface>',
            '[nsmsnmp]',
            '  <vrfName>management</vrfName>',
            '- <enabled>true</enabled>',
            '+ <enabled>false</enabled>',
            '[logging_cli]',
            '- <logging>true</logging>',
            '+ <logging>false</logging>'
        ]

        self.assertListEqual(expected, actual)

    def test_get_diff_string(self):
        running_config_str = """
            <data>
                <vr xmlns="http://www.company.com/TOOSchema/BarOS">
                    <vrId>0</vrId>
                </vr>
            </data>
        """
        candidate_config_str = """
            <data>
                <vr xmlns="http://www.company.com/TOOSchema/BarOS">
                    <vrId>2</vrId>
                </vr>
            </data>
        """

        xml_diff = XmlDiff(running_config_str, candidate_config_str)
        diff = xml_diff.get_diff_string()

        expected = '[vr]{0}- <vrId>0</vrId>{0}+ <vrId>2</vrId>'.format(os.linesep)
        self.assertEqual(expected, diff)
