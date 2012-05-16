"""
HTTP PATCH for TiddlyWeb.
"""

import simplejson

from tiddlyweb.model.bag import Bag
from tiddlyweb.model.policy import Policy
from tiddlyweb.store import NoBagError
from tiddlyweb.web.http import HTTP400, HTTP409, HTTP415, HTTPException
from tiddlyweb.web.util import get_route_value, content_length_and_type

class HTTP428(HTTPException):
    """428 Precondition Required"""

    status = __doc__

def patch_recipe(environ, start_response):
    return []

def patch_bag(environ, start_response):
    """
    PATCH a bag entity, resetting the description,
    or resetting one or more policy constraints.
    """
    store = environ['tiddlyweb.store']
    length, content_type = content_length_and_type(environ)

    if content_type != 'application/json':
        raise HTTP415('application/json required')

    bag_name = get_route_value(environ, 'bag_name')
    bag = Bag(bag_name)
    try:
        bag = store.get(bag)
    except NoBagError:
        raise HTTP409('Unable to patch non-existent bag')

    data = _read_input(environ, length)

    try:
        for key, value in data.iteritems():
            if key == 'desc':
                bag.desc = value
            elif key == 'policy':
                for constraint, rules in value.iteritems():
                    if constraint in Policy.attributes:
                        setattr(bag.policy, constraint, rules)
    except AttributeError, exc:
        raise HTTP400('Malformed bag info: %s' % exc)

    store.put(bag)

    start_response('204 No Content', [])
    return []


def patch_tiddler(environ, start_response):
    return []


PATCHABLE_ROUTES = [
        ('/recipes/{recipe_name:segment}', patch_recipe),
        ('/bags/{bag_name:segment}', patch_bag),
        ('/bags/{bag_name:segment}/tiddlers/{tiddler_name:segment}',
            patch_tiddler),
        ]


def init(config):
    """
    Initialize the plugin by calling add_patch_method.
    """
    if 'selector' in config:
        _add_patch_method(config['selector'])

def _add_patch_method(selector):
    """
    Add PATCH to PATCHABLE_ROUTES.
    """
    for index, (regex, method_dict) in enumerate(selector.mappings):
        if PATCHABLE_ROUTES:
            for path, method in PATCHABLE_ROUTES:
                if regex.match(path) is not None:
                    method_dict['PATCH'] = method
                    selector.mappings[index] = (regex, method_dict)
                    PATCHABLE_ROUTES.remove((path, method))
                    break
        else:
            break

def _read_input(environ, length):
    """
    Transform the wsgi input from JSON into a Python dict.
    """
    content = environ['wsgi.input'].read(int(length))

    try:
        data = simplejson.loads(content)
    except simplejson.JSONDecodeError, exc:
        raise HTTP400('Malformed patch document: %s' % exc)

    return data
