# -*- encoding: utf-8 -*-
#
# Copyright (c) 2007 The PyAMF Project. All rights reserved.
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
General gateway tests.

@author: U{Nick Joyce<mailto:nick@boxdesign.co.uk>}

@since: 0.1.0
"""

import unittest

import pyamf
from pyamf import gateway, remoting

class TestService(object):
    def foo(self):
        return 'foo'

    def echo(self, x):
        return x

class FaultTestCase(unittest.TestCase):
    def test_create(self):
        x = gateway.Fault()

        self.assertEquals(x.code, None)
        self.assertEquals(x.detail, None)
        self.assertEquals(x.description, None)
        self.assertEquals(x.root_cause, None)

        x = gateway.Fault(code=404, detail='Not Found', root_cause=[],
            description='Foo bar')

        self.assertEquals(x.code, 404)
        self.assertEquals(x.detail, 'Not Found')
        self.assertEquals(x.description, 'Foo bar')
        self.assertEquals(x.root_cause, [])

    def test_build(self):
        fault = None

        try:
            raise TypeError, "unknown type"
        except TypeError, e:
            fault = gateway.build_fault()

        self.assertTrue(isinstance(fault, gateway.Fault))
        self.assertEquals(fault.code, 'TypeError')
        self.assertEquals(len(fault.root_cause), 1)

        tb = fault.root_cause[0]
        self.assertEquals(len(tb), 4)

        self.assertTrue(__file__.startswith(tb[0]))
        self.assertEquals(tb[1], 65)
        self.assertEquals(tb[2], 'test_build')
        self.assertEquals(tb[3], 'raise TypeError, "unknown type"')

    def test_encode(self):
        encoder = pyamf.get_encoder(pyamf.AMF0)
        decoder = pyamf.get_decoder(pyamf.AMF0)
        decoder.stream = encoder.stream

        try:
            raise TypeError, "unknown type"
        except TypeError, e:
            encoder.writeElement(gateway.build_fault())

        buffer = encoder.stream
        buffer.seek(0, 0)

        fault = decoder.readElement()
        old_fault = gateway.build_fault()

        self.assertEquals(fault.faultCode, old_fault.faultCode)
        self.assertEquals(fault.faultDetail, old_fault.faultDetail)
        self.assertEquals(fault.faultString, old_fault.faultString)

class ServiceWrapperTestCase(unittest.TestCase):
    def test_create(self):
        x = gateway.ServiceWrapper('blah')

        self.assertEquals(x.service, 'blah')
        self.assertEquals(x.authenticator, None)

        x = gateway.ServiceWrapper(ord, authenticator=chr)

        self.assertEquals(x.service, ord)
        self.assertEquals(x.authenticator, chr)

    def test_cmp(self):
        x = gateway.ServiceWrapper('blah')
        y = gateway.ServiceWrapper('blah')
        z = gateway.ServiceWrapper('bleh')

        self.assertEquals(x, y)
        self.assertNotEquals(y, z)

    def test_call(self):
        def add(x, y):
            self.assertEquals(x, 1)
            self.assertEquals(y, 2)

            return x + y

        x = gateway.ServiceWrapper(add)

        self.assertTrue(callable(x))
        self.assertEquals(x(None, [1, 2]), 3)

        x = gateway.ServiceWrapper('blah')

        self.assertRaises(TypeError, x, None, [])

        x = gateway.ServiceWrapper(TestService)

        self.assertRaises(TypeError, x, None, [])
        self.assertEquals(x('foo', []), 'foo')

        self.assertRaises(NameError, x, 'xyx', [])
        self.assertRaises(NameError, x, '_private', [])

        self.assertEquals(x('echo', [x]), x)

class ServiceRequestTestCase(unittest.TestCase):
    def test_create(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertEquals(x.request, request)
        self.assertEquals(x.service, sw)
        self.assertEquals(x.method, None)

    def test_authenticate(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertTrue(x.authenticate(None, None))

        def auth(u, p):
            if u == 'foo' and p == 'bar':
                return True

            return False

        sw = gateway.ServiceWrapper(TestService, authenticator=auth)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertFalse(x.authenticate(None, None))
        self.assertTrue(x.authenticate('foo', 'bar'))

    def test_call(self):
        sw = gateway.ServiceWrapper(TestService)
        request = remoting.Envelope()

        x = gateway.ServiceRequest(request, sw, None)

        self.assertRaises(TypeError, x)

        x = gateway.ServiceRequest(request, sw, 'foo')
        self.assertEquals(x(), 'foo')

        x = gateway.ServiceRequest(request, sw, 'echo')
        self.assertEquals(x(x), x)

class ServiceCollectionTestCase(unittest.TestCase):
    def test_contains(self):
        x = gateway.ServiceCollection()

        self.assertFalse(TestService in x)
        self.assertFalse('foo.bar' in x)

        x['foo.bar'] = gateway.ServiceWrapper(TestService)

        self.assertTrue(TestService in x)
        self.assertTrue('foo.bar' in x)

class BaseGatewayTestCase(unittest.TestCase):
    def test_create(self):
        x = gateway.BaseGateway()
        self.assertEquals(x.services, {})

        x = gateway.BaseGateway({})
        self.assertEquals(x.services, {})

        x = gateway.BaseGateway({})
        self.assertEquals(x.services, {})

        x = gateway.BaseGateway({'x': TestService})
        self.assertEquals(x.services, {'x': TestService})

        self.assertRaises(TypeError, gateway.BaseGateway, [])

    def test_add_service(self):
        gw = gateway.BaseGateway()
        self.assertEquals(gw.services, {})

        gw.addService(TestService)
        self.assertTrue(TestService in gw.services)
        self.assertTrue('TestService' in gw.services)

        del gw.services['TestService']

        gw.addService(TestService, 'foo.bar')
        self.assertTrue(TestService in gw.services)
        self.assertTrue('foo.bar' in gw.services)

        del gw.services['foo.bar']

        class FooService(object):
            def __str__(self):
                return 'foo'

            def __call__(*args, **kwargs):
                pass

        x = FooService()

        gw.addService(x)
        self.assertTrue(x in gw.services)
        self.assertTrue('foo' in gw.services)

        del gw.services['foo']

        self.assertEquals(gw.services, {})

    def test_remove_service(self):
        gw = gateway.BaseGateway({'test': TestService})
        self.assertTrue('test' in gw.services)
        wrapper = gw.services['test']

        gw.removeService('test')

        self.assertFalse('test' in gw.services)
        self.assertFalse(TestService in gw.services)
        self.assertFalse(wrapper in gw.services)
        self.assertEquals(gw.services, {})

        gw = gateway.BaseGateway({'test': TestService})
        self.assertTrue(TestService in gw.services)
        wrapper = gw.services['test']

        gw.removeService(TestService)

        self.assertFalse('test' in gw.services)
        self.assertFalse(TestService in gw.services)
        self.assertFalse(wrapper in gw.services)
        self.assertEquals(gw.services, {})

        gw = gateway.BaseGateway({'test': TestService})
        self.assertTrue(TestService in gw.services)
        wrapper = gw.services['test']

        gw.removeService(wrapper)

        self.assertFalse('test' in gw.services)
        self.assertFalse(TestService in gw.services)
        self.assertFalse(wrapper in gw.services)
        self.assertEquals(gw.services, {})

        self.assertRaises(NameError, gw.removeService, 'test')
        self.assertRaises(NameError, gw.removeService, TestService)
        self.assertRaises(NameError, gw.removeService, wrapper)

    def test_service_request(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        message = remoting.Message(envelope, 'foo', None, None)
        self.assertRaises(NameError, gw.getServiceRequest, message)

        message = remoting.Message(envelope, 'test.foo', None, None)
        sr = gw.getServiceRequest(message)

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, envelope)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, 'foo')

        message = remoting.Message(envelope, 'test', None, None)
        sr = gw.getServiceRequest(message)

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, envelope)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, None)

        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()
        message = remoting.Message(envelope, 'test', remoting.STATUS_OK, [])

        sr = gw.getServiceRequest(message)

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, envelope)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, None)

        # try to access an unknown service
        message = remoting.Message(envelope, 'foo', remoting.STATUS_OK, [])
        self.assertRaises(NameError, gw.getServiceRequest, message)

        # check x.x calls
        message = remoting.Message(envelope, 'test.test', remoting.STATUS_OK, [])
        sr = gw.getServiceRequest(message)

        self.assertTrue(isinstance(sr, gateway.ServiceRequest))
        self.assertEquals(sr.request, envelope)
        self.assertEquals(sr.service, TestService)
        self.assertEquals(sr.method, 'test')

    def test_get_response(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        self.assertRaises(NotImplementedError, gw.getResponse, envelope)

    def test_process_request(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()
        request = remoting.Message(envelope, 'test.foo', None, [])

        response = gw.processRequest(request)

        self.assertTrue(isinstance(response, remoting.Message))
        self.assertEquals(response.target, 'test.foo')
        self.assertEquals(response.status, remoting.STATUS_OK)
        self.assertEquals(response.body, 'foo')

        # Test a non existant service call
        request = remoting.Message(envelope, 'nope', None, [])
        response = gw.processRequest(request)

        self.assertTrue(isinstance(response, remoting.Message))
        self.assertEquals(response.target, 'nope')
        self.assertEquals(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, gateway.Fault))

        self.assertEquals(response.body.code, 'NameError')
        self.assertEquals(response.body.description, 'Unknown service nope')

    def test_malformed_credentials_header(self):
        gw = gateway.BaseGateway({'test': TestService})
        envelope = remoting.Envelope()

        request = remoting.Message(envelope, 'test.foo', None, [])
        request.headers['Credentials'] = {'foo': 'bar'}

        response = gw.processRequest(request)

        self.assertTrue(isinstance(response, remoting.Message))
        self.assertEquals(response.target, 'test.foo')
        self.assertEquals(response.status, remoting.STATUS_ERROR)
        self.assertTrue(isinstance(response.body, gateway.Fault))

        self.assertEquals(response.body.code, 'RemotingError')
        self.assertEquals(response.body.description,
            'Invalid credentials object')

def suite():
    suite = unittest.TestSuite()

    # basics first
    suite.addTest(unittest.makeSuite(FaultTestCase))
    suite.addTest(unittest.makeSuite(ServiceWrapperTestCase))
    suite.addTest(unittest.makeSuite(ServiceRequestTestCase))
    suite.addTest(unittest.makeSuite(ServiceCollectionTestCase))
    suite.addTest(unittest.makeSuite(BaseGatewayTestCase))

    try:
        import wsgiref
    except ImportError:
        wsgiref = None

    if wsgiref:
        from pyamf.tests.gateway import test_wsgi

        suite.addTest(test_wsgi.suite())

    try:
        import twisted
    except ImportError:
        twisted = None

    if twisted:
        from pyamf.tests.gateway import test_twisted

        #suite.addTest(test_twisted.suite())

    try:
        import django
    except ImportError:
        django = None

    if django:
        from pyamf.tests.gateway import test_django

        suite.addTest(test_django.suite())

    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
