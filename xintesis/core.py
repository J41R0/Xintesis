__author__ = 'J41R0'

import os
import shutil
import inspect
import logging
from importlib import import_module

from flask_restplus import fields, reqparse
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

import xintesis
from xintesis import manager

pack_dir = ""
mod_dir = ""


def init():
    pack_dir = os.path.join(xintesis.PROJECT_PATH, 'packages')
    mod_dir = os.path.join(xintesis.PROJECT_PATH, 'modules')
    manager.server_modules = os.listdir(mod_dir)
    manager.server_packages = os.listdir(pack_dir)


class StaticMethod(object):
    """
    Class for recreate static method call
    """

    def __init__(self, func):
        self.func = func
        self.__name__ = func.__name__

    def __get__(self, obj, cls):
        return self.func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


class ProjectFile:
    def __init__(self, project_name):
        self.model_path = os.path.join(xintesis.PROJECT_PATH, "model/" + project_name)
        self.log = None

    def set_logger(self, logger):
        self.log = logger

    def save_file(self, path, file_data):
        try:
            if type(file_data) == FileStorage:
                file_data.save(self.model_path + "/" + path + "/" + secure_filename(file_data.filename))
            else:
                file = open(self.model_path + "/" + path, 'w')
                file.write(file_data)
                file.close()
            return True
        except Exception as err:
            self.log.debug(str(err))
        return False

    def get_file(self, path):
        try:
            file = open(self.model_path + "/" + path, 'r')
            file_data = file.read()
            file.close()
            return file_data
        except Exception as err:
            self.log.debug(str(err))

    def lsdir(self, path="", only_dir=False):
        try:
            if path == "":
                if only_dir:
                    return [x for x in os.listdir(self.model_path) if os.path.isdir(self.model_path + "/" + x)]
                else:
                    return list(os.listdir(self.model_path))
            else:
                temp_path = self.model_path + "/" + path
                if only_dir:
                    return [x for x in os.listdir(temp_path) if os.path.isdir(temp_path + "/" + x)]
                else:
                    return list(os.listdir(temp_path))

        except Exception as err:
            self.log.debug(str(err))

    def walk_dir(self):
        try:
            return [x[0] for x in os.walk(self.model_path)]
        except Exception as err:
            self.log.debug(str(err))

    def mkdir(self, dir_name):
        try:
            os.mkdir(self.model_path + "/" + dir_name)
            return True
        except Exception as err:
            self.log.debug(str(err))

    def rm_data(self, path):
        try:
            if os.path.isfile(self.model_path + "/" + path):
                os.remove(self.model_path + "/" + path)
            else:
                shutil.rmtree(self.model_path + "/" + path)
            return True
        except Exception as err:
            self.log.debug(str(err))

    def exist(self, path):
        try:
            return os.path.exists(self.model_path + "/" + path)
        except Exception as err:
            self.log.debug(str(err))

    def renamedir(self, path, new_path):
        try:
            return os.rename(self.model_path + "/" + path, self.model_path + "/" + new_path)
        except Exception as err:
            self.log.debug(str(err))


