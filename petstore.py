import falcon
import falcon.status_codes as status
from serve_swagger import SpecServer

def getPetById(**request_handler_args):
        resp = request_handler_args['resp']
        resp.status = falcon.HTTP_200
        resp.body = 'Got your pet! Good thing it was chippped....'

def findPetsByStatus(**request_handler_args):
        resp = request_handler_args['resp']
        resp.status = falcon.HTTP_200
        resp.body = 'Pet is found! Get a fence.......'

def deletePet(**request_handler_args):
        resp = request_handler_args['resp']
        resp.status = falcon.HTTP_204
        resp.body = 'Your pet is deleted! Very sad......'

def not_found(**request_handler_args):
    raise falcon.HTTPNotFound('Not found.', 'Requested resource not found.')

def forbidden(**request_handler_args):
    raise falcon.HTTPForbidden('Forbidden.', 'You are forbidden from accessing this.')

def im_a_teapot(**request_handler_args):
    resp = request_handler_args['resp']
    resp.status = status.HTTP_IM_A_TEAPOT

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

api = application = falcon.API()
server = SpecServer(operation_handlers=operation_handlers)
with open('petstore.json') as f:
    server.load_spec_swagger(f.read())
api.add_sink(server, r'/')

"""
to test:
gunicorn -b 127.0.0.1:8001 petstore:application
curl 127.0.0.1:8001/3.0/pet/findByStatus
curl 127.0.0.1:8001/3.0/pet/1
curl -X DELETE 127.0.0.1:8001/3.0/pet/1
"""