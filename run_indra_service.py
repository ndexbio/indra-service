__author__ = 'dexter'

import argparse
from bottle import route, run, template, default_app, request, post, abort,debug, Bottle
import ndex.client as nc
import json
import bel_utils as bu
import subprocess

parser = argparse.ArgumentParser(description='run the indra service')

parser.add_argument('--verbose', dest='verbose', action='store_const',
                    const=True, default=False,
                    help='verbose mode')
parser.add_argument('--debug', dest='debug', action='store_const',
                    const=True, default=False,
                    help='debug mode')

arg = parser.parse_args()

if arg.debug:
    print "Debug mode engaged"
    debug()

if arg.verbose:
    print "Starting indra service in verbose mode"
else:
    print "Starting indra service"

app = default_app()
app.config['verbose'] = arg.verbose

app.config['ndex'] = nc.Ndex()

app.config['engine'] = bu.BELQueryEngine()

@route('/hello/<name>')
def index(name):
    verbose_mode = app.config.get("verbose")
    if verbose_mode:
        return template('<b>This is the test method saying Hello, {{name}} verbosely</b>!', name=name)
    else:
        return template('<b>Hello {{name}}</b>!', name=name)

@route('/ruby_info')
def inf():
   out= subprocess.check_output(["gem", "list"])
   return template(out)

# GET the network summary
@route('/network/<networkId>')
def get_network_summary(networkId):
    ndex = app.config.get('ndex')
    return ndex.get_network_summary(networkId)

@route('/network/<network_id>/asBELscript/query', method='GET')
def run_bel_script_query_get(network_id):
    query_string = request.query.searchString or None
    engine = app.config.get('engine')
    bel_script = engine.bel_neighborhood_query(network_id, query_string)
    if not bel_script:
        return ''
    return bel_script

@route('/network/<network_id>/asBELscript/query', method='POST')
def run_bel_script_query(network_id):
    dict = json.load(request.body)
    query_string = dict.get('searchString')
    engine = app.config.get('engine')
    bel_script = engine.bel_neighborhood_query(network_id, query_string)
    if not bel_script:
        return ''
    return bel_script

@route('/network/<network_id>/asBELRDF/query', method='GET')
def run_bel_script_query_get(network_id):
    query_string = request.query.searchString or None
    engine = app.config.get('engine')
    bel_script = engine.bel_neighborhood_query(network_id, query_string)
    if not bel_script:
        return ''

    rdf = bu.bel_script_to_rdf(bel_script)
    return rdf

@route('/network/<network_id>/asBELRDF/query', method='POST')
def run_bel_script_query(network_id):
    dict = json.load(request.body)
    query_string = dict.get('searchString')
    engine = app.config.get('engine')
    try:
        bel_script = engine.bel_neighborhood_query(network_id, query_string)
    except RuntimeError as re:
        return {"Error": True, "message": re.message}

    if not bel_script:
        return ''
    rdf = bu.bel_script_to_rdf(bel_script)
    return rdf

##==================================================
# Deprecated, remove soon - Dexter 1/3/17
def belscript_query(network_id, search_string):
    ndex = app.config.get('ndex')

    if not search_string:
        abort(401, "requires searchString parameter")

    cx = ndex.get_neighborhood(network_id, search_string)
    bel_cx = bu.BelCx(cx)
    bel_script = bel_cx.to_bel_script()
    return bel_script

@route('/network/<network_id>/asBELscript/query_old', method='POST')
def run_bel_script_query(network_id):
    dict = json.load(request.body)
    search_string = dict.get('searchString')
    bel_script = belscript_query(network_id, search_string)
    return bel_script

@route('/network/<network_id>/asBELscript/query_old', method='GET')
def run_bel_script_query_get(network_id):
    search_string = request.query.searchString or None
    bel_script = belscript_query(network_id, search_string)
    return bel_script

@route('/network/<network_id>/asBELRDF/query_old', method='GET')
def run_bel_script_query_get(network_id):
    search_string = request.query.searchString or None
    bel_script = belscript_query(network_id, search_string)
    rdf = bu.bel_script_to_rdf(bel_script)
    return rdf

@route('/network/<network_id>/asBELRDF/query_old', method='POST')
def run_bel_script_query(network_id):
    dict = json.load(request.body)
    search_string = dict.get('searchString')
    bel_script = belscript_query(network_id, search_string)
    rdf = bu.bel_script_to_rdf(bel_script)
    return rdf


run(app, host='0.0.0.0', port=80)

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