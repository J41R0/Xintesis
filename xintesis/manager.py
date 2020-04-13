__author__ = 'J4IR0'
__doc__ = "Xintesis manager, contains global variables and singletons objects used"

import os
import sys
import errno
import logging
import configparser

from shutil import copyfile
from logging.handlers import RotatingFileHandler

import xintesis

# TODO: review unused functions to erase it

config_file = None
service_set = set()

# server flags
server_loaded = False

# server data
server_broken_packages = []
server_packages = []
server_modules = []


# log_file_handler = None
def __find_config_file(app_name):
    global_conf_dir = os.path.join(xintesis.PROJECT_PATH, 'conf')
    global_conf_file = os.path.join(global_conf_dir, 'config.ini')
    is_global = False
    if os.path.exists(global_conf_dir):
        if os.path.exists(global_conf_file):
            global config_file
            config_file = global_conf_file
            return config_file
        is_global = True

    paths = [
        os.path.join(xintesis.PROJECT_PATH, 'config.ini'),
        os.path.join(".", "config.ini".format(app_name)),
        os.path.join("../", "config.ini".format(app_name)),
        os.path.join(".", "{0}.ini".format(app_name)),
        os.path.join("../etc", "{0}.ini".format(app_name)),
        os.path.join("../config", "{0}.ini".format(app_name)),
        os.path.join("/usr/share", app_name, "data", "{0}.ini".format(app_name)),
        os.path.join("/opt", app_name, "{0}.ini".format(app_name)),
        os.path.join("/opt", app_name, "config.ini"),
        os.path.join("/etc", app_name, "{0}.ini".format(app_name))
    ]
    for file in paths:
        if os.path.exists(file):
            # global config_file
            if is_global:
                copyfile(file, global_conf_file)
                config_file = global_conf_file
            else:
                config_file = os.path.abspath(file)
            break
    return config_file


def exist_deps(deps_list):
    """Check internal deps for dep_list"""
    deps_set = set(deps_list)
    active_components = set(server_packages) | set(server_modules)
    # print(deps_list, active_components)
    if len(active_components.intersection(deps_set)) != len(deps_set):
        return False
    return True


def add_logger(proj_name, logger_obj):
    set_singleton(logger_obj, proj_name + "_logger")


def logger(project_name):
    """
    Get project logger
    Args:
        project_name: project name

    Returns: Logger object

    """
    return get_singleton(project_name + "_logger")


# init global logger
def __init_logger(ini_file):
    """
    Server logger initialization
    Args:
        ini_file: server config file

    Returns:

    """
    if not os.path.exists(ini_file):
        raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), ini_file)

    parser = configparser.ConfigParser()
    try:
        parser.read(ini_file)
        format_str = parser.get("logging", "format", fallback=None)
        date_fmt = parser.get("logging", "datefmt", fallback=None)
        log_file = parser.get("logging", "filename", fallback=None)
        log_level = parser.getint("logging", "level", fallback=0)
    except Exception as error:
        raise error

    log_handlers = []
    log_file = os.path.join(xintesis.PROJECT_PATH, log_file)

    if 1 <= log_level <= 5:
        log_level *= 10
    else:
        log_level = 0

    if log_file:
        try:
            log_dir = os.path.dirname(log_file)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            max_bytes = parser.getint("logging", "max_bytes", fallback=0)
            backup_count = parser.getint("logging", "backup_count", fallback=0)
            file_handler = RotatingFileHandler(log_file, maxBytes=max_bytes,
                                               backupCount=backup_count)
            # file_handler.setLevel(log_level)
            log_handlers.append(file_handler)
        except Exception as err:
            raise err
    try:
        show_stdout = parser.getboolean("logging", "enabled_stdout", fallback=False)
        if show_stdout:
            stdout_handler = logging.StreamHandler(sys.stdout)
            stdout_handler.setLevel(log_level)
            log_handlers.append(stdout_handler)
    except Exception as err:
        raise err
    try:
        # set handlers to logger
        logging.basicConfig(format=format_str, datefmt=date_fmt,
                            handlers=log_handlers, level=log_level)
    except Exception as err:
        raise err
        # return log_handlers


