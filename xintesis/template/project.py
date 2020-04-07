__author__ = 'J41R0'

from jinja2 import Environment

project_template = """
# default imports
from flask import Blueprint, request, send_file
from flask_restplus import Api, Resource
from flask_jwt_extended import jwt_optional, decode_token
from jwt.exceptions import DecodeError as JWTDecodeError, ExpiredSignatureError

from xintesis import Project, ServicePack

# const definition
SUCC = 0
DATA = 1
TYPE = 2

project = Project("{{name}}")

# header
authorizations = {'api_key': {'type': 'apiKey', 'in': 'header', 'name': 'XSA-API-KEY'}}
project_api = Blueprint('{{name}}', __name__, url_prefix='/{{name}}/api')
{{name}}_api = Api(project_api, title='{{show_name}} Project', description='{{description}}', authorizations=authorizations)


{% if show_api %}
@{{name}}_api.default_namespace.hide{% endif %}
@{{name}}_api.default_namespace.route('/logs')
class Defalut(Resource):
    def get(self):
        \"\"\"Logged data\"\"\"
        return "Not implemented", 200

{% for current_component in components %}
# Package {{current_component.name}} {% if current_component.is_service %}
from projects.{{current_component.name}}.services import service_pack as {{current_component.name}}{% else %}
from packages.{{current_component.name}}.services import service_pack as {{current_component.name}}
{% endif %}
{{current_component.name}}_ns = {{name}}_api.namespace('{{current_component.name}}', description='{{current_component.desc}}')


class {{current_component.name.upper()}}_SERVICES:{% for curr_serv_pack in current_component.my_services.keys() %}{% if show_api %}
    @{{current_component.name}}_ns.hide{% endif %}
    @{{current_component.name}}_ns.route('/{{curr_serv_pack}}')
    @{{current_component.name}}_ns.header('XSA-API-KEY', 'JWT TOKEN', required=True)
    class {{curr_serv_pack}}(Resource):
        {% if current_component.my_services[curr_serv_pack].get["active"] %}{% if current_component.my_services[curr_serv_pack].get["expect"] and not current_component.my_services[curr_serv_pack].get["parser"] %}
        get_model = {{name}}_api.model('{{curr_serv_pack}} Get Model', {{current_component.name}}.my_services["{{curr_serv_pack}}"].get["expect"]){% endif %}{% if current_component.my_services[curr_serv_pack].get["marshall"] %}
        get_marshall = {{name}}_api.model('{{curr_serv_pack}} Get Response', {{current_component.name}}.my_services["{{curr_serv_pack}}"].get["marshall"]){% endif %}
        @jwt_optional
        {% if security and current_component.my_services[curr_serv_pack].get["security"] %}@{{name}}_api.doc(security='api_key')
        {% endif %}{% if current_component.my_services[curr_serv_pack].get["expect"] %}{% if current_component.my_services[curr_serv_pack].get["parser"] %}@{{name}}_api.expect({{current_component.name}}.my_services["{{curr_serv_pack}}"].get["expect"]){% else %}@{{name}}_api.expect(get_model){% endif %}
        {% endif %}{% if current_component.my_services[curr_serv_pack].get["marshall"] %}@{{name}}_api.marshal_with(get_marshall, code=200)
        {% endif %}@{{name}}_api.response(200, 'Success')
        @{{name}}_api.response(418, 'Process error'){% if security and current_component.my_services[curr_serv_pack].get["security"] %}
        @{{name}}_api.response(401, 'Unauthorized')
        @{{name}}_api.response(403, 'Forbidden'){% endif %}
        def get(self):
            \"\"\"{{current_component.my_services[curr_serv_pack].get["doc"]}}\"\"\"
            {% if security %}
            current_request_data = {
                "Host": request.headers['Host'] if 'Host' in request.headers else None,
                "User-Agent": request.headers['User-Agent'] if 'User-Agent' in request.headers else None,
                "Accept": request.headers['Accept'] if 'Accept' in request.headers else None,
                # "Accept-Language": request.headers[
                #    'Accept-Language'] if 'Accept-Language' in request.headers else None,
                # "Accept-Encoding": request.headers[
                #    'Accept-Encoding'] if 'Accept-Encoding' in request.headers else None,
                # "Referer": request.headers['Referer'] if 'Referer' in request.headers else None,
                # "Origin": request.headers['Origin'] if 'Origin' in request.headers else None,
                # "Connection": request.headers['Connection'] if 'Connection' in request.headers else None
            }
            tk_header = request.headers.get('XSA-API-KEY')
            if tk_header is None:
                return {"success": False, "message": "Login token required"}, 401
            try:
                identity = decode_token(tk_header).get('identity')
            except JWTDecodeError:
                return {"success": False, "message": "Incorrect login token"}, 401
            except ExpiredSignatureError:
                return {"success": False, "message": "Expired login token"}, 401
            if not identity:
                return {"success": False, "message": "Login token required"}, 401
            test = decode_token(tk_header)
            coincidences = set(identity.keys()).intersection(set(current_request_data.keys()))
            autentication_data_ok = True
            for curr_key in coincidences:
                if identity[curr_key] != current_request_data[curr_key]:
                    autentication_data_ok = False
                    break
            if not autentication_data_ok:
                return {"success": False, "message": "Unauthorized access"}, 401

            user = identity["user"]
            uri = "{{name}}/api/{{current_component.name}}/{{curr_serv_pack}}/GET"

            authorized = project.auth(user, uri)
            if not authorized:
                return {"success": False, "message": "You have not access to this resource"}, 401
            identity['uri'] = uri
            {% endif %}{% if current_component.my_services[curr_serv_pack].get["parser"] %}
            input = {{current_component.name}}.my_services["{{curr_serv_pack}}"].get["expect"].parse_args()
            {% else %}input = {{name}}_api.payload{% endif %}
            response = {"success": False, "data": "", "message": ""}
            try:
                obj_dict = project.get_object('{{current_component.name}}'){% if security and current_component.my_services[curr_serv_pack].get["security"] %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].get_call(project=project.file_handler, input=input, obj_dict=obj_dict, identity=identity){% else %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].get_call(project=project.file_handler, input=input, obj_dict=obj_dict){% endif %}
                code = 200
                succ = call[SUCC]
                data = call[DATA]
                res_type = None
                if len(call) > 2:
                    res_type = call[TYPE]
                response["success"] = succ
                # processing files
                if succ and res_type == "file":
                    name = str(data).split("/")[-1]
                    return send_file(data, as_attachment=True, attachment_filename=name)
                if succ:
                    response["data"] = data
                else:
                    response["message"] = data{% if security and current_component.my_services[curr_serv_pack].get["security"] %}
                    code = res_type if res_type in (401, 403) else 418{% else %}
                    code = 418{% endif %}
                return response, code
            except ServicePack.XtsServiceException as err:
                return err.response, err.resp_code
            except Exception as err:
                return {"success": False, "message": str(err)}, 418{% endif %}
{% if current_component.my_services[curr_serv_pack].post["active"] %}{% if current_component.my_services[curr_serv_pack].post["expect"] and not current_component.my_services[curr_serv_pack].post["parser"] %}
        post_model = {{name}}_api.model('{{curr_serv_pack}} Post Model', {{current_component.name}}.my_services["{{curr_serv_pack}}"].post["expect"]){% endif %}{% if current_component.my_services[curr_serv_pack].post["marshall"] %}
        post_marshall = {{name}}_api.model('{{curr_serv_pack}} Post Response', {{current_component.name}}.my_services["{{curr_serv_pack}}"].post["marshall"]){% endif %}
        @jwt_optional
        {% if security and current_component.my_services[curr_serv_pack].post["security"] %}@{{name}}_api.doc(security='api_key')
        {% endif %}{% if current_component.my_services[curr_serv_pack].post["expect"] %}{% if current_component.my_services[curr_serv_pack].post["parser"] %}@{{name}}_api.expect({{current_component.name}}.my_services["{{curr_serv_pack}}"].post["expect"]){% else %}@{{name}}_api.expect(post_model){% endif %}
        {% endif %}{% if current_component.my_services[curr_serv_pack].post["marshall"] %}@{{name}}_api.marshal_with(post_marshall, code=201)
        {% endif %}@{{name}}_api.response(201, 'Success')
        @{{name}}_api.response(418, 'Process error'){% if security and current_component.my_services[curr_serv_pack].post["security"] %}
        @{{name}}_api.response(401, 'Unauthorized')
        @{{name}}_api.response(403, 'Forbidden'){% endif %}
        def post(self):
            \"\"\"{{current_component.my_services[curr_serv_pack].post["doc"]}}\"\"\"
            {% if security %}
            current_request_data = {
                "Host": request.headers['Host'] if 'Host' in request.headers else None,
                "User-Agent": request.headers['User-Agent'] if 'User-Agent' in request.headers else None,
                "Accept": request.headers['Accept'] if 'Accept' in request.headers else None,
                # "Accept-Language": request.headers[
                #    'Accept-Language'] if 'Accept-Language' in request.headers else None,
                # "Accept-Encoding": request.headers[
                #    'Accept-Encoding'] if 'Accept-Encoding' in request.headers else None,
                # "Referer": request.headers['Referer'] if 'Referer' in request.headers else None,
                # "Origin": request.headers['Origin'] if 'Origin' in request.headers else None,
                # "Connection": request.headers['Connection'] if 'Connection' in request.headers else None
            }
            tk_header = request.headers.get('XSA-API-KEY')
            if tk_header is None:
                return {"success": False, "message": "Login token required"}, 401
            try:
                identity = decode_token(tk_header).get('identity')
            except JWTDecodeError:
                return {"success": False, "message": "Incorrect login token"}, 401
            except ExpiredSignatureError:
                return {"success": False, "message": "Expired login token"}, 401
            if not identity:
                return {"success": False, "message": "Login token required"}, 401
            test = decode_token(tk_header)
            coincidences = set(identity.keys()).intersection(set(current_request_data.keys()))
            autentication_data_ok = True
            for curr_key in coincidences:
                if identity[curr_key] != current_request_data[curr_key]:
                    autentication_data_ok = False
                    break
            if not autentication_data_ok:
                return {"success": False, "message": "Unauthorized access"}, 401

            user = identity["user"]
            uri = "{{name}}/api/{{current_component.name}}/{{curr_serv_pack}}/POST"

            authorized = project.auth(user, uri)
            if not authorized:
                return {"success": False, "message": "You have not access to this resource"}, 401
            identity['uri'] = uri
            {% endif %}{% if current_component.my_services[curr_serv_pack].post["parser"] %}
            input = {{current_component.name}}.my_services["{{curr_serv_pack}}"].post["expect"].parse_args()
            {% else %}input = {{name}}_api.payload{% endif %}
            response = {"success": False, "data": "", "message": ""}
            try:
                obj_dict = project.get_object('{{current_component.name}}'){% if security and current_component.my_services[curr_serv_pack].post["security"] %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].post_call(project=project.file_handler, input=input, obj_dict=obj_dict, identity=identity){% else %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].post_call(project=project.file_handler, input=input, obj_dict=obj_dict){% endif %}
                code = 201
                succ = call[SUCC]
                data = call[DATA]
                res_type = None
                if len(call) > 2:
                    res_type = call[TYPE]
                response["success"] = succ
                # processing files
                if succ and res_type == "file":
                    name = str(data).split("/")[-1]
                    return send_file(data, as_attachment=True, attachment_filename=name)
                if succ:
                    response["data"] = data
                else:
                    response["message"] = data{% if security and current_component.my_services[curr_serv_pack].get["security"] %}
                    code = res_type if res_type in (401, 403) else 418{% else %}
                    code = 418{% endif %}
                return response, code
            except ServicePack.XtsServiceException as err:
                return err.response, err.resp_code
            except Exception as err:
                return {"success": False, "message": str(err)}, 418{% endif %}
{% if current_component.my_services[curr_serv_pack].put["active"] %}{% if current_component.my_services[curr_serv_pack].put["expect"] and not current_component.my_services[curr_serv_pack].put["parser"] %}
        put_model = {{name}}_api.model('{{curr_serv_pack}} Put Model', {{current_component.name}}.my_services["{{curr_serv_pack}}"].put["expect"]){% endif %}{% if current_component.my_services[curr_serv_pack].put["marshall"] %}
        put_marshall = {{name}}_api.model('{{curr_serv_pack}} Put Response', {{current_component.name}}.my_services["{{curr_serv_pack}}"].put["marshall"]){% endif %}
        @jwt_optional
        {% if security and current_component.my_services[curr_serv_pack].put["security"] %}@{{name}}_api.doc(security='api_key')
        {% endif %}{% if current_component.my_services[curr_serv_pack].put["expect"] %}{% if current_component.my_services[curr_serv_pack].put["parser"] %}@{{name}}_api.expect({{current_component.name}}.my_services["{{curr_serv_pack}}"].put["expect"]){% else %}@{{name}}_api.expect(put_model){% endif %}
        {% endif %}{% if current_component.my_services[curr_serv_pack].put["marshall"] %}@{{name}}_api.marshal_with(put_marshall, code=201)
        {% endif %}@{{name}}_api.response(201, 'Success')
        @{{name}}_api.response(418, 'Process error'){% if security and current_component.my_services[curr_serv_pack].put["security"] %}
        @{{name}}_api.response(401, 'Unauthorized')
        @{{name}}_api.response(403, 'Forbidden'){% endif %}
        def put(self):
            \"\"\"{{current_component.my_services[curr_serv_pack].put["doc"]}}\"\"\"
            {% if security %}
            current_request_data = {
                "Host": request.headers['Host'] if 'Host' in request.headers else None,
                "User-Agent": request.headers['User-Agent'] if 'User-Agent' in request.headers else None,
                "Accept": request.headers['Accept'] if 'Accept' in request.headers else None,
                # "Accept-Language": request.headers[
                #    'Accept-Language'] if 'Accept-Language' in request.headers else None,
                # "Accept-Encoding": request.headers[
                #    'Accept-Encoding'] if 'Accept-Encoding' in request.headers else None,
                # "Referer": request.headers['Referer'] if 'Referer' in request.headers else None,
                # "Origin": request.headers['Origin'] if 'Origin' in request.headers else None,
                # "Connection": request.headers['Connection'] if 'Connection' in request.headers else None
            }
            tk_header = request.headers.get('XSA-API-KEY')
            if tk_header is None:
                return {"success": False, "message": "Login token required"}, 401
            try:
                identity = decode_token(tk_header).get('identity')
            except JWTDecodeError:
                return {"success": False, "message": "Incorrect login token"}, 401
            except ExpiredSignatureError:
                return {"success": False, "message": "Expired login token"}, 401
            if not identity:
                return {"success": False, "message": "Login token required"}, 401
            test = decode_token(tk_header)
            coincidences = set(identity.keys()).intersection(set(current_request_data.keys()))
            autentication_data_ok = True
            for curr_key in coincidences:
                if identity[curr_key] != current_request_data[curr_key]:
                    autentication_data_ok = False
                    break
            if not autentication_data_ok:
                return {"success": False, "message": "Unauthorized access"}, 401

            user = identity["user"]
            uri = "{{name}}/api/{{current_component.name}}/{{curr_serv_pack}}/PUT"

            authorized = project.auth(user, uri)
            if not authorized:
                return {"success": False, "message": "You have not access to this resource"}, 401
            identity['uri'] = uri
            {% endif %}{% if current_component.my_services[curr_serv_pack].put["parser"] %}
            input = {{current_component.name}}.my_services["{{curr_serv_pack}}"].put["expect"].parse_args()
            {% else %}input = {{name}}_api.payload{% endif %}
            response = {"success": False, "data": "", "message": ""}
            try:
                obj_dict = project.get_object('{{current_component.name}}'){% if security and current_component.my_services[curr_serv_pack].put["security"] %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].put_call(project=project.file_handler, input=input, obj_dict=obj_dict, identity=identity){% else %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].put_call(project=project.file_handler, input=input, obj_dict=obj_dict){% endif %}
                code = 201
                succ = call[SUCC]
                data = call[DATA]
                res_type = None
                if len(call) > 2:
                    res_type = call[TYPE]
                response["success"] = succ
                # processing files
                if succ and res_type == "file":
                    name = str(data).split("/")[-1]
                    return send_file(data, as_attachment=True, attachment_filename=name)
                if succ:
                    response["data"] = data
                else:
                    response["message"] = data{% if security and current_component.my_services[curr_serv_pack].get["security"] %}
                    code = res_type if res_type in (401, 403) else 418{% else %}
                    code = 418{% endif %}
                return response, code
            except ServicePack.XtsServiceException as err:
                return err.response, err.resp_code
            except Exception as err:
                return {"success": False, "message": str(err)}, 418{% endif %}
{% if current_component.my_services[curr_serv_pack].delete["active"] %}{% if current_component.my_services[curr_serv_pack].delete["expect"] and not current_component.my_services[curr_serv_pack].delete["parser"] %}
        delete_model = {{name}}_api.model('{{curr_serv_pack}} Delete Model', {{current_component.name}}.my_services["{{curr_serv_pack}}"].delete["expect"]){% endif %}{% if current_component.my_services[curr_serv_pack].delete["marshall"] %}
        delete_marshall = {{name}}_api.model('{{curr_serv_pack}} Delete Response', {{current_component.name}}.my_services["{{curr_serv_pack}}"].delete["marshall"]){% endif %}
        @jwt_optional
        {% if security and current_component.my_services[curr_serv_pack].delete["security"] %}@{{name}}_api.doc(security='api_key')
        {% endif %}{% if current_component.my_services[curr_serv_pack].delete["expect"] %}{% if current_component.my_services[curr_serv_pack].delete["parser"] %}@{{name}}_api.expect({{current_component.name}}.my_services["{{curr_serv_pack}}"].delete["expect"]){% else %}@{{name}}_api.expect(delete_model){% endif %}
        {% endif %}{% if current_component.my_services[curr_serv_pack].delete["marshall"] %}@{{name}}_api.marshal_with(delete_marshall, code=204)
        {% endif %}@{{name}}_api.response(204, 'Success')
        @{{name}}_api.response(418, 'Process error'){% if security and current_component.my_services[curr_serv_pack].delete["security"] %}
        @{{name}}_api.response(401, 'Unauthorized')
        @{{name}}_api.response(403, 'Forbidden'){% endif %}
        def delete(self):
            \"\"\"{{current_component.my_services[curr_serv_pack].delete["doc"]}}\"\"\"
            {% if security %}
            current_request_data = {
                "Host": request.headers['Host'] if 'Host' in request.headers else None,
                "User-Agent": request.headers['User-Agent'] if 'User-Agent' in request.headers else None,
                "Accept": request.headers['Accept'] if 'Accept' in request.headers else None,
                # "Accept-Language": request.headers[
                #    'Accept-Language'] if 'Accept-Language' in request.headers else None,
                # "Accept-Encoding": request.headers[
                #    'Accept-Encoding'] if 'Accept-Encoding' in request.headers else None,
                # "Referer": request.headers['Referer'] if 'Referer' in request.headers else None,
                # "Origin": request.headers['Origin'] if 'Origin' in request.headers else None,
                # "Connection": request.headers['Connection'] if 'Connection' in request.headers else None
            }
            tk_header = request.headers.get('XSA-API-KEY')
            if tk_header is None:
                return {"success": False, "message": "Login token required"}, 401
            try:
                identity = decode_token(tk_header).get('identity')
            except JWTDecodeError:
                return {"success": False, "message": "Incorrect login token"}, 401
            except ExpiredSignatureError:
                return {"success": False, "message": "Expired login token"}, 401
            if not identity:
                return {"success": False, "message": "Login token required"}, 401
            test = decode_token(tk_header)
            coincidences = set(identity.keys()).intersection(set(current_request_data.keys()))
            autentication_data_ok = True
            for curr_key in coincidences:
                if identity[curr_key] != current_request_data[curr_key]:
                    autentication_data_ok = False
                    break
            if not autentication_data_ok:
                return {"success": False, "message": "Unauthorized access"}, 401

            user = identity["user"]
            uri = "{{name}}/api/{{current_component.name}}/{{curr_serv_pack}}/DELETE"

            authorized = project.auth(user, uri)
            if not authorized:
                return {"success": False, "message": "You have not access to this resource"}, 401
            identity['uri'] = uri
            {% endif %}{% if current_component.my_services[curr_serv_pack].delete["parser"] %}
            input = {{current_component.name}}.my_services["{{curr_serv_pack}}"].delete["expect"].parse_args()
            {% else %}input = {{name}}_api.payload{% endif %}
            response = {"success": False, "data": "", "message": ""}
            try:
                obj_dict = project.get_object('{{current_component.name}}')
                obj_dict = project.get_object('{{current_component.name}}'){% if security and current_component.my_services[curr_serv_pack].delete["security"] %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].delete_call(project=project.file_handler, input=input, obj_dict=obj_dict, identity=identity){% else %}
                call = {{current_component.name}}.my_services["{{curr_serv_pack}}"].delete_call(project=project.file_handler, input=input, obj_dict=obj_dict){% endif %}
                code = 204
                succ = call[SUCC]
                data = call[DATA]
                res_type = None
                if len(call) > 2:
                    res_type = call[TYPE]
                response["success"] = succ
                if succ:
                    response["data"] = data
                else:
                    response["message"] = data{% if security and current_component.my_services[curr_serv_pack].get["security"] %}
                    code = res_type if res_type in (401, 403) else 418{% else %}
                    code = 418{% endif %}
                return response, code
            except ServicePack.XtsServiceException as err:
                return err.response, err.resp_code
            except Exception as err:
                return {"success": False, "message": str(err)}, 418{% endif %}{% endfor %}{% endfor %}
"""


def gen_project_src(name, id, hide_api, use_security, components_data_list, description=""):
    kwargs = dict()
    kwargs["show_name"] = name
    kwargs["name"] = id
    kwargs["show_api"] = hide_api
    # define condition to activate security
    kwargs["security"] = use_security
    # each component is a controller
    kwargs["components"] = components_data_list
    kwargs["description"] = description
    # print("----------------Generated-------------------")
    # __location__ = os.path.dirname(__file__)
    # project_template = open(os.path.join(__location__, "project.pyt"))
    source = Environment().from_string(project_template).render(**kwargs)
    # print(source)
    return source
