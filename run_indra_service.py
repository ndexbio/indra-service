__author__ = 'dexter'

import argparse
from bottle import route, run, template, default_app, request, debug
import ndex.client as nc
import json
import bel_utils as bu
import subprocess
import os
import psutil
import time


parser = argparse.ArgumentParser(description='run the indra service')

parser.add_argument('--verbose', dest='verbose', action='store_const',
                    const=True, default=False,
                    help='verbose mode')
parser.add_argument('--debug', dest='debug', action='store_const',
                    const=True, default=False,
                    help='debug mode')

arg = parser.parse_args()

if not bu.bel_gem_installed():
    raise Exception("The bel ruby gem is not installed. Aborting INDRA service start.")

if arg.debug:
    print("Debug mode engaged")
    debug()

if arg.verbose:
    print("Starting indra service in verbose mode")
else:
    print("Starting indra service")

app = default_app()
app.config['verbose'] = arg.verbose

app.config['ndex'] = nc.Ndex()

special_network_ids = [
    "9ea3c170-01ad-11e5-ac0f-000c29cb28fb",
    "55c84fa4-01b4-11e5-ac0f-000c29cb28fb"
]

app.config['engine'] = bu.BELQueryEngine(special_network_ids = special_network_ids)

def bel_gem_installed():
    try:
        installed = subprocess.check_output(["gem", "list", "bel", "-i"])
        print("installed = " + installed)
        if installed == "true\n":
            return True
        else:
            return False
    except Exception as re:
        return {"ERROR": True, "message": re.message}

@route('/hello/<name>')
def index(name):
    try:
        verbose_mode = app.config.get("verbose")
        if verbose_mode:
            return template('<b>This is the test method saying Hello, {{name}} verbosely</b>!', name=name)
        else:
            return template('<b>Hello {{name}}</b>!', name=name)
    except Exception as re:
        return {"error": True, "message": re.message}

@route('/status')
def status():
    try:
        q = request.query['memsize']

        engine = app.config.get('engine')
        rss_limit = 500000000
        start = time.time()
        result = {}
        result['message'] = {'time': start}
        result['message']['status'] = 'OK'

        if q:
            if type(q) is str:
                rss_limit = int(q)
            else:
                rss_limit = q

        large_corpus_uuid = "9ea3c170-01ad-11e5-ac0f-000c29cb28fb"

        gem_installed = bel_gem_installed()
        result['message']["bel_gem_installed"] = gem_installed

        # run a test query
        # NFKB1 neighborhood on BEL Large Corpus
        bel_script = engine.bel_neighborhood_query(large_corpus_uuid, 'NFKB1')

        if bel_script:
            result['message']["bel_query"] = "OK"
            if gem_installed:
                # convert the result to RDF
                bu.bel_script_to_rdf(bel_script)
                result['message']["bel_rdf"] = "DONE"
        else:
            result['message']["bel_query"] = "FAILED"
            result['message']['status'] = 'TROUBLE'

        # check memory use
        this_process = psutil.Process(os.getpid())
        rss = this_process.memory_info().rss
        result['message']['rss'] = rss
        if rss > rss_limit:
            result['message']['memory_status'] = "high memory usage"
            result['message']['status'] = 'TROUBLE'

        stop = time.time()
        result['message']['duration'] = stop - start

        # return the status
        print(json.dumps(result))
        return result

    except Exception as re:
        return {'message': {"error": True, "message": re.message}}

@route('/status/simple')
def status():
    try:
        q = request.query['memsize']

        engine = app.config.get('engine')
        rss_limit = 500000000
        start = time.time()
        result = {}
        result['message'] = {'time': start}
        result['message']['status'] = 'OK'

        if q:
            if type(q) is str:
                rss_limit = int(q)
            else:
                rss_limit = q

        large_corpus_uuid = "9ea3c170-01ad-11e5-ac0f-000c29cb28fb"

        gem_installed = bel_gem_installed()
        result['message']["bel_gem_installed"] = gem_installed

        # run a test query
        # NFKB1 neighborhood on BEL Large Corpus
        bel_script = engine.bel_neighborhood_query(large_corpus_uuid, 'NFKB1')

        if bel_script:
            result['message']["bel_query"] = "OK"
            if gem_installed:
                # convert the result to RDF
                # ============================================
                # DONT RUN THE RUBY SCRIPT FOR SIMPLE STATUS
                # ============================================
                # bu.bel_script_to_rdf(bel_script)
                result['message']["bel_rdf"] = "DONE"
        else:
            result['message']["bel_query"] = "FAILED"
            result['message']['status'] = 'TROUBLE'

        # check memory use
        this_process = psutil.Process(os.getpid())
        rss = this_process.memory_info().rss
        result['message']['rss'] = rss
        if rss > rss_limit:
            result['message']['memory_status'] = "high memory usage"
            result['message']['status'] = 'TROUBLE'

        stop = time.time()
        result['message']['duration'] = stop - start

        # return the status
        print(json.dumps(result))
        return result

    except Exception as re:
        return {'message': {"error": True, "message": re.message}}

@route('/bel_gem_installed')
def check_bel_gem():
    try:
        return {"content": str(bu.bel_gem_installed())}
    except Exception as re:
        return {"error": True, "message": re.message}

@route('/inf')
def inf():
    try:
        out = subprocess.check_output(["gem", "list"])
        return template(out)
    except Exception as re:
        return {"error": True, "message": re.message}

