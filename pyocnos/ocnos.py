"""
Class to communicate with devices running OcNOS operating system
"""
import logging
from future.utils import raise_from
from ncclient import NCClientError
from ncclient import manager

from pyocnos.exceptions import OCNOSUnOpenedConnectionException
from pyocnos.exceptions import OCNOSConnectionException
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigException


class OCNOS(object):
    """
    Class to instantiate a OcNOS device
    """

    def __init__(self, hostname, username, password, timeout=60):
        """
        OCNOS device constructor.
        Args:
            hostname: (str) IP or FQDN of the target device
            username: (str) Username
            password: (str) Password
            timeout: (int) Timeout (default: 60 sec)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout

        self._connection = None
        self._running_config = None
        self.log = logging.getLogger(__name__)

    def open(self):
        """
        Open a connection to an OcNOS running device using SSH.

        Returns: None
        Raises: OCNOSConnectionException
        """

        try:
            self._connection = manager.connect(
                host=self.hostname,
                port=830,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False
            )
        except NCClientError as ncclient_exception:
            self.log.error('Error', exc_info=True)
            raise_from(
                OCNOSConnectionException('Unable to open ssh connection.'),
                ncclient_exception
            )
        else:
            self.log.info(
                "Connected to '%s' for user '%s'.",
                self.hostname,
                self.username
            )

    def close(self):
        """
        Close the SSH connection to the OcNOS running device.

        Returns: None
        Raises: OCNOSConnectionException

        """
        if self._connection:
            try:
                self._connection.close_session()
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSConnectionException(
                        'Unable to close ssh connection.'
                    ),
                    ncclient_exception
                )
            else:
                self.log.info(
                    "Connection closed to '%s' for user '%s'.",
                    self.hostname,
                    self.username
                )
                self._connection = None

    def is_alive(self):
        """
        Check if the SSH connection is still alive.

        Returns: Boolean

        """
        return self._connection.connected if self._connection else False

    def get_running_config(self):
        """
        Populate running_config from remote device.

        Returns: String
        Raises: OCNOSUnOpenedConnectionException,
         OCNOSUnableToRetrieveConfigException

        """
        if self._connection:
            try:
                return self._connection.get_config(source='running').data_xml
            except NCClientError as ncclient_exception:
                self.log.error('Error', exc_info=True)
                raise_from(
                    OCNOSUnableToRetrieveConfigException(),
                    ncclient_exception
                )
        else:
            self.log.error('Error', exc_info=True)
            raise OCNOSUnOpenedConnectionException()
