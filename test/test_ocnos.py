import unittest
import mock
from ncclient import NCClientError

from pyocnos.exceptions import OCNOSUnOpenedConnectionException
from pyocnos.exceptions import OCNOSConnectionException
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigException
from pyocnos.ocnos import OCNOS

connect_path = 'pyocnos.ocnos.manager.connect'


class TestOCNOS(unittest.TestCase):
    def setUp(self):
        self.device = OCNOS(
            hostname='hostname',
            username='username',
            password='password',
            timeout=100
        )

    @mock.patch(connect_path)
    def test_open(self, mock_manager_connect):
        self.device.open()
        mock_manager_connect.assert_called_with(
            host='hostname', port=830, username='username',
            password='password', timeout=100,
            look_for_keys=False
        )

    @mock.patch(connect_path)
    def test_open_when_ncclient_raises_exception(self, mock_manager_connect):
        mock_manager_connect.side_effect = NCClientError
        self.assertRaises(OCNOSConnectionException, self.device.open)

    @mock.patch(connect_path)
    def test_close(self, mock_manager_connect):
        self.device.open()
        close_session_mock = self.device._connection.close_session = mock.MagicMock()
        self.device.close()
        close_session_mock.assert_called_once()

    @mock.patch(connect_path)
    def test_close_when_ncclient_raises_exception(self, mock_manager_connect):
        self.device.open()
        self.device._connection.close_session.side_effect = NCClientError
        self.assertRaises(OCNOSConnectionException, self.device.close)

    def test_is_alive_when_open_not_called(self):
        self.assertFalse(self.device.is_alive())

    @mock.patch(connect_path)
    def test_is_alive_when_open_called(self, mock_manager_connect):
        self.device.open()
        self.device._connection.connected = True
        self.assertTrue(self.device.is_alive())

    def test_get_running_config(self):
        with mock.patch(connect_path) as mock_manager_connect:
            get_config_mock = mock_manager_connect. \
                return_value.get_config.return_value = mock.MagicMock()
            get_config_mock.data_xml = 'running_config'
            self.device.open()
            self.assertEquals(self.device.get_running_config(),
                              'running_config')

    def test_get_running_config_when_no_connection(self):
        self.assertRaises(OCNOSUnOpenedConnectionException,
                          self.device.get_running_config)

    def test_get_running_config_when_ncclinet_raises_exception(self):
        with mock.patch(connect_path) as mock_manager_connect:
            self.device.open()
            get_config_mock = mock_manager_connect. \
                return_value.get_config = mock.MagicMock()
            get_config_mock.side_effect = NCClientError
            self.assertRaises(OCNOSUnableToRetrieveConfigException,
                              self.device.get_running_config)
