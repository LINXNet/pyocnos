#!/usr/bin/env python
""" Exceptions for pyocnos """

from ncclient.operations.rpc import RPCError


class OCNOSError(Exception):
    """ OcNOS Exception """
    def __init__(self, msg='', ncclient_exc=None):
        if ncclient_exc is not None and isinstance(ncclient_exc, RPCError):
            if hasattr(ncclient_exc, 'errors'):
                # Received multiple ncclient errors
                netconf_errors = ncclient_exc.errors
            else:
                netconf_errors = [ncclient_exc]
            netconf_msgs = []
            for error in netconf_errors:
                netconf_msgs.append(
                    'rpc-error:\n'
                    '    error-tag: {}\n'
                    '    error-path: {}\n'
                    '    error-message: {}\n'
                    '    error-info:\n'
                    '    {}'.format(
                        # The internal attributes in RPCError class for
                        # its properties, "tag", "path", etc. might be
                        # unavailable since they are all set at run time
                        # depending on rpc error.
                        getattr(error, '_tag', ''),
                        getattr(error, '_path', ''),
                        getattr(error, '_message', ''),
                        getattr(error, '_info', '')
                    )
                )

            error_msg = ('{}\n'
                         '{}'.format(
                             msg,
                             '\n'.join(netconf_msgs)
                         ))
        else:
            error_msg = msg

        super().__init__(error_msg)


class OCNOSUnOpenedConnectionError(OCNOSError):
    """
    Exception class when no connection is open
    """

    def __init__(self):
        message = 'Please open a connection first using the open().'
        super().__init__(message)


class OCNOSConnectionError(OCNOSError):
    """
    Exception class when couldn't open a connection
    """


class OCNOSBasicModeError(OCNOSError):
    """
    Exception class when failed to set basic mode to trim
    """


class OCNOSUnableToRetrieveConfigError(OCNOSError):
    """
       Exception class when unable to retrieve running config
    """


class OCNOSNoCandidateConfigError(OCNOSError):
    """
       Exception class when unable to load candidate config
    """

    def __init__(self):
        message = "Please provide 'filename' or 'config' attribute"
        super().__init__(message)


class OCNOSLoadCandidateConfigFileReadError(OCNOSError):
    """
    Exception class when unable to read file give for config
    """

    def __init__(self):
        message = "Unable to read file"
        super().__init__(message)


class OCNOSCandidateConfigNotLoadedError(OCNOSError):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "No candidate config loaded use load_candidate_config func"
        super().__init__(message)


class OCNOSCandidateConfigNotInServerCapabilitiesError(OCNOSError):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "Candidate config not in server capabilities"
        super().__init__(message)


class OCNOSCandidateConfigInvalidError(OCNOSError):
    """
    Exception class when candidate config is invalid
    """


class OCNOSCDuplicateKeyError(OCNOSError):
    """
    Exception class when config contains elements with the same key
    """
