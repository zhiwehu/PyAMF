# -*- encoding: utf8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
# 
# Arnar Birgisson
# Thijs Triemstra
# Nick Joyce
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Flex Messaging implementation.

This module contains the message classes used with Flex Data Services.

@see: U{RemoteObject on OSFlash (external)
<http://osflash.org/documentation/amf3#remoteobject>}

@author: U{Arnar Birgisson<mailto:arnarbi@gmail.com>}
@author: U{Thijs Triemstra<mailto:info@collab.nl>}
@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import pyamf

__all__ = [
    'RemotingMessage',
    'CommandMessage',
    'AcknowledgeMessage',
    'ErrorMessage'
]

class AbstractMessage(object):
    """
    Abstract base class for all Flex messages.

    Messages have two customizable sections; headers and data. The headers
    property provides access to specialized meta information for a specific
    message instance. The data property contains the instance specific data
    that needs to be delivered and processed by the decoder.

    @see: U{AbstractMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AbstractMessage.html>}
    """

    #: Each message pushed from the server will contain this header identifying
    #: the client that will receive the message.
    DESTINATION_CLIENT_ID_HEADER = "DSDstClientId"
    #: Messages are tagged with the endpoint id for the channel they are sent over.
    ENDPOINT_HEADER = "DSEndpoint"
    #: Messages that need to set remote credentials for a destination carry the
    #: C{Base64} encoded credentials in this header.
    REMOTE_CREDENTIALS_HEADER = "DSRemoteCredentials"
    #: The request timeout value is set on outbound messages by services or channels and
    #: the value controls how long the responder will wait for an acknowledgement, result
    #: or fault response for the message before timing out the request.
    REQUEST_TIMEOUT_HEADER = "DSRequestTimeout"
    
    def __init__(self):
        #: Specific data that needs to be delivered to the remote destination.
        self.data = None
        #: The clientId indicates which client sent the message. 
        self.clientId = None
        #: The message destination.
        self.destination = None
        #: Message headers.
        #: 
        #: Core header names begin with a 'DS' prefix. Custom header names should start
        #: with a unique prefix to avoid name collisions.
        self.headers = []
        #: Unique message ID.
        self.messageId = None
        #: Indicates how long the message should be considered valid and deliverable.
        #:
        #: Time to live is the number of milliseconds that this message remains valid
        #: starting from the specified C{timestamp} value. For example, if the timestamp
        #: value is 04/05/05 1:30:45 PST and the timeToLive value is 5000, then this
        #: message will expire at 04/05/05 1:30:50 PST. Once a message expires it will
        #: not be delivered to any other clients.
        self.timeToLive = None
        #: Time stamp for the message.
        self.timestamp = None

    def __repr__(self):
        m = '<%s ' % self.__class__.__name__

        for k, v in self.__dict__.iteritems():
            m += ' %s=%s' % (k, v)

        return m + " />"

class AsyncMessage(AbstractMessage):
    """
    I am the base class for all asynchronous Flex messages.

    @see: U{AsyncMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AsyncMessage.html>}
    """

    #: Messages that were sent with a defined subtopic property indicate their target
    #: subtopic in this header.
    SUBTOPIC_HEADER = "DSSubtopic"
    
    def __init__(self):
        """
        """
        AbstractMessage.__init__(self)
        #: Correlation id of the message.
        self.correlationId = None

class AcknowledgeMessage(AsyncMessage):
    """
    I acknowledge the receipt of a message that was sent previously.

    Every message sent within the messaging system must receive an
    acknowledgement.

    @see: U{AcknowledgeMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/AcknowledgeMessage.html>}
    """
    #: Used to indicate that the acknowledgement is for a message that
    #: generated an error.
    ERROR_HINT_HEADER = "DSErrorHint"
    
    pass

class CommandMessage(AsyncMessage):
    """
    Provides a mechanism for sending commands related to publish/subscribe
    messaging, ping, and cluster operations.

    @see: U{CommandMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/CommandMessage.html>}
    """

    #: The server message type for authentication commands.
    AUTHENTICATION_MESSAGE_REF_TYPE = "flex.messaging.messages.AuthenticationMessage"
    #: This is used to test connectivity over the current channel
    #: to the remote endpoint.
    CLIENT_PING_OPERATION = 5
    #: This is used by a remote destination to sync missed or cached messages back
    #: to a client as a result of a client issued poll command.
    CLIENT_SYNC_OPERATION = 4
    #: This is used to request a list of failover endpoint URIs for the remote
    #: destination based on cluster membership.
    CLUSTER_REQUEST_OPERATION = 7
    #: This is used to send credentials to the endpoint so that the user can be
    #: logged in over the current channel. The credentials need to be C{Base64}
    #: encoded and stored in the body of the message.
    LOGIN_OPERATION = 8
    #: This is used to log the user out of the current channel, and will invalidate
    #: the server session if the channel is HTTP based.
    LOGOUT_OPERATION = 9
    #: This is used to poll a remote destination for pending, undelivered messages.
    POLL_OPERATION = 2
    #: Subscribe commands issued by a consumer pass the consumer's C{selector}
    #: expression in this header.
    SELECTOR_HEADER = "DSSelector"
    #: This is used to indicate that the client's session with a remote destination
    #: has timed out.
    SESSION_INVALIDATE_OPERATION = 10
    #: This is used to subscribe to a remote destination.
    SUBSCRIBE_OPERATION = 0
    #: This is the default operation for new L{CommandMessage} instances.
    UNKNOWN_OPERATION = 1000
    #: This is used to unsubscribe from a remote destination.
    UNSUBSCRIBE_OPERATION = 1
    
    def __init__(self):
        """
        """
        AsyncMessage.__init__(self)
        #: Operation/command.
        self.operation = None
        #: Remote destination belonging to a specific service, based upon
        #: whether this message type matches the message type the service
        #: handles.
        self.messageRefType = None

class ErrorMessage(AbstractMessage):
    """
    I am the Flex error message to be returned to the client.

    This class is used to report errors within the messaging system.

    @see: U{ErrorMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/ErrorMessage.html>}
    """

    #: If a message may not have been delivered, the faultCode will contain
    #: this constant.
    MESSAGE_DELIVERY_IN_DOUBT = "Client.Error.DeliveryInDoubt"
    #: Header name for the retryable hint header.
    #:
    #: This is used to indicate that the operation that generated the error may
    #: be retryable rather than fatal.
    RETRYABLE_HINT_HEADER = "DSRetryableErrorHint"
    
    def __init__(self):
        """
        """
        AbstractMessage.__init__(self)
        #: Extended data that the remote destination has chosen to associate with 
        #: this error to facilitate custom error processing on the client. 
        self.extendedData = {}   
        #: Fault code for the error. 
        self.faultCode = None
        #: Detailed description of what caused the error. 
        self.faultDetail = None
        #: A simple description of the error. 
        self.faultString = None
        #: Should a traceback exist for the error, this property contains the
        #: message.
        self.rootCause = {}

class RemotingMessage(AbstractMessage):
    """
    I am used to send RPC requests to a remote endpoint.

    @see: U{RemotingMessage on Livedocs (external)
    <http://livedocs.adobe.com/flex/201/langref/mx/messaging/messages/RemotingMessage.html>}
    """

    def __init__(self):
        """
        """
        AbstractMessage.__init__(self)
        #: Name of the remote method/operation that should be called.
        self.operation = None
        #: Name of the service to be called including package name.
        #: This property is provided for backwards compatibility.
        self.source = None

pyamf.register_class(RemotingMessage, 'flex.messaging.messages.RemotingMessage')
pyamf.register_class(ErrorMessage, 'flex.messaging.messages.ErrorMessage')
pyamf.register_class(CommandMessage, 'flex.messaging.messages.CommandMessage')
pyamf.register_class(AcknowledgeMessage,
    'flex.messaging.messages.AcknowledgeMessage')