class Project:
    def __init__(self, name):
        self.name = name
        # required None init
        self.log = None
        self.__log_handler = None
        self.file_handler = ProjectFile(self.name)
        self.__objects = dict()
        self.__shared_obj = dict()
        self.uri_list = list()
        # authorization function reference
        self.__auth_function = None
        # login function reference
        self.__login_function = None
        # project configuration data
        self.config = None

    def init_objects(self, security_cfg):
        try:
            module_ini_obj = import_module('projects.' + self.name)
            load_cfg = self.config.copy()
            load_cfg['uris'] = self.uri_list.copy()
            self.__objects[self.name] = module_ini_obj.init_objects(load_cfg)
            if security_cfg['use_security']:
                try:
                    auth_id = module_ini_obj.AUTH
                    self.set_auth(self.__objects[self.name][auth_id])
                except:
                    logging.error("No authorization function defined in project " + self.name)
                try:
                    login_id = module_ini_obj.LOGIN
                    self.set_login(self.__objects[self.name][login_id])
                except:
                    logging.error("No login function defined in project " + self.name)
        except:
            logging.error("Cannot init project " + self.name + " objects due error importing 'init_objects' function")

    def set_auth(self, auth_function):
        self.__auth_function = auth_function

    def set_login(self, login_function):
        self.__login_function = login_function

    def auth(self, user, uri):
        if self.__auth_function is not None:
            return self.__auth_function(user, uri)
        return False

    def login(self, username, password):
        if self.__auth_function is not None:
            return self.__login_function(username, password)
        return False

    def set_uris(self, component_uri_dict):
        for key, uri_list in component_uri_dict.items():
            for uri in uri_list:
                self.uri_list.append(self.name + "/api/" + key + "/" + uri)

    def shared(self):
        if len(self.__shared_obj) != 0:
            return True
        return False

    def add_shared_obj(self, project, obj_name):
        self.__shared_obj[project] = obj_name

    def get_shared_obj(self):
        return self.__shared_obj

    def set_object(self, component_name, obj_dict):
        self.__objects[component_name] = obj_dict

    def get_object(self, component_name):
        try:
            obj = self.__objects[component_name]
        except Exception as err:
            self.log.warning("Not found objects for " + component_name + " due: " + str(err))
            return None
        if obj:
            return obj
        self.log.warning("Not loaded component: " + component_name + " in project" + self.name)

    def init_logger(self, format="%(asctime)s - %(levelname)s - %(filename)s - %(lineno)d - %(message)s",
                    date_format="%Y-%m-%d %H:%M:%S", level=0):
        if self.log is not None:
            self.log.setLevel(level)
            formatter = logging.Formatter(format, date_format)
            self.__log_handler.setFormatter(formatter)
            # self.log.handlers
        else:
            log_path = os.path.join(xintesis.PROJECT_PATH, "logs/" + self.name)
            if not os.path.exists(log_path):
                os.makedirs(log_path)
            log_file = log_path + "/server_log.log"

            self.log = logging.getLogger(self.name)
            self.log.setLevel(level)

            self.__log_handler = logging.FileHandler(log_file)
            formatter = logging.Formatter(format, date_format)
            self.__log_handler.setFormatter(formatter)
            self.log.addHandler(self.__log_handler)
        self.file_handler.set_logger(self.log)
        return self.log


class Service:
    def __init__(self, name):
        self.name = name
        # services
        self.get = {}
        self.post = {}
        self.put = {}
        self.delete = {}

    def get_call(self, *args, **kwargs):
        result = self.get["func"](*args, **kwargs)
        if len(result) < 2:
            raise Exception("Service call must return at least two values, operation <boolean> and result")
        else:
            if type(result[0]) != bool:
                raise Exception("Service call first value most be boolean type")
        return result

    def post_call(self, *args, **kwargs):
        result = self.post["func"](*args, **kwargs)
        if len(result) < 2:
            raise Exception("Service call must return at least two values, operation <boolean> and result")
        else:
            if type(result[0]) != bool:
                raise Exception("Service call first value most be boolean type")
        return result

    def put_call(self, *args, **kwargs):
        result = self.put["func"](*args, **kwargs)
        if len(result) < 2:
            raise Exception("Service call must return at least two values, operation <boolean> and result")
        else:
            if type(result[0]) != bool:
                raise Exception("Service call first value most be boolean type")
        return result

    def delete_call(self, *args, **kwargs):
        result = self.delete["func"](*args, **kwargs)
        if len(result) != 2:
            raise Exception("Service call must return two values, operation <boolean> and result")
        else:
            if type(result[0]) != bool:
                raise Exception("Service call first value most be boolean type")
        return result


