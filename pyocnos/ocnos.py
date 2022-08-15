"""
Class to communicate with devices running OcNOS operating system
"""
import functools
import logging
# todo: Remove this once Ipinfusion have fix issue on as5812 switches for timeout
from time import sleep

from future.utils import raise_from
import lxml
from ncclient import manager
from ncclient import NCClientError

from pyocnos import LOGGER_NAME
from pyocnos.diff import build_xml_diff
from pyocnos.exceptions import OCNOSBasicModeError
from pyocnos.exceptions import OCNOSCandidateConfigInvalidError
from pyocnos.exceptions import OCNOSCandidateConfigNotInServerCapabilitiesError
from pyocnos.exceptions import OCNOSCandidateConfigNotLoadedError
from pyocnos.exceptions import OCNOSConnectionError
from pyocnos.exceptions import OCNOSLoadCandidateConfigFileReadError
from pyocnos.exceptions import OCNOSNoCandidateConfigError
from pyocnos.exceptions import OCNOSUnableToRetrieveConfigError
from pyocnos.exceptions import OCNOSUnOpenedConnectionError


class DefaultManager(manager.Manager):
    """
    Class extending ncclient default Manager class to prefer
    default netconf operations instead of vendor specific operations.
    """
    # pylint: disable=abstract-method
    def __getattr__(self, method):
        if method in manager.OPERATIONS:
            return functools.partial(self.execute, manager.OPERATIONS[method])
        return super().__getattr__(method)


