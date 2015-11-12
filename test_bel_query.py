__author__ = 'dexter'

import ndex.client as nc
import bel_utils as bu

def get_neighborhood_as_wrapped_network(ndex, network_id, search_string):
    summary = ndex.get_network_summary(network_id)
    source_format = bu.get_source_format(summary)
    if not source_format == "BEL":
        print ("non-BEL network: network id " + network_id + " has source format " + str(source_format))
        return False
    ndex_network = ndex.get_neighborhood(network_id, search_string)
    print str(ndex_network)
    return bu.NetworkWrapper(ndex_network, ['bel'])

ndex = nc.Ndex()
search_string = "RBL2 EP300"
# Small Corpus
network_id = '55c84fa4-01b4-11e5-ac0f-000c29cb28fb'
wrapped_network = get_neighborhood_as_wrapped_network(ndex, network_id, search_string)

bel_script = wrapped_network.writeBELScript()

print bel_script

rdf = bu.bel_script_to_rdf(bel_script)

print rdf