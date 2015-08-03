# serve_swagger
Use Swagger API JSON to create Falcon REST APIs.

This shows how you can use a Swagger JSON API document to create a REST API server in Python using Falcon.

It's easy!  Have a look at the petstore example to see how its done.

Each Swagger route must have a unique operation id.

In your Python code, import Falcon and serve_swagger as follows:

import falcon
import falcon.status_codes as status
from serve_swagger import SpecServer

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

finally, set up Falcon and the Swagger spec server, load in your Swagger JSON API spec document, like so:

```
api = application = falcon.API()
server = SpecServer(operation_handlers=operation_handlers)
with open('petstore.json') as f:
    server.load_spec_swagger(f.read())
api.add_sink(server, r'/')
```

Run it as follows:
gunicorn -b 127.0.0.1:8001 petstore:application

to test:
curl 127.0.0.1:8001/3.0/pet/findByStatus
curl 127.0.0.1:8001/3.0/pet/1
curl -X DELETE 127.0.0.1:8001/3.0/pet/1


