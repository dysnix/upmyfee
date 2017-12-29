import json

import re
import urllib3
import decimal
import logging
from requests import Request, Session
from requests.auth import HTTPBasicAuth

try:
    import urllib.parse as urlparse
except ImportError:
    import urlparse

urllib3.disable_warnings()

USER_AGENT = "lepricoin"

HTTP_TIMEOUT = 30

log = logging.getLogger("BitcoinRPC")


class JSONRPCException(Exception):
    def __init__(self, rpc_error):
        parent_args = []
        try:
            parent_args.append(rpc_error['message'])
        except:
            pass
        Exception.__init__(self, *parent_args)
        self.error = rpc_error
        self.code = rpc_error['code'] if 'code' in rpc_error else None
        self.message = rpc_error['message'] if 'message' in rpc_error else None

    def __str__(self):
        return '%d: %s' % (self.code, self.message)

    def __repr__(self):
        return '<%s \'%s\'>' % (self.__class__.__name__, self)


def EncodeDecimal(o):
    if isinstance(o, decimal.Decimal):
        return float(round(o, 8))
    raise TypeError(repr(o) + " is not JSON serializable")


class AuthServiceProxy(object):
    __id_count = 0

    def __init__(self, service_url, service_name=None, timeout=HTTP_TIMEOUT, verify=True):
        schema, username, password, hostport = re.search(r'^(.*)://(.*):(.*)@(.*)$', service_url).groups()

        self.__service_url = service_url
        self.__service_name = service_name
        self.__verify = verify
        self.__timeout = timeout
        self.__session = Session()

        url = '{schema}://{hostport}'.format(schema=schema, hostport=hostport)
        self.__request = Request('POST', url, auth=HTTPBasicAuth(username, password), headers={'User-Agent': USER_AGENT,
                                                                                               'Content-type': 'application/json'})

    def __getattr__(self, name):
        if name.startswith('__') and name.endswith('__'):
            raise AttributeError
        if self.__service_name is not None:
            name = "%s.%s" % (self.__service_name, name)
        return AuthServiceProxy(self.__service_url, name, self.__timeout, self.__verify)

    def __call__(self, *args):
        AuthServiceProxy.__id_count += 1

        log.debug("-%s-> %s %s" % (AuthServiceProxy.__id_count, self.__service_name,
                                   json.dumps(args, default=EncodeDecimal)))
        postdata = json.dumps({'version': '1.1',
                               'method': self.__service_name,
                               'params': args,
                               'id': AuthServiceProxy.__id_count}, default=EncodeDecimal)

        self.__request.data = postdata

        prepped = self.__request.prepare()

        resp = self.__session.send(prepped, verify=self.__verify, timeout=self.__timeout)

        response = self._get_response(resp)
        if response.get('error') is not None:
            raise JSONRPCException(response['error'])
        elif 'result' not in response:
            raise JSONRPCException({
                'code': -343, 'message': 'missing JSON-RPC result'})

        return response['result']

    def _get_response(self, http_response):
        if http_response is None:
            raise JSONRPCException({
                'code': -342, 'message': 'missing HTTP response from server'})

        content_type = http_response.headers.get('Content-Type')
        if content_type != 'application/json':
            raise JSONRPCException({
                'code': -342, 'message': 'non-JSON HTTP response with \'%i\' from server: %s' % (
                    http_response.status_code, http_response.text)})

        response = http_response.json(parse_float=decimal.Decimal)
        if "error" in response and response["error"] is None:
            log.debug("<-%s- %s" % (response["id"], json.dumps(response["result"], default=EncodeDecimal)))
        else:
            log.debug("<-- " + http_response.content.decode('utf-8'))
        return response
