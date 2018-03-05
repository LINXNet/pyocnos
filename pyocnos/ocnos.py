"""
Class to communicate with devices running OcNOS operating system
"""
import logging
import lxml
from future.utils import raise_from
from ncclient import NCClientError
from ncclient import manager

from pyocnos.exceptions import OCNOSConnectionException
from pyocnos.exceptions import OCNOSNoCandidateConfigException
from pyocnos.exceptions import OCNOSLoadCandidateConfigFileReadException
from pyocnos.exceptions import OCNOSCandidateConfigNotLoadedException
from pyocnos.exceptions import \
    OCNOSCandidateConfigNotInServerCapabilitiesException
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigException
from pyocnos.exceptions import OCNOSUnOpenedConnectionException


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
        self._candidate_config = None
        self.log = logging.getLogger(__name__)

    def __enter__(self):
        """
        Context manager enter open connection
        Returns: OCNOS

        """
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        """
        Context manager enter exit connection
        Args:
            exc_type:
            exc_val:
            exc_tb:

        Returns: None

        """
        self.close()

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

    def load_candidate_config(self, filename=None, config=None):
        """
        Load candidate_config from a string or file like object
        Args:
            filename: Path to the file containing the desired
                          configuration. Default: None.
            config: String containing the desired configuration.
                          Default: None.

        Returns: None
        Raises: OCNOSLoadCandidateConfigException,
         OCNOSLoadCandidateConfigFileReadException

        """
        if filename is None and config is None:
            raise OCNOSNoCandidateConfigException
        elif filename:
            try:
                self._candidate_config = lxml.etree.parse(filename)
            except IOError as io_error:
                raise_from(OCNOSLoadCandidateConfigFileReadException, io_error)
        else:
            self._candidate_config = lxml.etree.fromstring(config)
        self.log.info("candidate_config loaded")

    def commit_config(self):
        """
        Commit the loaded candidate config
        Returns: None
        Raises: OCNOSUnOpenedConnectionException
            OCNOSCandidateConfigNotLoadedException
            OCNOSCandidateConfigNotInServerCapabilitiesException
        """
        if self._candidate_config is None:
            self.log.error('Error: Candidate config not loaded')
            raise OCNOSCandidateConfigNotLoadedException

        if not self._connection:
            self.log.error('Error: no open connection', exc_info=True)
            raise OCNOSUnOpenedConnectionException()

        if ':candidate' not in self._connection.server_capabilities:
            raise OCNOSCandidateConfigNotInServerCapabilitiesException

        # discard old candidate config
        # lock the current candidate config
        # edit it
        # commit will replace the running one with candidate

        self._connection.discard_changes()
        with self._connection.locked(target='candidate'):
            self._connection.edit_config(
                target='candidate',
                config=self._candidate_config,
                test_option='test-then-set',
                default_operation='replace'
            )
            self._connection.commit()
        self._connection.copy_config(source='running', target='startup')
