__author__ = 'dexter'

import ndex.client as nc
import bel_utils as bu
import json

ndex = nc.Ndex()
query_string = "RBL2 EP300"
# Small Corpus
network_id = '55c84fa4-01b4-11e5-ac0f-000c29cb28fb'

# large Corpus
#network_id = "9ea3c170-01ad-11e5-ac0f-000c29cb28fb"

engine = bu.BELQueryEngine()

bel_script = engine.bel_neighborhood_query(network_id, query_string)

outfile = open("test_query_bel_new.bel", 'wt')
outfile.write(bel_script)
outfile.close()

rdf = bu.bel_script_to_rdf(bel_script)

outfile = open("test_query_rdf_new.rdf", 'wt')
outfile.write(rdf)
outfile.close()