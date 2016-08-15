"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
import falcon
import json
import logging
from urllib.parse import parse_qs
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)
from falcon.routing import compile_uri_template

class SpecServer():

    # The Falcon web server has the concept of a "sink" in which all URI's that match a certain pattern
    # bypass the normal Falcon routing and instead are handed to the sink to process.
    # That's how this Mailman proxy works.
    # It is a sink which captures all inbound URI's and executes the correct auth function for that URI.
    # If the auth function returns True, the request is sent on to the Mailman REST API

    def __init__(self, operation_handlers, config=None):
        self.routing_table = {}
        self.config = config or {}
        self.routing_templates = []
        self.operation_handlers = operation_handlers
        log.info("SpecServer initialised")


    def __call__(self, req, resp, **kwargs):
        # this is the main entry point to inbound request processing
        log.info("SpecServer called")
        self.req = req
        self.resp = resp
        self.process_inbound_request()


    def process_inbound_request(self):
        # This is the meat of the application and steps through everything when a request comes in.

        if self.handle_preflight_request(): return # it would be good if we could just force a response return

        self.match_request_url_to_operation()

        #self.parse_form_data()

        self.dispatch_matched_operation_to_request_handlers()


    def load_spec_swagger(self, swagger_spec):
        # a Swagger spec (typically filenamed api-docs.json) defines a number of API "operations"
        # each operationId is (meant to be) unique and defines the operation's HTTP method & a URI template
        #
        # the routing table here is a dict that allows lookup of a Swagger operationId and its URI template
        # when an HTTP request comes in, we work out which Swagger operationId it maps to
        # this is done by doing a regular expression match of the inbound URL to each URI template until we
        # find the correct Swagger operationId

        # you can add multiple Swagger specs but be aware that a duplicate operationId will overwrite existing


        # this function sets up the routing table by parsing the Swagger spec JSON
        log.info("Loading swagger spec into routing table")
        # param swagger_spec is a JSON document
        try:
            swagger_spec = json.loads(swagger_spec)
        except:
            raise Exception("Unable to parse the Swagger spec JSON document.")
        try:
            for k in swagger_spec['paths'].keys():
                for http_method in swagger_spec['paths'][k].keys():
                    uri_fields, uri_template = compile_uri_template('/' + http_method.lower() + swagger_spec['basePath'] + k)
                    self.routing_templates.append(repr(uri_template))
                    operationId = swagger_spec['paths'][k][http_method]['operationId']
                    self.routing_table[operationId] = {'uri_fields': uri_fields, 'uri_template': uri_template}
                    if operationId not in self.operation_handlers.keys():
                        log.warning('In Swagger spec but not in operation_handlers: {}'.format(operationId))
        except:
            raise Exception("Unable to build routing table from provided Swagger spec.")

    def handle_preflight_request(self):
        # a request with the OPTIONS http method is a CORS pre-flight request, necessary to enable browser to send
        # custom authentication headers which we need for JWT token authentication and PUT, PATCH & DELETE methods
        if self.req.method == 'OPTIONS':
            log.info("Got an OPTIONS request: ".format(self.req.relative_uri))
            self.resp.set_header('Access-Control-Allow-Origin', '*')
            self.resp.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, PATCH, DELETE, OPTIONS')
            self.resp.set_header('Access-Control-Allow-Headers', 'X-Auth-Token, Keep-Alive, Users-Agent, X-Requested-With, If-Modified-Since, Cache-Control, Content-Type')
            self.resp.set_header('Access-Control-Max-Age', 1728000) # 20 days
            response_body = '\n'


            self.routing_templates.sort()

            response_body += 'All Swagger operations:\n\n'

            for route in sorted(self.routing_templates):
                response_body += repr(route) + '\n'
            response_body += '\n'

            for operation in sorted(self.routing_table.items()):
                response_body += repr(operation) + '\n'
            response_body += '\n'
            for operation in sorted(self.routing_table):
                response_body += operation + '\n'
            response_body += '\n'
            self.resp.body = response_body
            self.resp.status = falcon.HTTP_200
            return True

    def match_request_url_to_operation(self):
        # work out which Swagger operation has been requested by matching the inbound URL against
        # the URL template defined for each Swagger operation
        self.matched_operation = None
        self.uri_fields = None
        for operation, v in sorted(self.routing_table.items(), reverse=False):
            # a hack to get around the fact that we cant order the route evaluation
            # so we do it in reverse. ListsStylesGET conflicts with ListsVARGET
            # a more generalised server would require a way of ordering the route evaluation
            route_signature = '/' + self.req.method.lower() + self.req.relative_uri
            log.info("Trying to match route signature: {}".format(route_signature))
            m = v['uri_template'].match(route_signature)
            if m:
                log.info("Request URL matches route signature: {}".format(route_signature))
                # the regex groupdict function conveniently puts our URI template fieldnames and values in a dict
                self.uri_fields = m.groupdict()
                log.info("Request URL contained these template fields: {}".format(self.uri_fields))
                self.matched_operation = operation
                log.info("Matched operation: {} {}".format(self.matched_operation, v))
                break

        # the request URL does not match any of the routes from our Swagger specification, so return 404
        if self.matched_operation is None:
            log.info("Request URL does not match any route signature: {}".format(route_signature))
            raise falcon.HTTPNotFound()

        # the request URL matches an operation from our Swagger specification, but does not have request_handlers so return 404
        if self.matched_operation not in self.operation_handlers.keys():
            log.info("Operation found in spec but not in operation_handlers: {}".format(self.matched_operation))
            raise falcon.HTTPNotFound()


    def parse_form_data(self):
        # where content-type is 'application/x-www-form-urlencoded' we put form fields into a dict for convenience
        self.form_fields = None
        print('self.req.params')
        print(self.req.params)
        if self.req.method in ['POST', 'PATCH', 'PUT']:
            postdata = self.req.stream.read()
            print(postdata)
            #self.req.context['postdata'] = self.req.stream.read()
            #log.info("POST data in req.context: {}".format(postdata))
            #log.info("POST data in req.context: {}".format(self.req.context['postdata']))
            if self.req.get_header('content-type').lower() == 'application/x-www-form-urlencoded':
                self.form_fields = parse_qs(self.req.context['postdata'].decode('utf-8'))
            log.info("Form fields found: {}".format(self.form_fields))


    def dispatch_matched_operation_to_request_handlers(self):
        # ok finally we can execute the auth function for the Swagger operation
        log.info('Dispatching to: {}'.format(self.matched_operation))
        matched_operation_handlers = self.operation_handlers[self.matched_operation]
        request_handler_args = {
            'req': self.req,
            'resp': self.resp,
            'config': self.config,
            'uri_fields': self.uri_fields,
            'operation_id': self.matched_operation,
        }
        for item in matched_operation_handlers:

            ####### DO AUTHORIZATION REQUEST HANDLERS
            # if the item is a tuple then it contains one or more authorization functions
            # ONLY ONE AUTHORIZATION FUNCTION NEEDS TO RETURN TRUE FOR REQUEST TO BE AUTHORIZED!!!!!!!
            if isinstance(item, tuple):
                for authorization_function in item:
                    if authorization_function(**request_handler_args):
                        log.info("Successful execution of authorization handler: {}".format(authorization_function))
                        # we got a True back from the authorization function, request is authorized!
                        break
                else:
                    log.info("Failed execution of authorization handler: {}".format(authorization_function))
                    # no authorization functions return True so request is not authorized, abort with exception
                    raise falcon.HTTPUnauthorized('Unauthorized.', 'Request is not authorized.')
                continue # (outer for loop) to next handler function

            ####### DO REQUEST HANDLERS
            # if the item is a function then it's just a request handler - execute it
            log.info("Sending request to operation_request_handler: {}".format(item))
            item(**request_handler_args)

            ####### OUR JOB IS FINISHED - WHAT HAPPENS NEXT?
            # control returns to Falcon and Falcon returns the response object to the client

