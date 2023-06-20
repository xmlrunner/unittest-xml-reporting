import inspect

from allure_commons.model2 import Label
from allure_commons.model2 import Parameter
from allure_commons.utils import represent


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
    test_id = test.id()
    suit_name, test_name = test_id.split(".")[1:]
    return f"{suit_name}.{test_name}"


def get_suit_name(test):
    suit_name = test.id().split(".")[1]
    return suit_name


def get_domain_name(test):
    if test.DOMAIN is None:
        return "Default"
    return str(test.DOMAIN)


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
    # ToDo move to commons
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