# GET the network summary
@route('/network/<networkId>')
def get_network_summary(networkId):
    try:
        ndex = app.config.get('ndex')
        return ndex.get_network_summary(networkId)
    except Exception as re:
        return {"error": True, "message": re.message}

@route('/network/<network_id>/asBELscript/query', method='GET')
def run_bel_script_query_get(network_id):
    try:
        query_string = request.query.searchString or None
        engine = app.config.get('engine')
        bel_script = engine.bel_neighborhood_query(network_id, query_string)
        if bel_script:
            return {"content": bel_script}
        else:
            return {"content": ''}
    except Exception as re:
        return {"error": True, "message": re.message}

@route('/network/<network_id>/asBELscript/query', method='POST')
def run_bel_script_query(network_id):
    try:
        dict = json.load(request.body)
        query_string = dict.get('searchString')
        engine = app.config.get('engine')
        print("POST bel neighborhood: "   + query_string + " on " + network_id)
        bel_script = engine.bel_neighborhood_query(network_id, query_string)
        if bel_script:
            return {"content": bel_script}
        else:
            return {"content": ''}
    except Exception as re:
        return {"error": True, "message": re.message}

@route('/network/<network_id>/asBELRDF/query', method='GET')
def run_bel_script_query_get(network_id):
    try:
        query_string = request.query.searchString or None
        engine = app.config.get('engine')
        print("GET bel neighborhood: "   + query_string + " on " + network_id)
        bel_script = engine.bel_neighborhood_query(network_id, query_string)
        if bel_script:
            rdf = bu.bel_script_to_rdf(bel_script)
            return {"content": rdf}
        else:
            return {"content": ''}
    except Exception as re:
        return {"error": True, "message": re.message}

@route('/network/<network_id>/asBELRDF/query', method='POST')
def run_bel_script_query(network_id):
    try:
        dict = json.load(request.body)
        query_string = dict.get('searchString')
        engine = app.config.get('engine')
        print("POST rdf neighborhood: "   + query_string + " on " + network_id)
        bel_script = engine.bel_neighborhood_query(network_id, query_string)
        if bel_script:
            rdf = bu.bel_script_to_rdf(bel_script)
            return {"content": rdf}
        else:
            return {"content": ''}
    except Exception as re:
        return {"error": True, "message": re.message}

run(app, host='0.0.0.0', port=8011)

##==================================================
# Deprecated, remove soon - Dexter 1/3/17
# def belscript_query(network_id, search_string):
#     ndex = app.config.get('ndex')
#
#     if not search_string:
#         abort(401, "requires searchString parameter")
#
#     cx = ndex.get_neighborhood(network_id, search_string)
#     bel_cx = bu.BelCx(cx)
#     bel_script = bel_cx.to_bel_script()
#     return bel_script
#
# @route('/network/<network_id>/asBELscript/query_old', method='POST')
# def run_bel_script_query(network_id):
#     dict = json.load(request.body)
#     search_string = dict.get('searchString')
#     bel_script = belscript_query(network_id, search_string)
#     return bel_script
#
# @route('/network/<network_id>/asBELscript/query_old', method='GET')
# def run_bel_script_query_get(network_id):
#     search_string = request.query.searchString or None
#     bel_script = belscript_query(network_id, search_string)
#     return bel_script
#
# @route('/network/<network_id>/asBELRDF/query_old', method='GET')
# def run_bel_script_query_get(network_id):
#     search_string = request.query.searchString or None
#     bel_script = belscript_query(network_id, search_string)
#     rdf = bu.bel_script_to_rdf(bel_script)
#     return rdf
#
# @route('/network/<network_id>/asBELRDF/query_old', method='POST')
# def run_bel_script_query(network_id):
#     dict = json.load(request.body)
#     search_string = dict.get('searchString')
#     bel_script = belscript_query(network_id, search_string)
#     rdf = bu.bel_script_to_rdf(bel_script)
#     return rdf

# def get_neighborhood_as_wrapped_network(ndex, network_id, search_string):
#     summary = ndex.get_network_summary(network_id)
#     source_format = bu.get_source_format(summary)
#     if not source_format == "BEL":
#         abort(401, "non-BEL network: network id " + network_id + " has source format " + str(source_format))
#
#     ndex_network = ndex.get_neighborhood(network_id, search_string)
#     return bu.NetworkWrapper(ndex_network, ['bel'])


# @route('/network/<network_id>/asBELscript/query_old', method='POST')
# def run_bel_script_query(network_id):
#     ndex = app.config.get('ndex')
#     dict = json.load(request.body)
#     search_string = dict.get('searchString')
#     if not search_string:
#         abort(401, "requires searchString parameter in POST data")
#     wrapped_network = get_neighborhood_as_wrapped_network(ndex, network_id, search_string)
#     bel_script = wrapped_network.writeBELScript()
#     return bel_script
#
# @route('/network/<network_id>/asBELRDF/query', method='POST')
# def run_bel_rdf_query(network_id):
#     ndex = app.config.get('ndex')
#     dict = json.load(request.body)
#     search_string = dict.get('searchString')
#     if not search_string:
#         abort(401, "requires searchString parameter in POST data")
#     wrapped_network = get_neighborhood_as_wrapped_network(ndex, network_id, search_string)
#     bel_script = wrapped_network.writeBELScript()
#     rdf = bu.bel_script_to_rdf(bel_script)
#     return rdf
