__author__ = 'dexter'

import ndex.client as nc
import bel_utils as bu
import json

ndex = nc.Ndex()
search_string = "RBL2 EP300"
# Small Corpus

#
# This is a test script using a deprecated, first-pass method of
# implementing bel2rdf from CX
#
#network_id = '55c84fa4-01b4-11e5-ac0f-000c29cb28fb'

# large Corpus
network_id = "9ea3c170-01ad-11e5-ac0f-000c29cb28fb"

cx = ndex.get_neighborhood(network_id, search_string)
bel_cx = bu.BelCx(cx)

outfile = open("test_query_cx.json", 'wt')
outfile.write(json.dumps(bel_cx.cx, indent=4))
outfile.close()

bel_script = bel_cx.to_bel_script()

outfile = open("test_query_bel.bel", 'wt')
outfile.write(bel_script)
outfile.close()

rdf = bu.bel_script_to_rdf(bel_script)

outfile = open("test_query_rdf.rdf", 'wt')
outfile.write(rdf)
outfile.close()