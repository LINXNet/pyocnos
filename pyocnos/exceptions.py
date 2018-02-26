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