class OCNOS:
    # pylint: disable=too-many-instance-attributes
    """ Class to instantiate a OcNOS device """

    def __init__(self, hostname, username, password, timeout=60, port=830):
        # pylint: disable=too-many-arguments
        """
        OCNOS device constructor.
        Args:
            hostname:   (str) IP or FQDN of the target device
            username:   (str) Username
            password:   (str) Password
            timeout:    (int) Timeout (default: 60 sec)
            port:       (int) Port (default: 830)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.timeout = timeout
        self.port = port

        self._connection = None
        self._candidate_config = None
        self.log = logging.getLogger(LOGGER_NAME)

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

        Returns:    None
        Raises:     OCNOSConnectionError
        """
        allow_agent = bool(self.password is None)

        # Because of the bug in ncclient it's not possible to connect to
        # multiple vendors from one python app (the vendor specific operations
        # are globally set and used by all connections)
        # OCNOS uses standard netconf operations, so using workaround with
        # DefaultManager class to temporarily fix the issue
        # ncclient github issue - https://github.com/ncclient/ncclient/issues/386
        try:
            built_in_manager = manager.connect(
                host=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=self.timeout,
                look_for_keys=False,
                allow_agent=allow_agent,
                hostkey_verify=False,
            )
            # pylint: disable=protected-access
            self._connection = DefaultManager(built_in_manager._session,
                                              built_in_manager._device_handler,
                                              built_in_manager._timeout)
            # todo: Remove this once Ipinfusion have fix issue on as5812 switches for timeout
            sleep(2)
        except NCClientError as ncclient_exception:
            self.log.error('Error', exc_info=True)
            raise_from(
                OCNOSConnectionError('Unable to open ssh connection.', ncclient_exception),
                ncclient_exception
            )
        else:
            self.log.info(
                "Connected to '%s' for user '%s'.",
                self.hostname,
                self.username
            )

        try:
            # Set basic mode to trim
            rpc_elem = lxml.etree.fromstring(
                b'<?xml version="1.0" encoding="UTF-8"?>'
                b'<set-default-handling-basic-mode '
                b'xmlns="http://ipinfusion.com/ns/zebmcli"><mode>'
                b'trim</mode></set-default-handling-basic-mode>'
            )
            self._connection.dispatch(rpc_elem)
        except NCClientError as ncclient_exception:
            self.log.error('Error', exc_info=True)
            raise_from(
                OCNOSBasicModeError('Unable to set basic mode to trim.', ncclient_exception),
                ncclient_exception
            )
        else:
            self.log.info(
                "Successfully set-default-handling-basic-mode to trim."
            )

    def close(self):
        """
        Close the SSH connection to the OcNOS running device.

        Returns: None
        Raises: OCNOSConnectionError
        """
        if self._connection:
            # If the netconf connection is closed in napalm __del__ method
            # (e.g. as in napalm_ansible) the underlying ssh transport can
            # be closed before the close_session method is called
            if not self._connection._session.transport.is_active():  # pylint: disable=protected-access
                raise OCNOSConnectionError(
                    'Unable to close ssh connection. The ssh transport is closed.'
                )
            try:
                self._connection.close_session()
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSConnectionError(
                        'Unable to close ssh connection.',
                        ncclient_exception
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

        Returns:    (bool) True if the SSH connection is still alive.
        """
        return self._connection.connected if self._connection else False

    def load_candidate_config(self, filename=None, config=None):
        """
        Load candidate_config from a string or file like object
        Args:
            filename:       Path to the file containing the desired
                            configuration. Default: None.
            config:         String containing the desired configuration.
                            Default: None.

        Returns:            None
        Raises:             OCNOSLoadCandidateConfigError,
                            OCNOSLoadCandidateConfigFileReadError
        """
        if filename is None and config is None:
            raise OCNOSNoCandidateConfigError
        if filename:
            try:
                self._candidate_config = lxml.etree.parse(
                    str(filename),
                    parser=lxml.etree.XMLParser(remove_blank_text=True)
                ).getroot()
            except IOError as io_error:
                raise_from(OCNOSLoadCandidateConfigFileReadError, io_error)
        else:
            # napalm_install_config passess config as string to the driver so
            # encoding that to bytes
            if isinstance(config, str):
                config = config.encode()
            # parsing from bytes, so it works with xml encoding declaration
            self._candidate_config = lxml.etree.fromstring(
                config,
                parser=lxml.etree.XMLParser(remove_blank_text=True))
        self._candidate_config.tag = 'config'
        self.log.info('candidate_config loaded')

    def commit_config(self, replace_config=False):
        """
        Commit the loaded candidate config

        Args:
            replace_config:     (bool) True if replacing the running config
                                with the candidate config. Merging the two
                                otherwise.

        Returns:                None
        Raises:                 OCNOSUnOpenedConnectionError
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

        # Select the default operation. Either replacing or merging the config
        if replace_config:
            self.log.info('Replace Running config with Candidate config')
            default_operation = 'replace'
        else:
            self.log.info('Merge Candidate config with Running config')
            default_operation = 'merge'

        with self._connection.locked(target='candidate'):
            self._connection.discard_changes()
            try:
                self._connection.edit_config(
                    target='candidate',
                    config=self._candidate_config,
                    error_option='rollback-on-error',
                    default_operation=default_operation
                )
                self._connection.commit()
            except NCClientError as ncclient_exception:
                self.log.error('error', exc_info=True)
                raise_from(
                    OCNOSCandidateConfigInvalidError('Failed to change the running config.', ncclient_exception),
                    ncclient_exception
                )
        self._connection.copy_config(source='running', target='startup')

    def compare_config(self):
        """
        Diff on the running and candidate config
        Returns:        List
        Raises:         OCNOSCandidateConfigNotLoadedError
                        OCNOSUnOpenedConnectionError

        """
        if self._candidate_config is None:
            self.log.error('Error: Candidate config not loaded')
            raise OCNOSCandidateConfigNotLoadedError

        if not self._connection:
            self.log.error('Error: no open connection', exc_info=True)
            raise OCNOSUnOpenedConnectionError

        return build_xml_diff(self._get_config_from_device('running'),
                              lxml.etree.tostring(self._candidate_config, encoding='UTF-8'))

    # pylint: disable=inconsistent-return-statements
    def _get_config_from_device(self, config_name):
        """
        Get config from device depending on config name
        Args:
            config_name:    (str) e.g. running or startup

        Returns:            (str) xml string representing the config
        Raises:             OCNOSUnOpenedConnectionError,
                            OCNOSUnableToRetrieveConfigError
        """
        if self._connection:
            try:
                config = self._connection.get_config(
                    source=config_name,
                    with_defaults='trim'
                ).data_xml
            except NCClientError as ncclient_exception:
                self.log.error('Error', exc_info=True)
                raise_from(
                    OCNOSUnableToRetrieveConfigError('Unable to retrieve running config.', ncclient_exception),
                    ncclient_exception
                )
            else:
                running_config = lxml.etree.fromstring(
                    config.encode(),
                    parser=lxml.etree.XMLParser(remove_blank_text=True))
                running_config.tag = 'config'
                return lxml.etree.tostring(running_config, encoding='UTF-8', pretty_print=True).decode()
        else:
            self.log.error('Error', exc_info=True)
            raise OCNOSUnOpenedConnectionError

    def get_config(self, retrieve='all'):
        """
        Get all or a specific config
        Args:
            retrieve:   (str) could be all or one of startup, running,
                        or candidate

        Returns:        (dict)

        """
        return {
            'startup': self._get_config_from_device('startup') if retrieve in ('startup', 'all') else '',
            'running': self._get_config_from_device('running') if retrieve in ('running', 'all') else '',
            'candidate': self._get_config_from_device('candidate') if retrieve in ('candidate', 'all') else ''
        }

    def discard_config(self):
        """
        Clear previously loaded candidate_config without committing it.

        Returns:    None
        """

        self._candidate_config = None
        self.log.info("candidate_config discarded")
