__author__ = 'dexter'

# This script is called from the command line to run the enrichment server with the persisted e_sets
#
# The script reads all of the e_sets and then starts the bottle server
#
# The optional argument 'verbose' specifies verbose logging for testing
#

#
# python run_e_service.py
#
# python run_e_service.py --verbose
#

# body

import argparse
from bottle import route, run, template, default_app, request, post, abort,debug, Bottle
import ndex.client as nc
import json
import bel_utils as bu
import subprocess
import pwd
import os

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

def get_neighborhood_as_wrapped_network(ndex, network_id, search_string):
    summary = ndex.get_network_summary(network_id)
    source_format = bu.get_source_format(summary)
    if not source_format == "BEL":
        abort(401, "non-BEL network: network id " + network_id + " has source format " + str(source_format))

    ndex_network = ndex.get_neighborhood(network_id, search_string)
    return bu.NetworkWrapper(ndex_network, ['bel'])

@route('/network/<network_id>/asBELscript/query', method='POST')
def run_bel_script_query(network_id):
    ndex = app.config.get('ndex')
    dict = json.load(request.body)
    search_string = dict.get('searchString')
    if not search_string:
        abort(401, "requires searchString parameter in POST data")
    wrapped_network = get_neighborhood_as_wrapped_network(ndex, network_id, search_string)
    bel_script = wrapped_network.writeBELScript()
    return bel_script

@route('/network/<network_id>/asBELRDF/query', method='POST')
def run_bel_rdf_query(network_id):
    ndex = app.config.get('ndex')
    dict = json.load(request.body)
    search_string = dict.get('searchString')
    if not search_string:
        abort(401, "requires searchString parameter in POST data")
    wrapped_network = get_neighborhood_as_wrapped_network(ndex, network_id, search_string)
    bel_script = wrapped_network.writeBELScript()
    rdf = bu.bel_script_to_rdf(bel_script)
    return rdf

run(app, host='0.0.0.0', port=80)
