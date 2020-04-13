__author__ = 'J41R0'

import os
import yaml
import logging
from importlib import import_module

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from werkzeug.contrib.fixers import ProxyFix

import xintesis
from xintesis import manager
from xintesis.template.project import *


class XtsEngine:
    """
    Xintesis engine class for load data for server start and all services interfaces generation
    """
    generated = False

    def __init__(self):
        self.app = XtsEngine.load_app()

    @staticmethod
    def run(is_wsgi=False):
        """
        Start server for flask application app  
        Args:
            is_wsgi: is running wsgi

        Returns: None

        """
        app = XtsEngine.load_app()
        CORS(app)
        if manager.server_loaded:
            server_mode = manager.config_get("server", "mode")
            host = manager.config_get("server", "host", fallback=None)
            port = manager.config_get("server", "port", fallback=None)
            debug = False
            if server_mode == "debug":
                debug = True
            if is_wsgi:
                return app, host, port, debug
            app.run(host=host, port=port, debug=debug, use_reloader=False)
        else:
            logging.fatal("Xintesis Engine: Server configuration needs to be loaded ")

    @staticmethod
    def load_app():
        """
        Build and load all project interfaces from skeletons and joint all in flask application
        Returns: Flask application with all interfaces

        """
        # init const values
        API = 0
        PROJECT_OBJ = 1
        # init manager
        manager.load()
        # create application
        app = Flask("Xintesis Server")
        app.wsgi_app = ProxyFix(app.wsgi_app)
        app.config['JWT_SECRET_KEY'] = os.getenv('XTS_SECRET_KEY', "may the force be with you ...")
        app.config['JWT_HEADER_NAME'] = 'XSA-API-KEY'
        app.config['JWT_HEADER_TYPE'] = str
        app.config['JWT_ALGORITHM'] = 'HS512'
        app.config['JWT_ACCESS_TOKEN_EXPIRES'] = True
        jwt = JWTManager(app)
        manager.set_singleton(jwt, "xts_jwt")
        manager.set_singleton(app, "xts_app")
        if not manager.server_loaded:
            projects_dict = dict()
            # server load and project interface generation
            proj_dir = os.path.join(xintesis.PROJECT_PATH, 'projects')
            # init all project custom objects
            for project in os.listdir(proj_dir):
                if project not in projects_dict.keys() and os.path.isdir(os.path.join(proj_dir, project)) and \
                        XtsEngine.__is_valid_folder(proj_dir, project):
                    logging.info("Loading project " + project)
                    proj_data = XtsEngine.__load_project(project, os.path.join(proj_dir, project))
                    if proj_data:
                        # tuple: <api, project obj>
                        projects_dict[project] = proj_data

            # handle projects shared packages
            for project in projects_dict.keys():
                if projects_dict[project][PROJECT_OBJ].shared():
                    try:
                        for proj, obj_id in projects_dict[project][PROJECT_OBJ].get_shared_obj().items():
                            shared = projects_dict[proj][PROJECT_OBJ].get_object(obj_id)
                            projects_dict[project][PROJECT_OBJ].set_object(obj_id, shared)
                    except Exception as err:
                        logging.critical("Can not link shared object from " + project + " due:" + str(err))
            logging.info("Load finished, projects path:")
            host = manager.config_get("server", "host")
            port = manager.config_get("server", "port")
            # register each project API
            for project in projects_dict.keys():
                logging.info("Running API endpoint on: " + host + ':' + port + '/' + str(project) + '/api')
                app.register_blueprint(projects_dict[project][API])
                # save ref to API blue print
                # manager.set_singleton(projects_dict[project][API], name=project + "_API")
        manager.server_loaded = True
        return app

    @staticmethod
    def __is_valid_folder(proj_dir, proj):
        if proj != '__pycache__' and os.path.exists(os.path.join(proj_dir, proj)):
            content = os.listdir(os.path.join(proj_dir, proj))
            # project definition requirements
            if "config.yaml" in content:
                return True
        return False

    @staticmethod
    def __load_component(proj_id, project, curr_cfg, project_deps):
        # init each component objects
        component_name = curr_cfg['name']
        if not manager.exist_deps([component_name]):
            raise Exception("Component " + component_name + " not in loaded dependencies")
        if component_name not in project_deps:
            raise Exception("Component " + component_name + " not in project " + proj_id + " dependencies")
        # remove found dependencies
        project_deps.remove(component_name)
        if 'dependencies' in curr_cfg.keys():
            deps = curr_cfg['dependencies']
            if not manager.exist_deps(deps):
                raise Exception("Project " + proj_id + " can not load all dependencies")
        try:
            # init and subscribe all components
            if 'shared' in curr_cfg.keys():
                project.add_shared_obj(curr_cfg['shared']['project_id'], component_name)
            else:
                pack_config = curr_cfg['config']
                # init all package objects for project
                init_obj = import_module('packages.' + component_name)
                try:
                    obj_dict = init_obj.init_objects(pack_config)
                    project.set_object(component_name, obj_dict)
                except Exception as err:
                    logging.warning("Not objects created for component '" + component_name
                                    + "' in project '" + project.name + "' due: " + str(err))

        except Exception as err:
            raise Exception("Error " + str(err) + " loading package " + component_name)

    @staticmethod
    def __initial_load(proj_id, curr_cfg, project_deps):
        # inital load for project
        project = None
        project_api = None
        proj_name = curr_cfg['project name']
        uri_dict = dict()
        # controller services
        serv_pack_list = []

        # security vars
        security_cfg = curr_cfg['security']
        use_security = security_cfg['use_security']

        # project description
        proj_desc = curr_cfg['description']
        proj_desc = str(proj_desc).replace("\n", " ")
        # dependencies API generation
        for curr_dep in project_deps:
            if curr_dep in manager.server_broken_packages:
                Exception("Project " + proj_id + " can not load " + curr_cfg[
                    'name'] + " sub-dependencies")
            try:
                package = import_module('packages.' + curr_dep + '.controller')
            except Exception as err:
                raise Exception("Cannot import module " + curr_dep + " due: " + str(err))
            # set package name
            package.service_pack.name = curr_dep
            uri_dict[curr_dep] = package.service_pack.list_uris()
            serv_pack_list.append(package.service_pack)
        # include service.py services in project API
        try:
            package = import_module("projects." + proj_id + '.controller')
            # TODO: change repeated project name in URI
            package.service_pack.name = proj_id
            uri_dict[proj_id] = package.service_pack.list_uris()
            package.service_pack.is_service = True
            serv_pack_list.append(package.service_pack)
        except Exception as err:
            logging.error("Ignored particular services due: " + str(err))

        # init project data
        XtsEngine.__init_project_data(proj_id)
        hide_api = False
        if "mode" in curr_cfg.keys() and curr_cfg["mode"] == "production":
            hide_api = True
        # gen project source
        src = gen_project_src(proj_name, proj_id, hide_api, use_security, serv_pack_list, proj_desc)
        # write source to api file
        api_path = os.path.join(xintesis.PROJECT_PATH, "controllers/" + proj_id) + "/api.py"
        with open(api_path, "wt") as file:
            file.write(src)
        file.close()
        try:
            # load API blueprint and store for return
            api = import_module('controllers.' + proj_id + '.api')
            project_api = api.project_api
            log_cfg = curr_cfg['logging']
            project = api.project
            project.init_logger(format=log_cfg['format'],
                                date_format=log_cfg['date_format'],
                                level=log_cfg['level'])
            project.set_uris(uri_dict)
            # set up project configuration and init self project objects
            if 'config' in curr_cfg.keys():
                project.config = curr_cfg['config']
            project.init_objects(security_cfg)
        except Exception as err:
            logging.critical("Error importing API " + proj_id + ": " + str(err))

        logging.info("Project " + proj_id + " API generated")
        return project, project_api

    @staticmethod
    def __load_project(proj_id, curr_proj_path):
        """
        Generate proj_name services interface according to project yaml configuration
        Args:
            proj_id: project name
            curr_proj_path: current project path

        Returns: current project blueprint

        """
        try:
            if os.path.exists(curr_proj_path + "/config.yaml"):
                with open(curr_proj_path + "/config.yaml", 'r') as cfg_file:
                    config = cfg_file.read()
                cfg_file.close()
                first = True
                all_deps_ok = False
                project = None
                project_api = None
                project_deps = None
                for curr_cfg in yaml.safe_load_all(config):
                    if curr_cfg is not None:
                        if all_deps_ok:
                            # load and init each project component
                            XtsEngine.__load_component(proj_id, project, curr_cfg, project_deps)
                        if first:
                            # for first loading step

                            first = False
                            project_deps = curr_cfg['dependencies'] if curr_cfg['dependencies'] else []
                            if proj_id in project_deps:
                                raise Exception(
                                    "Cannot load project " + proj_id + " due conflict with dependencies name")
                            if not manager.exist_deps(project_deps):
                                raise Exception("Project " + proj_id + " can not load all required dependencies")
                            else:
                                all_deps_ok = True
                            project, project_api = XtsEngine.__initial_load(proj_id, curr_cfg, project_deps)

                # project_deps.remove(proj_id)
                if len(project_deps) != 0:
                    logging.critical("Project " + proj_id + " not load dependencies: " + str(project_deps))
                # return API blueprint if all load steps success
                if project_api is not None:
                    logging.info("Project " + proj_id + " components loaded")
                    # manager.add_logger(proj_id, project.logger)
                    return project_api, project
        except Exception as err:
            logging.critical("Cannot load project " + proj_id + " due: " + str(err))

    @staticmethod
    def __init_project_data(proj_name):
        """
        Create folders used by project if they not exist
        Args:
            proj_name: Project name

        Returns: None

        """
        # init project folders for model, temporal files, service controller and logger
        log_path = os.path.join(xintesis.PROJECT_PATH, "logs/" + proj_name)
        if not os.path.exists(log_path):
            os.makedirs(log_path)

        model_path = os.path.join(xintesis.PROJECT_PATH, "model/" + proj_name)
        if not os.path.exists(model_path):
            os.makedirs(model_path)

        controller_path = os.path.join(xintesis.PROJECT_PATH, "controllers/" + proj_name)
        if not os.path.exists(controller_path):
            os.makedirs(controller_path)
