import logging
import re

logger = logging.getLogger('base')


def import_by_string(full_name):
    module_name, unit_name = full_name.rsplit('.', 1)
    return getattr(
        __import__(module_name, fromlist=['']),
        unit_name)


def identity(args):
    return args


# Permits only trivial lambda functions that support basic arithmetic.
# For E.g., normalizing dimensions to the same scale with `lambda x: x/255`
RESTRICTED_LAMBDA_FUNCTION_RE = re.compile(r'lambda\s+?.\s*:\s*([a-z\d]+\s*(\*|\/|\+|\-)\s*)+([a-z\d]+\s*)')


class BadLambdaFunctionError(Exception):
    def __init__(self, message):
        self.message = message


def safe_eval_lambda(lambda_str):
    """Uses a regular expression to permit only trivial lambda functions which are then evaled
    without builtins.

    It's prudent to read https://nedbatchelder.com/blog/201206/eval_really_is_dangerous.html
    to understand how dangerous eval can be and even though a developer has full control of
    a spec that is deployed, we want to make it hard for a blackhat to craft something malicious
    that bypasses both the sanitizing regex and the restricted mode where builtins are nullified.

    Please note that `ast.literal_eval` does not support lambda functions.

    :param lambda_str: A trivial lambda function that supports basic arithmetic only. Validated with
    RESTRICTED_LAMBDA_FUNCTION_RE and meant for trivial scenarios like normalizing dimensions to the
    same scale with `lambda x: x/255'.

    :return: An evaluated lambda function.
    """
    if RESTRICTED_LAMBDA_FUNCTION_RE.match(lambda_str):
        try:
            return eval(lambda_str, {'__builtins__': {}})
        except Exception as e:
            raise BadLambdaFunctionError(e)
    raise BadLambdaFunctionError(lambda_str)


def import_function_or_identity(full_name):
    if full_name:
        try:
            return import_by_string(full_name)
        except Exception as e:
            logger.error(
                'Failed importing function %s with exception %s, '
                'degrading to the identity function',
                full_name, e)
    return identity


def import_callable_class_or_identity(full_name):
    if full_name:
        try:
            klass = import_by_string(full_name)
            if callable(klass):
                instance = klass()
                return instance
            else:
                logger.error(
                    'Class %s does not define "__call__", '
                    'degrading to the identity function',
                    full_name)
        except Exception as e:
            logger.error(
                'Failed importing callable class %s with exception %s, '
                'degrading to the identity function',
                full_name, e)
    return identity


def name(klass_or_function):
    try:
        return klass_or_function.__name__
    except:
        return klass_or_function.__class__.__name__
