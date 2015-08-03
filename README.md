License: GPL
# serve_swagger
Use Swagger API JSON to create Falcon REST APIs.

This is intended just as a proof of concept/technology demo.  It is based on Swagger PetStore REST API.

A presentation was done on this topic at PyCon Brisbane 2015 - here is the presentation notes: https://github.com/crowdwave/serve_swagger/blob/master/PyConPresentation.pdf

You can browse the Swagger PetStore API at http://petstore.swagger.io/

This shows how you can use a Swagger JSON API document to create a REST API server in Python using Falcon.

It's easy!  Have a look at the petstore.py example to see how its done.

Each Swagger route must have a unique operation id.

In your Python code, import Falcon and serve_swagger as follows:

```
import falcon
import falcon.status_codes as status
from serve_swagger import SpecServer
```

create Python functions that you want to execute in response to incoming requests.
Make sure your function takes **request_handler_args as its argument.

Like so:

```
def deletePet(**request_handler_args):
        resp = request_handler_args['resp']
        resp.status = falcon.HTTP_204
        resp.body = 'Your pet is deleted! Very sad......'
```

create an operation_handlers dict that maps each swagger operation id to one of your functions.

```
operation_handlers = {
    'addPet':                       [not_found],
    'updatePet':                    [not_found],
    'findPetsByStatus':             [findPetsByStatus],
    'findPetsByTags':               [forbidden],
    'getPetById':                   [getPetById],
    'updatePetWithForm':            [forbidden],
    'deletePet':                    [deletePet],
    'uploadFile':                   [not_found],
    'getInventory':                 [not_found],
    'placeOrder':                   [forbidden],
    'getOrderById':                 [not_found],
    'deleteOrder':                  [im_a_teapot],
    'createUser':                   [forbidden],
    'createUsersWithArrayInput':    [not_found],
    'createUsersWithListInput':     [im_a_teapot],
    'loginUser':                    [not_found],
    'logoutUser':                   [not_found],
    'getUserByName':                [not_found],
    'updateUser':                   [not_found],
    'deleteUser':                   [not_found],
}
```

If you want to get fancy, you can push each request through multiple request handlers, like so:
```
operation_handlers = {
    'addPet': [authenticate_handler, refresh_cookie, add_some_header, addPet],
```

You can also push requests through authorization handlers. This is done by creating a tuple of request handlers that return True if the authorization succeeds. Note that only ONE authorization handler needs to return True for the authorization to succeed.
```
operation_handlers = {
    'addPet': [authenticate_handler, (requires_admin, requires_manager,), addPet],
```


finally, set up Falcon and the Swagger spec server, load in your Swagger JSON API spec document, like so:

```
api = application = falcon.API()
server = SpecServer(operation_handlers=operation_handlers)
with open('petstore.json') as f:
    server.load_spec_swagger(f.read())
api.add_sink(server, r'/')
```

Run it as follows:
```
gunicorn -b 127.0.0.1:8001 petstore:application
```

to test:
```
curl 127.0.0.1:8001/3.0/pet/findByStatus
curl 127.0.0.1:8001/3.0/pet/1
curl -X DELETE 127.0.0.1:8001/3.0/pet/1
```

Please note that this code is substantially extracted from the Mailman 3 authenticating proxy server which is found at https://gitlab.com/astuart/mailmania