class ServicePack(object):
    def __init__(self, doc, default_mashall=False):
        self.name = ""
        self.desc = doc
        self.flag_def_marshall = default_mashall
        self.controller = None
        self.is_service = False
        self.my_services = {}
        self.__init_defaults__()
        self.model_list = list()
        self.__METHOD = 0
        self.__SEC = 1

    def list_uris(self):
        uri_list = list()
        for key, value in self.my_services.items():
            if value.get["active"]:
                uri_list.append(key + "/GET")
            if value.post["active"]:
                uri_list.append(key + "/POST")
            if value.put["active"]:
                uri_list.append(key + "/PUT")
            if value.delete["active"]:
                uri_list.append(key + "/DELETE")
        return uri_list

    def __init_defaults__(self):
        # services structure:
        # {"active": Bool, "security": Bool, "parser": Bool, "expect": None, "doc": "", "func": None}
        self.__get = {"active": False, "security": True, "parser": True, "expect": None, "doc": "", "func": None}
        self.__post = {"active": False, "security": True, "parser": False, "expect": None, "doc": "", "func": None}
        self.__put = {"active": False, "security": True, "parser": False, "expect": None, "doc": "", "func": None}
        self.__delete = {"active": False, "security": True, "parser": False, "expect": None, "doc": "", "func": None}
        # Structure: {"func_name":[<"get"|"post"|"put"|"delete">,<True,False>]}, handle list as tuple
        self.__unsec_mapping = dict()

        # default marshall
        if self.flag_def_marshall:
            self.__get["marshall"] = ServicePack.__def_marshall()
            self.__post["marshall"] = ServicePack.__def_marshall()
            self.__put["marshall"] = ServicePack.__def_marshall()
            self.__delete["marshall"] = ServicePack.__def_marshall()
        else:
            self.__get["marshall"] = None
            self.__post["marshall"] = None
            self.__put["marshall"] = None
            self.__delete["marshall"] = None
        # default delete expect
        self.__delete["expect"] = {
            'id_list': fields.List(fields.String, required=True, description='Lista de ID a eliminar')}
        # default get expect
        self.__get["expect"] = self.__def_get_parser()

    # define defaults methods for marshall and expecting
    @staticmethod
    def __def_marshall(fields_dict=fields.String(required=False, description='Datos de respuesta')):
        expect_model = {}
        expect_model["success"] = fields.Boolean(required=True, description='Resultado de la operacion realizada')
        expect_model["message"] = fields.String(required=False, description='Mensaje en caso de error')
        if type(fields_dict) == dict:
            expect_model.update(fields_dict)
        else:
            expect_model["data"] = fields_dict
        return expect_model

    @staticmethod
    def __def_get_parser():
        def_get_parser = reqparse.RequestParser()
        def_get_parser.add_argument('elements',
                                    type=int,
                                    required=False,
                                    help='Elements per page')
        def_get_parser.add_argument('page',
                                    type=int,
                                    required=False,
                                    help='Page number')
        return def_get_parser

    def get_expect(self, func):
        try:
            expect = func()
            if type(expect) != dict:
                self.__get["expect"] = expect
                if expect is None:
                    self.__get["parser"] = False
            else:
                logging.warning("Expect get function '" + func.__name__ + "' has a BODY param, expect set to default")
        except Exception as err:
            logging.critical("Expect function '" + func.__name__ + "' error: " + str(err))
        func_src = inspect.getsource(func)
        # get request must not contain body
        if "werkzeug.datastructures.FileStorage" in func_src:
            logging.warning("Expect get function '" + func.__name__ + "' has a BODY param, expect set to default")
            self.__get["expect"] = self.__def_get_parser()
        if "location='form'" in func_src:
            logging.warning("Expect get function '" + func.__name__ + "' has a BODY param, expect set to default")
            self.__get["expect"] = self.__def_get_parser()

        static_call = StaticMethod(func)
        return static_call

    def get_marshall(self, func):
        data = func()
        self.__get["marshall"] = ServicePack.__def_marshall(data)

        static_call = StaticMethod(func)
        return static_call

    def post_expect(self, func):
        try:
            expect = func()
            if type(expect) != dict:
                self.__post["parser"] = True
            self.__post["expect"] = expect
        except Exception as err:
            logging.critical("Expect function '" + func.__name__ + "' error: " + str(err))

        static_call = StaticMethod(func)
        return static_call

    def post_marshall(self, func):
        data = func()
        self.__post["marshall"] = ServicePack.__def_marshall(data)

        static_call = StaticMethod(func)
        return static_call

    def put_expect(self, func):
        try:
            expect = func()
            if type(expect) != dict:
                self.__put["parser"] = True
            self.__put["expect"] = expect
        except Exception as err:
            logging.critical("Expect function '" + func.__name__ + "' error: " + str(err))

        static_call = StaticMethod(func)
        return static_call

    def put_marshall(self, func):
        data = func()
        self.__put["marshall"] = ServicePack.__def_marshall(data)

        static_call = StaticMethod(func)
        return static_call

    def delete_expect(self, func):
        try:
            expect = func()
            if type(expect) != dict:
                self.__delete["parser"] = True
            self.__delete["expect"] = expect
        except Exception as err:
            logging.critical("Expect function '" + func.__name__ + "' error: " + str(err))

        static_call = StaticMethod(func)
        return static_call

    # 204 responses not content allowed
    def __delete_marshall(self, func):
        data = func()
        self.__delete["marshall"] = ServicePack.__def_marshall(data)

        static_call = StaticMethod(func)
        return static_call

    def service(self, some_class):
        new_serv = Service(some_class.__name__)

        # marshalling warnings
        if self.__post["active"] and self.__post["marshall"] is None:
            logging.warning("No active POST marshalling in " + new_serv.name)
        if self.__put["active"] and self.__put["marshall"] is None:
            logging.warning("No active PUT marshalling in " + new_serv.name)

        # updating security sync
        for key, value in self.__unsec_mapping.items():
            if value[self.__METHOD] == "get":
                self.__get["security"] = value[self.__SEC]
            if value[self.__METHOD] == "post":
                self.__post["security"] = value[self.__SEC]
            if value[self.__METHOD] == "put":
                self.__put["security"] = value[self.__SEC]
            if value[self.__METHOD] == "delete":
                self.__delete["security"] = value[self.__SEC]

        new_serv.post = self.__post.copy()
        new_serv.get = self.__get.copy()
        new_serv.put = self.__put.copy()
        new_serv.delete = self.__delete.copy()
        self.my_services[some_class.__name__] = new_serv
        self.__init_defaults__()
        return some_class

    def unsec(self, func):
        """
        Disable security from service
        Args:
            func: some class method

        Returns: func

        """
        # security sync
        if str(func.__name__) not in self.__unsec_mapping.keys():
            self.__unsec_mapping[str(func.__name__)] = ["", False]
        else:
            self.__unsec_mapping[str(func.__name__)][self.__SEC] = False
        return func

    def get_method(self, func):
        if self.__get["active"]:
            logging.warning("GET method previously defined, redefinition ignored ")
            return func
        self.__get["active"] = True
        self.__get["doc"] = func.__doc__ if func.__doc__ else ""
        self.__get["func"] = func
        # security sync
        if str(func.__name__) not in self.__unsec_mapping.keys():
            self.__unsec_mapping[str(func.__name__)] = ["get", True]
        else:
            self.__unsec_mapping[str(func.__name__)][self.__METHOD] = "get"

        static_call = StaticMethod(func)
        return static_call

    def post_method(self, func):
        if self.__post["active"]:
            logging.warning("POST method previously defined, redefinition ignored ")
            return func
        self.__post["active"] = True
        self.__post["doc"] = func.__doc__ if func.__doc__ else ""
        self.__post["func"] = func
        # security sync
        if str(func.__name__) not in self.__unsec_mapping.keys():
            self.__unsec_mapping[str(func.__name__)] = ["post", True]
        else:
            self.__unsec_mapping[str(func.__name__)][self.__METHOD] = "post"

        static_call = StaticMethod(func)
        return static_call

    def put_method(self, func):
        if self.__put["active"]:
            logging.warning("PUT method previously defined, redefinition ignored ")
            return func
        self.__put["active"] = True
        self.__put["doc"] = func.__doc__ if func.__doc__ else ""
        self.__put["func"] = func
        # security sync
        if str(func.__name__) not in self.__unsec_mapping.keys():
            self.__unsec_mapping[str(func.__name__)] = ["put", True]
        else:
            self.__unsec_mapping[str(func.__name__)][self.__METHOD] = "put"

        static_call = StaticMethod(func)
        return static_call

    def delete_method(self, func):
        if self.__delete["active"]:
            logging.warning("DELETE method previously defined, redefinition ignored ")
            return func
        self.__delete["active"] = True
        self.__delete["doc"] = func.__doc__ if func.__doc__ else ""
        self.__delete["func"] = func
        # security sync
        if str(func.__name__) not in self.__unsec_mapping.keys():
            self.__unsec_mapping[str(func.__name__)] = ["delete", True]
        else:
            self.__unsec_mapping[str(func.__name__)][self.__METHOD] = "delete"

        static_call = StaticMethod(func)
        return static_call

    # Xintesis Service  Exceptions
    class XtsServiceException(Exception):
        def __init__(self, msg, code=418):
            response = {"success": False, "message": str(msg)}
            resp_code = code

    class XtsServiceUnauthorized(XtsServiceException):
        def __init__(self, msg):
            response = {"success": False, "message": str(msg)}
            resp_code = 401

    class XtsServiceForbidden(XtsServiceException):
        def __init__(self, msg):
            response = {"success": False, "message": str(msg)}
            resp_code = 403
