__author__ = 'J41R0'

# defaults
wsgi = """#! /usr/bin/env python3
# -*- encoding: utf-8 -*-

import os
import sys
import xintesis
from xintesis.engine import XthEngine

if __name__ == "__main__":
    xintesis.PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))
    xintesis.core.init_core()
    XthEngine.run()

"""

def_init = """
def init_objects(config_dict):
    \"\"\"
    Init required project's objects using defined configuration. Returns an object dict that is added to project object. 
    This method is called  in server load step. 
    Args:
        config_dict: project config dict

    Returns: dict object in way {'<obj_nname>':<object>, ... }

    \"\"\"
    # only testing purposes
    obj_list = dict()
    obj_list['input_cfg'] = config_dict
    return obj_list

"""

app_cfg = """[server]
# server host
host = 0.0.0.0
# server port
port = 5000
# execution mode
mode = debug
# application name
app_name = app
# secert key for jwt auth
jwt_secret_key = may the force be with you ...

[logging]
# path to file to write logs
filename = logs/xsa_server.log
# show log in standard output if , if 0 as_process not show, otherwise show logs in console.
enabled_stdout = 1
# min logging level. 0- default 1- debug, 2- info, 3- warning, 4- error, 5- critical.
level = 2
# maximun log file size (bytes)
max_bytes = 1048576
# maximun log file count
backup_count = 3
# log format
format = %%(asctime)s - %%(levelname)s - %%(filename)s - %%(lineno)d - %%(message)s
# date format
datefmt = %%Y-%%m-%%d %%H:%%M:%%S

"""

proj_cfg = """---
project name: Default
security:
  use_security: False
description: >
  Default sample project. Change me !!!
mode: debug
logging:
  level: 1
  format: '%%(asctime)s - %%(levelname)s - %%(filename)s - %%(lineno)d - %%(message)s'
  date_format: '%%Y-%%m-%%d %%H:%%M:%%S'
config:
  desc: my project config data
dependencies:
  - demo
---
name: demo
config:
  model:
    type: file
    file_path: model
--- 

"""

demo_pack = """import werkzeug
from flask_restplus import fields, reqparse
from xintesis import ServicePack

service_pack = ServicePack("My demo component general description.")


@service_pack.service
class DemoPack:
    @service_pack.get_expect    
    def val_def():
        \"\"\"
        GET expect always use a RequestParser and not defined param location = 'form' . 
        If not expect defined by default use the integer fields 'elements' and 'page',
        \"\"\"
        
        expect = reqparse.RequestParser()
        expect.add_argument('get_data',
                            required=True,
                            help='Some input data')
        return expect

    @service_pack.get_method
    def some_method(project, input, obj_dict):
        \"\"\"My GET example DOC\"\"\"
        # result = demo_method_to_service(project)
        result = "CHANGE"
        # some code
        print(project.uri_list)
        # print(obj_dict)
        return True, result

    @service_pack.post_expect
    def expect_def():
        \"\"\"
        POST expect may use a RequestParser or JSON imput in pyaload field formated as dict, see also PUT expect example
        \"\"\"
        post_data = reqparse.RequestParser()
        post_data.add_argument('some_file',
                                type=werkzeug.datastructures.FileStorage,
                                location='files',
                                required=True,
                                help='Some file')
        post_data.add_argument('some_data',
                                required=False,
                                location='form',
                                help='Some optional data')
        return post_data
        
    @service_pack.post_method
    def some_method2(**kwargs):
        \"\"\"My POST example DOC\"\"\"
        project = kwargs['project']
        my_input = kwargs['input']
        obj_dict = kwargs['obj_dict']
        
        # some code
        data = input['some_data']
        print(data)
        
        file = input['some_file']
        save_file_dir = "downloads" 
        if not project.model_exist(save_file_dir):
            project.model_mkdir(save_file_dir)
        
        # saving file    
        if my_input['img_file'].filename not in project.model_lsdir():
            # internally use secure filename 
            project.model_save_file(save_file_path, file) 
        
        # returning a file, the only case to return 3 params 
        return True, project.model_lsdir()[-1], "file"
        
    @service_pack.put_expect
    def expect_put():
        \"\"\"
        PUT expect may use a RequestParser or JSON imput in pyaload field formated as dict, see also POST expect example 
        \"\"\"
        expect = dict()
        expect["text"] = fields.String(required=True, description='A test parameter')
        return expect
        
    @service_pack.put_method
    def some_method3(**kwargs):
        project = kwargs['project']
        my_input = kwargs['input']
        obj_dict = kwargs['obj_dict']
        
        print(my_input)
        
        # not success operation return 
        return False, "My Bad!!!"
        
    @service_pack.delete_method
    def some_method4(**kwargs):
        project = kwargs['project']
        my_input = kwargs['input']
        obj_dict = kwargs['obj_dict']
        # if not expect defined kwargs['input']['id_list'] is a list of strings  
        dict_out = {}
        dict_out['numbers'] = [1,2,3]
        dict_out['text'] = "first numbers"
        # auto format dict to JSON
        return True, my_input

"""

demo_proj = """from xintesis import ServicePack
from flask_restplus import Resource, fields, reqparse

service_pack = ServicePack("My project general description.")


@service_pack.service
class DemoProj:
    @service_pack.delete_method
    def test_method(project, input, obj_dict):
        \"\"\" Complex help
        \n This method do nothing but show a JSON as doc 
        \n JSON: 
        \n\t {
        \n\t "features" :
        \n\t   [
        \n\t\t     {"name": "temperature", "val": 32},
        \n\t\t     {"name": "weight", "val": 55},
        \n\t   ]
        \n\t }
        \"\"\"
        # exceptions are handled in other place 
        # params can be access using kwargs or the variables project, input, obj_dict
        raise Exception("help")
        return True, "Never see it"

    @service_pack.get_method
    def test_method2(**kwargs):
        # a method with no doc in API
        print(kwargs)
        return True, 42

"""

demo_test = """from selenium import webdriver
import unittest


class DefaultVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_homepage(self):
        # Test Sample project homepage
        self.browser.get('http://localhost:5000/simple_demo')
        # Default title test
        self.assertIn('Default', self.browser.title)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
"""


def create_defaults(dir):
    # default app files
    with open(dir + "/wsgi.py", 'w') as new_wsgi:
        new_wsgi.write(wsgi)

    with open(dir + "/config.ini", 'w') as new_app_cfg:
        new_app_cfg.write(app_cfg)

    # default package files
    with open(dir + "/packages/demo/__init__.py", 'w') as demo_init:
        demo_init.write(demo_init)

    with open(dir + "/packages/demo/services.py", 'w') as demo_pack_services:
        demo_pack_services.write(demo_pack)

    # default project files
    with open(dir + "/projects/default/__init__.py", 'w') as def_init:
        def_init.write(def_init)

    with open(dir + "/projects/default/config.yaml", 'w') as def_proj_cfg:
        def_proj_cfg.write(proj_cfg)

    with open(dir + "/projects/default/services.py", 'w') as def_pack_services:
        def_pack_services.write(demo_proj)

    with open(dir + "/projects/default/test/test_project.py", 'w') as def_pack_test:
        def_pack_test.write(demo_test)
