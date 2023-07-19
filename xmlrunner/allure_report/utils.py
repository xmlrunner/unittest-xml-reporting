import inspect
import shutil
import posixpath
import re
from allure_commons.model2 import Label
from allure_commons.model2 import Parameter
from allure_commons.utils import represent
import os


def name(test):
    full_name = fullname(test)
    test_params = params(test)
    allure_name = full_name.split(".")[-1]
    if test_params:
        params_str = "-".join([p.value for p in test_params])
        return f"{allure_name}[{params_str}]"
    return allure_name


def fullname(test):
    if hasattr(test, "_testFunc"):
        suit_name = test._testFunc.__module__
        test_name = test._testFunc.__name__
        return f"{suit_name}.{test_name}"
    test_info = test.id()
    suit_name = test_name = ""
    # check if this is a setup class
    if test_info.startswith("setUpClass"):
        test_splits = test_info.split(" ")
        test_name = test_splits[0]
        suit_name = test_splits[1].strip('()').split('.')[1]
        print(suit_name)
    else:
        suit_name, test_name = test_info.split(".")[1:]
    return f"{suit_name}.{test_name}"


def get_file_name(test):
    file_name = os.path.basename(inspect.getfile(type(test))).split(".")[0]
    return file_name


def get_domain_name(test):
    if test.DOMAIN is None:
        return "Default"
    return str(test.DOMAIN)



def copy_log_file(test):
    """ Copy the log file from logs folder to specific test suite.

    :param test: The current test from TestCase Class
    :return:     True (if the file is existed in the logs folder) False (if the file doesn't exist)

    """
    test_name = get_file_name(test)
    org_file = posixpath.join("logs", test_name + ".log")
    if os.path.isfile(org_file):
        des_file = posixpath.join("test-reports", "allure-results", get_domain_name(test), test_name,
                                  test_name + ".log")
        shutil.copy2(org_file, des_file)
        return True
    else:
        return False


def update_attrs(test, name, values):
    if type(values) in (list, tuple, str) and name.isidentifier():
        attrib = getattr(test, name, values)
        if attrib and attrib != values:
            attrib = sum(
                [tuple(i) if type(i) in (tuple, list) else (i,) for i in (attrib, values)],
                ()
            )
        setattr(test, name, attrib)


def labels(test):
    ALLURE_LABELS = [
        'epic',
        'feature',
        'story',
        'severity'
    ]

    def _get_attrs(obj, keys):
        key_pairs = set()
        for key in keys:
            values = getattr(obj, key, ())
            for value in (values,) if type(values) == str else values:
                key_pairs.add((key, value))
        return key_pairs

    keys = ALLURE_LABELS
    pairs = _get_attrs(test, keys)

    if hasattr(test, "_testFunc"):
        pairs.update(_get_attrs(test._testFunc, keys))
    elif hasattr(test, "_testMethodName"):
        test_method = getattr(test, test._testMethodName)
        pairs.update(_get_attrs(test_method, keys))
    return [Label(name=name, value=value) for name, value in pairs]


def params(test):
    def _params(names, values):
        return [Parameter(name=name, value=represent(value)) for name, value in zip(names, values)]

    # this does not exist
    test_id = test.id()

    if len(test_id.split("\n")) > 1:
        if hasattr(test, "_testFunc"):
            wrapper_arg_spec = inspect.getfullargspec(test._testFunc)
            arg_set, obj = wrapper_arg_spec.defaults
            test_arg_spec = inspect.getfullargspec(obj)
            args = test_arg_spec.args
            return _params(args, arg_set)
        elif hasattr(test, "_testMethodName"):
            method = getattr(test, test._testMethodName)
            wrapper_arg_spec = inspect.getfullargspec(method)
            obj, arg_set = wrapper_arg_spec.defaults
            test_arg_spec = inspect.getfullargspec(obj)
            args = test_arg_spec.args
            return _params(args[1:], arg_set)
