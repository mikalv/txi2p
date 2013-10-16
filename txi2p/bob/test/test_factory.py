# Copyright (c) str4d <str4d@mail.i2p>
# See COPYING for details.

from twisted.internet import defer
from twisted.internet.error import ConnectionLost, ConnectionRefusedError
from twisted.python import failure
from twisted.test import proto_helpers
from twisted.trial import unittest

from txi2p.bob.factory import BOBI2PClientFactory, BOBI2PServerFactory

connectionLostFailure = failure.Failure(ConnectionLost())
connectionRefusedFailure = failure.Failure(ConnectionRefusedError())


class BOBFactoryTestMixin(object):
    def setUp(self):
        self.aborted = []

    def makeProto(self, *a, **kw):
        fac = self.factory(*a, **kw)
        proto = fac.buildProtocol(None)
        transport = proto_helpers.StringTransport()
        transport.abortConnection = lambda: self.aborted.append(True)
        proto.makeConnection(transport)
        return fac, proto

    def test_cancellation(self):
        fac, proto = self.makeProto(None, None, None, '')
        fac.deferred.cancel()
        self.assert_(self.aborted)
        return self.assertFailure(fac.deferred, defer.CancelledError)

    def test_cancellationBeforeFailure(self):
        fac, proto = self.makeProto(None, None, None, '')
        fac.deferred.cancel()
        proto.connectionLost(connectionLostFailure)
        self.assert_(self.aborted)
        return self.assertFailure(fac.deferred, defer.CancelledError)

    def test_cancellationAfterFailure(self):
        fac, proto = self.makeProto(None, None, None, '')
        proto.connectionLost(connectionLostFailure)
        fac.deferred.cancel()
        self.assertFalse(self.aborted)
        return self.assertFailure(fac.deferred, ConnectionLost)

    def test_clientConnectionFailed(self):
        fac, proto = self.makeProto(None, None, None, '')
        fac.clientConnectionFailed(None, connectionRefusedFailure)
        return self.assertFailure(fac.deferred, ConnectionRefusedError)

    def test_defaultFactoryListsTunnels(self):
        fac, proto = self.makeProto(None, None, None, '')
        proto.dataReceived('BOB 00.00.10\nOK\n')
        self.assertEqual(proto.transport.value(), 'list\n')


class TestBOBI2PClientFactory(BOBFactoryTestMixin, unittest.TestCase):
    factory = BOBI2PClientFactory


class TestBOBI2PServerFactory(BOBFactoryTestMixin, unittest.TestCase):
    factory = BOBI2PServerFactory
