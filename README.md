# indra-service
This service provides analytic and NDEx related methods specifically required by to INDRA for Big Mechanism

# bel2rdf

A REST endpoint to return BEL RDF from queries vs BEL networks stored in NDEx:

Example POST a query:

http://bel2rdf.bigmech.ndexbio.org/network/9ea3c170-01ad-11e5-ac0f-000c29cb28fb/asBELRDF/query

Some brief documentation on the BEL RDF schema is at:

https://wiki.openbel.org/display/OBP/BEL+RDF+Model

Here is a screen shot from POSTMAN of a successful query vs. the BEL large corpus (~80 K statements)

## bel.rb

This python-based service uses the bel.rb ruby gem to convert the .bel form of BEL to the rdf form.

Work in progress: a bel.rb plugin to handle BEL encoded in the CX form used by NDEx.
 
The indra-service will be re-built to use this plugin when available.

### bel.rb from command line

To convert from .bel to RDF from the command line, use bel2rdf.rb (installed as part of bel.rb):

bel2rdf.rb --bel bel/small_corpus.bel

### bel.rb sources

https://github.com/OpenBEL/bel.rb

### Quick recipe to install bel.rb

Install ruby 2.0 if it is not installed on your machine.
Install bel plus some RDF gem dependencies.
Run with "--user-install" to install to $HOME/.gem, not system.

$ gem install bel rdf addressable uuid --user-install

Put ruby commands on your PATH.

$ PATH=$HOME/.gem/ruby/2.0.0/bin/:$PATH
