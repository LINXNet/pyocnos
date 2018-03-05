#!/usr/bin/env python
""" Exceptions for pyocnos """


class OCNOSException(Exception):
    """ OcNOS Exception """
    pass


class OCNOSUnOpenedConnectionException(OCNOSException):
    """
    Exception class when no connection is open
    """

    def __init__(self):
        message = 'Please open a connection first using the open().'
        super(OCNOSUnOpenedConnectionException, self).__init__(message)


class OCNOSConnectionException(OCNOSException):
    """
    Exception class when couldn't open a connection
    """
    pass


class OCNOSUnableToRetrieveConfigException(OCNOSException):
    """
       Exception class when unable to retrieve running config
    """

    def __init__(self):
        message = 'Unable to retrieve running config.'
        super(OCNOSUnableToRetrieveConfigException, self).__init__(message)


class OCNOSNoCandidateConfigException(OCNOSException):
    """
       Exception class when unable to load candidate config
    """

    def __init__(self):
        message = "Please provide 'filename' or 'config' attribute"
        super(OCNOSNoCandidateConfigException, self).__init__(message)


class OCNOSLoadCandidateConfigFileReadException(OCNOSException):
    """
    Exception class when unable to read file give for config
    """

    def __init__(self):
        message = "Unable to read file"
        super(
            OCNOSLoadCandidateConfigFileReadException,
            self
        ).__init__(message)


class OCNOSCandidateConfigNotLoadedException(OCNOSException):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "No candidate config loaded use load_candidate_config func"
        super(
            OCNOSCandidateConfigNotLoadedException,
            self
        ).__init__(message)


class OCNOSCandidateConfigNotInServerCapabilitiesException(OCNOSException):
    """
    Exception class when no candidate config is loaded
    """

    def __init__(self):
        message = "Candidate config not in server capabilities"
        super(
            OCNOSCandidateConfigNotInServerCapabilitiesException,
            self
        ).__init__(message)