def config_get(section, option, fallback=None, current_file_path=None):
    """
    Obtiene el valor de el parametro de configuracion deseado de un fichero dado
     o de la configuracion general del servidor
    Args:
        section: Nombre de la seccion donde se encuentra el dato
        option: Opcion deseada dentro de la seccion
        fallback: respuesta en caso de no encotrar la seccion u opcion deseadas
        current_file_path: Ruta hacia el fihero deseado, en caso de no especificarse
         lo busca en la configuracion general

    Returns: Valor del elemento en string o del fallback en caso de no encontrarse

    """
    # get section value from config file
    if current_file_path is None:
        try:
            parser = configparser.ConfigParser()
            parser.read(config_file)
            value = parser.get(section, option, fallback=fallback)
            return value
        except Exception as err:
            logging.error(str(err))
    else:
        # ini config file
        if str(current_file_path).split('.')[-1] == 'ini':
            try:
                parser = configparser.ConfigParser()
                parser.read(current_file_path)
                value = parser.get(section, option, fallback=fallback)
                return value
            except Exception as err:
                logging.error(str(err))
        else:
            logging.error("Cannot process ." + str(current_file_path).split('.')[-1] + " file")


def load(app_name="xsa"):
    """
    Carga el fichero de configuracion del servidor, inicia el logger con los paramentros encontrados y busca los
    modulos y paquetes activos en el servidor.
    Args:
        app_name: nombre de la aplicacion

    Returns: None

    """
    # load configfile and init system logger
    config_file = __find_config_file(app_name)
    if config_file is not None:
        __init_logger(config_file)
    __check_components()


def __check_components():
    """
    Search for packages and modules that can be used
    Returns: None

    """
    # check modules
    modules_dir = os.path.join(xintesis.PROJECT_PATH, "modules")
    for curr_mod in os.listdir(modules_dir):
        if os.path.exists(os.path.join(modules_dir, curr_mod + "/__init__.py")):
            server_modules.append(curr_mod)
    # check packages
    packages_dir = os.path.join(xintesis.PROJECT_PATH, "packages")
    for curr_pack in os.listdir(packages_dir):
        if os.path.exists(os.path.join(packages_dir, curr_pack + "/__init__.py")):
            server_packages.append(curr_pack)


def gen_unique_id():
    import uuid
    return str(uuid.uuid4())


__singletons = {}


def get_singleton(class_, *args, **kwargs):
    if str(class_) not in __singletons:
        if str(type(class_).__name__) not in __singletons:
            try:
                __singletons[str(type(class_).__name__)] = class_(*args, **kwargs)
            except Exception as err:
                logging.error('Error creating object from class: ' + type(class_).__name__)
                logging.error(str(err))
        else:
            return __singletons[str(type(class_).__name__)]
    else:
        return __singletons[class_]


def in_singleton(name):
    if name in __singletons.keys():
        return True
    return False


def set_singleton(object_, name=None):
    if name is None:
        if str(type(object_).__name__) not in __singletons:
            try:
                __singletons[type(object_).__name__] = object_
            except Exception as err:
                logging.error('Error adding object from class: ' + type(object_).__name__)
                logging.error(str(err))
                return False
    else:
        try:
            __singletons[name] = object_
        except Exception as err:
            logging.error('Error adding object from class: ' + type(object_).__name__)
            logging.error(str(err))
            return False
    return True


def set_single_data(data_name, value_):
    if str(data_name) not in __singletons:
        try:
            __singletons[str(data_name)] = value_
        except Exception as err:
            logging.error('Error adicionar el valor: ' + data_name)
            logging.error(str(err))
        return False
    return True


def list_objects():
    return __singletons.keys()