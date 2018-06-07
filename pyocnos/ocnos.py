"""
Class to communicate with devices running OcNOS operating system
"""
import logging
from time import sleep

import lxml
from future.utils import raise_from
from ncclient import NCClientError
from ncclient import manager

from pyocnos.diff.xml_diff import XmlDiff
from pyocnos.exceptions import OCNOSCandidateConfigInvalidError
from pyocnos.exceptions import OCNOSCandidateConfigNotInServerCapabilitiesError
from pyocnos.exceptions import OCNOSCandidateConfigNotLoadedError
from pyocnos.exceptions import OCNOSConnectionError
from pyocnos.exceptions import OCNOSLoadCandidateConfigFileReadError
from pyocnos.exceptions import OCNOSNoCandidateConfigError
from pyocnos.exceptions import OCNOSUnOpenedConnectionError
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigError


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
        Raises: OCNOSConnectionError
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
            # todo: Remove this once Ipinfusion have fix issue on as5812 switches for timeout
            sleep(2)
        except NCClientError as ncclient_exception:
            self.log.error('Error', exc_info=True)
            raise_from(
                OCNOSConnectionError('Unable to open ssh connection.'),
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
        Raises: OCNOSConnectionError

        """
        if self._connection:
            try:
                self._connection.close_session()
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSConnectionError(
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

    def load_candidate_config(self, filename=None, config=None):
        """
        Load candidate_config from a string or file like object
        Args:
            filename: Path to the file containing the desired
                          configuration. Default: None.
            config: String containing the desired configuration.
                          Default: None.

        Returns: None
        Raises: OCNOSLoadCandidateConfigError,
         OCNOSLoadCandidateConfigFileReadError

        """
        if filename is None and config is None:
            raise OCNOSNoCandidateConfigError
        elif filename:
            try:
                self._candidate_config = lxml.etree.parse(filename).getroot()
            except IOError as io_error:
                raise_from(OCNOSLoadCandidateConfigFileReadError, io_error)
        else:
            self._candidate_config = lxml.etree.fromstring(config)
        self._candidate_config.tag = 'config'
        self.log.info('candidate_config loaded')

    def commit_config(self):
        """
        Commit the loaded candidate config
        Returns: None
        Raises: OCNOSUnOpenedConnectionError
            OCNOSCandidateConfigNotLoadedError
            OCNOSCandidateConfigNotInServerCapabilitiesError
            OCNOSCandidateConfigInvalidError
        """
        if self._candidate_config is None:
            self.log.error('Error: Candidate config not loaded')
            raise OCNOSCandidateConfigNotLoadedError

        if not self._connection:
            self.log.error('Error: no open connection', exc_info=True)
            raise OCNOSUnOpenedConnectionError

        if ':candidate' not in self._connection.server_capabilities:
            raise OCNOSCandidateConfigNotInServerCapabilitiesError

        # discard old candidate config
        # lock the current candidate config
        # edit it
        # commit will replace the running one with candidate

        self._connection.discard_changes()
        with self._connection.locked(target='candidate'):
            try:
                self._connection.edit_config(
                    target='candidate',
                    config=self._candidate_config,
                    test_option='test-then-set',
                    default_operation='replace'
                )
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSCandidateConfigInvalidError,
                    ncclient_exception
                )
            self._connection.commit()
        self._connection.copy_config(source='running', target='startup')

    def compare_config(self):
        """
        Diff on the running and candidate config
        Returns: List
        Raises: OCNOSCandidateConfigNotLoadedError
            OCNOSUnOpenedConnectionError

        """
        if self._candidate_config is None:
            self.log.error('Error: Candidate config not loaded')
            raise OCNOSCandidateConfigNotLoadedError

        if not self._connection:
            self.log.error('Error: no open connection', exc_info=True)
            raise OCNOSUnOpenedConnectionError

        xml_diff = XmlDiff(self._get_config_from_device('running'), lxml.etree.tostring(self._candidate_config))
        return xml_diff.get_diff_string()

    def _get_config_from_device(self, config_name):
        """
        Get config from device depending on config name
        Args:
            config_name: (String) e.g. running or startup

        Returns: (String) xml string representing the config
        Raises: OCNOSUnOpenedConnectionError,
         OCNOSUnableToRetrieveConfigError

        """
        if self._connection:
            try:
                config = self._connection.get_config(source=config_name).data_xml
            except NCClientError as ncclient_exception:
                self.log.error('Error', exc_info=True)
                raise_from(
                    OCNOSUnableToRetrieveConfigError,
                    ncclient_exception
                )
            else:
                running_config = lxml.etree.fromstring(config.encode())
                running_config.tag = 'config'
                return lxml.etree.tostring(running_config, encoding='UTF-8', pretty_print=True)
        else:
            self.log.error('Error', exc_info=True)
            raise OCNOSUnOpenedConnectionError

    def get_config(self, retrieve='all'):
        """
        Get all or a specific config
        Args:
            retrieve: (String) could be all or one of startup, running,
              or candidate

        Returns: Dict

        """
        return {
            'startup': self._get_config_from_device('startup') if retrieve in ('startup', 'all') else '',
            'running': self._get_config_from_device('running') if retrieve in ('running', 'all') else '',
            'candidate': self._get_config_from_device('candidate') if retrieve in ('candidate', 'all') else ''
        }

    def discard_config(self):
        """
        Clear previously loaded candidate_config without committing it.

        Returns: None
        """

        self._candidate_config = None
        self.log.info("candidate_config discarded")
