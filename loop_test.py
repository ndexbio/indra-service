__author__ = 'aarongary'
import requests
import logging
import time
import logging
logger = logging.getLogger('status')
hdlr = logging.FileHandler('status.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

ndex_bel2rdf = 'http://ec2-54-212-209-240.us-west-2.compute.amazonaws.com:8011'

def get_status():
    url = ndex_bel2rdf + '/status?memsize=452181536'

    resp = requests.get(url)

    stat_results = resp.json()

    return stat_results

for i in range(1,4000):
    stat_results = get_status()
    rss = stat_results.get('rss')
    if rss is not None:
        logger.info(rss)
    else:
        logger.info('RSS WAS NONE!!!')


