
import os
import shutil

from wsgi_intercept import httplib2_intercept
import wsgi_intercept

import httplib2
import simplejson

from tiddlyweb.model.bag import Bag
from tiddlyweb.web.serve import load_app
from tiddlyweb.config import config

from tiddlywebplugins.utils import get_store

# NOTES
# bag and recipe don't etag handling for PUT so adding for PATCH
# is weird. Thus we need to do HTTP 428 checks for tiddlers, but not
# bag or recipe.


def setup_module(module):
    app = load_app()
    def app_fn():
        return app

    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('0.0.0.0', 8080, app_fn)

    module.store = get_store(config)
    module.http = httplib2.Http()

    try:
        shutil.rmtree('store')
    except:
        pass  # we don't care

def test_patch_bag_flow():
    desc = 'oh hi'
    bag_json = '{"desc": "%s", "policy": {"read": ["frank"], "vroom": ["frank"], "write": ["ANY"]}}' % desc
    response, content = http.request('http://0.0.0.0:8080/bags/testbag',
            method = 'PATCH',
            headers = {'Content-Type': 'application/json'},
            body = bag_json)

    # no patch before PUT
    assert response['status'] == '409', content

    response, content = http.request('http://0.0.0.0:8080/bags/testbag',
            method = 'PUT', 
            headers = {'Content-Type': 'application/json'},
            body = '{"policy": {"read": ["cdent"]}}')

    assert response['status'] == '204', content

    bag = store.get(Bag('testbag'))
    assert bag.desc == ''
    assert bag.policy.read == ['cdent']

    response, content = http.request('http://0.0.0.0:8080/bags/testbag',
            method = 'PATCH',
            headers = {'Content-Type': 'text/plain'},
            body = 'oh hi')

    assert response['status'] == '415'
    assert 'application/json required' in content

    response, content = http.request('http://0.0.0.0:8080/bags/testbag',
            method = 'PATCH',
            headers = {'Content-Type': 'application/json'},
            body = bag_json)

    assert response['status'] == '204', content

    bag = store.get(Bag('testbag'))
    assert bag.desc == 'oh hi'
    assert bag.policy.read == ['frank']
    assert bag.policy.write == ['ANY']
