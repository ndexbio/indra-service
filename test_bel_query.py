__author__ = 'dexter'

import ndex.client as nc
import bel_utils as bu
import json

ndex = nc.Ndex()
query_string_1 = "RBL2 EP300"
query_string_2 = "BRCA1 RBBP8"

# Small Corpus
small_corpus_id = '55c84fa4-01b4-11e5-ac0f-000c29cb28fb'

# large Corpus
large_corpus_id = "9ea3c170-01ad-11e5-ac0f-000c29cb28fb"

special_network_ids = [
    small_corpus_id,
    large_corpus_id
]

def neighborhood_query(network_id, query_string):
    try:
        return engine.bel_neighborhood_query(network_id, query_string)
    except RuntimeError as re:
        print(re.message)
        return {"error": True, "message": re.message}

engine = bu.BELQueryEngine(special_network_ids=special_network_ids)

large_corpus_bel_script_1 = neighborhood_query(small_corpus_id, query_string_1)
small_corpus_bel_script_1 = neighborhood_query(small_corpus_id, query_string_1)
large_corpus_bel_script_2 = neighborhood_query(large_corpus_id, query_string_2)
small_corpus_bel_script_2 = neighborhood_query(small_corpus_id, query_string_2)

# if output:
# outfile = open("test_query_bel_new.bel", 'wt')
# outfile.write(bel_script)
# outfile.close()

# rdf = bu.bel_script_to_rdf(large_corpus_id)

# outfile = open("test_query_rdf_new.rdf", 'wt')
# outfile.write(rdf)
# outfile.close()
