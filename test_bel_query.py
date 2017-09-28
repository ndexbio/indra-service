__author__ = 'dexter'

import ndex.client as nc
import bel_utils as bu
import subprocess
import json

ndex = nc.Ndex()
query_string_1 = "NFKB1"
query_string_2 = "BRCA1 RBBP8"

# Small Corpus
small_corpus_id = '55c84fa4-01b4-11e5-ac0f-000c29cb28fb'

# large Corpus
large_corpus_id = "9ea3c170-01ad-11e5-ac0f-000c29cb28fb"

special_network_ids = [
    small_corpus_id,
    large_corpus_id
]

def bel_gem_installed():
    try:
        installed = subprocess.check_output(["gem", "list", "bel", "-i"])
        print("installed = " + installed)
        if installed == "true\n":
            return True
        else:
            return False
    except RuntimeError as re:
        return {"error": True, "message": re.message}

def neighborhood_query(network_id, query_string, bel_ok=False):
    try:
        bel_script = engine.bel_neighborhood_query(network_id, query_string)
        if bel_script:
            print("bel query done: "   + query_string + " on " + network_id)
            if bel_ok:
                bu.bel_script_to_rdf(bel_script)
                print("bel rdf done: "  + query_string + " on " + network_id)
            else:
                print("no bel gem, skipping rdf")
        return True
    except RuntimeError as re:
        print(re.message)
        return {"error": True, "message": re.message}

bel_ok = bel_gem_installed()
engine = bu.BELQueryEngine(special_network_ids=special_network_ids)

neighborhood_query(large_corpus_id, query_string_1, bel_ok)
# neighborhood_query(small_corpus_id, query_string_1, bel_ok)
neighborhood_query(large_corpus_id, query_string_2, bel_ok)
# neighborhood_query(small_corpus_id, query_string_2, bel_ok)

# if output:
# outfile = open("test_query_bel_new.bel", 'wt')
# outfile.write(bel_script)
# outfile.close()

# rdf = bu.bel_script_to_rdf(large_corpus_id)

# outfile = open("test_query_rdf_new.rdf", 'wt')
# outfile.write(rdf)
# outfile.close()
