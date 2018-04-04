import os
import tempfile
import unittest

import lxml
import mock
from ncclient import NCClientError

from pyocnos.exceptions import OCNOSCandidateConfigInvalidError
from pyocnos.exceptions import OCNOSCandidateConfigNotInServerCapabilitiesError
from pyocnos.exceptions import OCNOSCandidateConfigNotLoadedError
from pyocnos.exceptions import OCNOSConnectionError
from pyocnos.exceptions import OCNOSLoadCandidateConfigFileReadError
from pyocnos.exceptions import OCNOSNoCandidateConfigError
from pyocnos.exceptions import OCNOSUnOpenedConnectionError
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigError
from pyocnos.ocnos import OCNOS

connect_path = 'pyocnos.ocnos.manager.connect'


class TestOCNOS(unittest.TestCase):
    def setUp(self):
        self.device = OCNOS(hostname='hostname', username='username', password='password', timeout=100)

    @mock.patch(connect_path)
    def test_open(self, mock_manager_connect):
        self.device.open()
        mock_manager_connect.assert_called_with(
            host='hostname', port=830, username='username',
            password='password', timeout=100,
            look_for_keys=False
        )

    @mock.patch(connect_path)
    def test_ocnos_class_in_context(self, mock_manager_connect):
        with OCNOS(hostname='hostname', username='username', password='password') as device:
            close_session_mock = device._connection.close_session = mock.MagicMock()
            device.is_alive()
        mock_manager_connect.assert_called_with(
            host='hostname', port=830, username='username',
            password='password', timeout=60,
            look_for_keys=False
        )
        close_session_mock.assert_called_once()

    @mock.patch(connect_path)
    def test_fail_open_when_ncclient_raises_exception(self, mock_manager_connect):
        mock_manager_connect.side_effect = NCClientError
        self.assertRaises(OCNOSConnectionError, self.device.open)

    @mock.patch(connect_path)
    def test_success_close(self, mock_manager_connect):
        self.device.open()
        close_session_mock = self.device._connection.close_session = mock.MagicMock()
        self.device.close()
        close_session_mock.assert_called_once()

    @mock.patch(connect_path)
    def test_fail_close_when_ncclient_raises_exception(self, mock_manager_connect):
        self.device.open()
        self.device._connection.close_session.side_effect = NCClientError
        self.assertRaises(OCNOSConnectionError, self.device.close)

    def test_is_alive_when_open_not_called(self):
        self.assertFalse(self.device.is_alive())

    @mock.patch(connect_path)
    def test_success_is_alive_when_connection_open(self, mock_manager_connect):
        self.device.open()
        self.device._connection.connected = True
        self.assertTrue(self.device.is_alive())

    def test_success_get_config_for_running(self):
        with mock.patch(connect_path) as mock_manager_connect:
            get_config_mock = mock_manager_connect.return_value.get_config.return_value = mock.MagicMock()
            get_config_mock.data_xml = '<vr>data</vr>'
            self.device.open()
            self.assertIsNotNone(self.device.get_config('running'))

    def test_fail_get_config_when_no_connection(self):
        self.assertRaises(OCNOSUnOpenedConnectionError, self.device.get_config)

    def test_fail_get_config_when_ncclinet_raises_exception(self):
        with mock.patch(connect_path) as mock_manager_connect:
            self.device.open()
            get_config_mock = mock_manager_connect.return_value.get_config = mock.MagicMock()
            get_config_mock.side_effect = NCClientError
            self.assertRaises(OCNOSUnableToRetrieveConfigError,
                              self.device.get_config)

    def test_fail_load_candidate_config_when_nor_string_or_file_given(self):
        self.assertRaises(OCNOSNoCandidateConfigError, self.device.load_candidate_config)

    def test_fail_load_candidate_config_when_unable_to_read_file(self):
        with self.assertRaises(OCNOSLoadCandidateConfigFileReadError):
            self.device.load_candidate_config(filename='foo.bar')

    def test_success_load_candidate_config_with_file(self):
        with tempfile.NamedTemporaryFile() as config_file:
            config_file.write(b'<config>foo</config>')
            config_file.seek(0)
            self.device.load_candidate_config(filename=config_file.name)
        self.assertEqual(
            b'<config>foo</config>',
            lxml.etree.tostring(self.device._candidate_config)
        )

    def test_success_load_candidate_config_a_string(self):
        self.device.load_candidate_config(config='<config>foo</config>')
        self.assertEqual(
            b'<config>foo</config>',
            lxml.etree.tostring(self.device._candidate_config)
        )

    def test_fail_commit_config_when_no_candidate_config_loaded(self):
        self.assertRaises(OCNOSCandidateConfigNotLoadedError, self.device.commit_config)

    def test_fail_commit_config_when_no_open_connection(self):
        self.device.load_candidate_config(config='<config>foo</config>')
        self.assertRaises(OCNOSUnOpenedConnectionError, self.device.commit_config)

    def test_fail_commit_config_when_candidate_not_in_server_capabilities(self):
        with mock.patch(connect_path) as mock_manager_connect:
            self.device.open()
            self.device.load_candidate_config(config='<config></config>')
            self.device._connection.server_capabilities = [':validate:1.0']
            self.assertRaises(OCNOSCandidateConfigNotInServerCapabilitiesError, self.device.commit_config)
            self.device.close()

    def test_fail_commit_config_when_ncclinet_raises_exception(self):
        config = '<config></config>'
        with mock.patch(connect_path) as mock_manager_connect:
            instance = mock_manager_connect.return_value
            instance.edit_config.side_effect = NCClientError
            self.device.open()
            self.device.load_candidate_config(config=config)
            self.device._connection.server_capabilities = [
                ':candidate',
                ':validate:1.0'
            ]
            self.assertRaises(OCNOSCandidateConfigInvalidError, self.device.commit_config)
            self.device.close()
        instance.discard_changes.assert_called_once()
        instance.locked.assert_called_with(target='candidate')

        instance.commit.assert_not_called()
        instance.copy_config.assert_not_called()

    def test_success_commit_config(self):
        config = '<config></config>'
        with mock.patch(connect_path) as mock_manager_connect:
            instance = mock_manager_connect.return_value
            self.device.open()
            self.device.load_candidate_config(config=config)
            self.device._connection.server_capabilities = [
                ':candidate',
                ':validate:1.0'
            ]
            self.device.commit_config()
            self.device.close()
        instance.discard_changes.assert_called_once()
        instance.locked.assert_called_with(target='candidate')
        instance.edit_config.assert_called_once_with(
            config=self.device._candidate_config,
            target='candidate',
            test_option='test-then-set',
            default_operation='replace'
        )
        instance.commit.assert_called_once_with()
        instance.copy_config.assert_called_once_with(
            target='startup',
            source='running'
        )

    def test_fail_compare_config_when_no_candidate_config_loaded(self):
        self.assertRaises(OCNOSCandidateConfigNotLoadedError, self.device.compare_config)

    def test_fail_compare_config_when_no_open_connection(self):
        self.device.load_candidate_config(config='<config>foo</config>')
        self.assertRaises(OCNOSUnOpenedConnectionError, self.device.compare_config)

    def test_success_compare_config(self):
        with mock.patch(connect_path) as mock_manager_connect:
            get_config_mock = mock_manager_connect.return_value.get_config.return_value = mock.MagicMock()
            get_config_mock.data_xml = '<data><vr><vrf>1</vrf></vr></data>'
            self.device.open()
            self.device.load_candidate_config(config='<config><vr><vrf>2</vrf></vr></config>')
            expected = ['[vr]', '- <vrf>1</vrf>', '+ <vrf>2</vrf>']
            self.assertEqual('{}'.format(os.linesep).join(expected), self.device.compare_config())

    def test_success_get_config_for_startup(self):
        with mock.patch(connect_path) as mock_manager_connect:
            get_config_mock = mock_manager_connect.return_value.get_config.return_value = mock.MagicMock()
            get_config_mock.data_xml = '<vr>1</vr>'
            self.device.open()

            config_element = lxml.etree.Element('config')
            config_element.text = '1'
            expected = lxml.etree.tostring(config_element, encoding='UTF-8', pretty_print=True)
            self.assertEqual(expected, self.device.get_config('startup')['startup'])

    def test_success_get_config_for_all_option(self):
        with mock.patch(connect_path) as mock_manager_connect:
            get_config_mock = mock_manager_connect.return_value.get_config.return_value = mock.MagicMock()
            get_config_mock.data_xml = '<data><vr>1</vr></data>'
            self.device.open()
            config_element = lxml.etree.Element('config')
            vr = lxml.etree.SubElement(config_element, 'vr')
            vr.text = '1'
            config_str = lxml.etree.tostring(config_element, encoding='UTF-8', pretty_print=True)
            expected = {
                'running': config_str,
                'startup': config_str,
                'candidate': config_str
            }
            self.assertEqual(
                expected,
                self.device.get_config()
            )

    def test_success_get_config_for_running(self):
        with mock.patch(connect_path) as mock_manager_connect:
            get_config_mock = mock_manager_connect.return_value.get_config.return_value = mock.MagicMock()
            get_config_mock.data_xml = '<data><vr>1</vr></data>'
            self.device.open()
            config_element = lxml.etree.Element('config')
            vr = lxml.etree.SubElement(config_element, 'vr')
            vr.text = '1'
            config_str = lxml.etree.tostring(config_element, encoding='UTF-8', pretty_print=True)
            expected = {
                'running': config_str,
                'startup': '',
                'candidate': ''
            }
            self.assertEqual(
                expected,
                self.device.get_config(retrieve='running')
            )

    def test_success_discard_config(self):
        self.device.load_candidate_config(config='<config>foo</config>')
        self.assertEqual(b'<config>foo</config>', lxml.etree.tostring(self.device._candidate_config))

        self.device.discard_config()
        self.assertIsNone(self.device._candidate_config)
