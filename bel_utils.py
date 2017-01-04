"""
Created on Sun Oct  5 11:10:59 2014

@author: Dexter Pratt
"""
import sys
import networkx as nx
import re
import StringIO
import subprocess
import os
import copy
import ndex.client as nc
import time

def get_source_format(network_summary):
    for prop in network_summary.get("properties"):
        name = prop.get("predicateString")
        value = prop.get("value")
        if name and name == "sourceFormat":
            return value
    return False

# Convert NDEx property graph json to a trivial networkx network
def ndexPropertyGraphNetworkToNetworkX(ndexPropertyGraphNetwork):
        g = nx.MultiDiGraph()
        for node in ndexPropertyGraphNetwork['nodes'].values():
            g.add_node(node['id'])
        for edge in ndexPropertyGraphNetwork['edges'].values():
            g.add_edge(edge['subjectId'], edge['objectId'])
        return g

# This is specific to summarizing a BEL network. 
# Need to generalize
def stripPrefixes(input):
    st = input.lower()
    if st.startswith('bel:'):
        return input[4:len(input)]
    elif st.startswith('hgnc:'):
         return input[5:len(input)]
    else:
         return input

# This is BEL specific, since BEL is the only current user of funciton terms
def getFunctionAbbreviation(input):
    st = input.lower()
    fl = stripPrefixes(st)
    if fl == "abundance":
        return "a"
    elif fl == "biological_process":
        return "bp"
    elif fl ==  "catalytic_activity":
        return "cat"
    elif fl ==  "complex_abundance":
        return "complex"
    elif fl ==  "pathology":
        return "path"
    elif fl ==  "peptidase_activity":
        return "pep"
    elif fl ==  "protein_abundance":
        return "p"
    elif fl ==  "rna_abundance":
        return "r"
    elif fl ==  "protein_modification":
        return "pmod"
    elif fl ==  "transcriptional_activity":
        return "tscript"
    elif fl ==  "molecular_activity":
        return "act"
    elif fl ==  "degradation":
        return "deg"
    elif fl ==  "kinase_activity":
        return "kin"
    elif fl ==  "substitution":
        return "sub"
    else:
        return fl

def getFunctionFull(input):
    st = input.lower()
    fl = stripPrefixes(st)
    if fl == "abundance":
        return "abundance"
    elif fl == "biologicalprocess":
        return "biologicalProcess"
    elif fl ==  "catalyticactivity":
        return "catalyticActivity"
    elif fl ==  "complexabundance":
        return "complexAbundance"
    elif fl ==  "pathology":
        return "pathology"
    elif fl ==  "peptidaseactivity":
        return "peptidaseActivity"
    elif fl ==  "proteinabundance":
        return "proteinAbundance"
    elif fl ==  "rnaabundance":
        return "rnaAbundance"
    elif fl ==  "proteinmodification":
        return "proteinModification"
    elif fl ==  "transcriptionalactivity":
        return "transcriptionalActivity"
    elif fl ==  "molecularactivity":
        return "molecularActivity"
    elif fl ==  "degradation":
        return "degradation"
    elif fl ==  "phosphataseactivity":
        return "phosphataseActivity"
    elif fl ==  "kinaseactivity":
        return "kinaseActivity"
    elif fl ==  "cellsecretion":
        return "cellSecretion"
    elif fl ==  "substitution":
        return "substitution"
    elif fl == "gtpboundactivity":
        return "gtpBoundActivity"
    elif fl == "cellsurfaceexpression":
        return "cellSurfaceExpression"
    elif fl == "micrornaabundance":
        fl = "microRnaAbundance"
    else:
        return fl

def getPredicateFull(p):
    if p == 'INCREASES':
        return 'increases'
    elif p == 'DECREASES':
        return 'decreases'
    elif p == 'DIRECTLY_INCREASES':
        return 'directlyIncreases'
    elif p == 'DIRECTLY_DECREASES':
        return 'directlyDecreases'
    else:
        return p

def write_utf(output,string):
    output.write(string.encode('utf8','replace'))

#BEL2RDFPATH = "/Users/dexter/.gem/ruby/2.0.0/gems/bel-1.0.1/bin/bel2rdf"

BEL2RDFPATH = "/Users/dexter/.gem/ruby/2.0.0/bin/bel2rdf"

#RUBYPATH = "/Users/dexter/.gem/ruby/2.0.0/bin/ruby"

RUBYPATH = "/usr/local/bin/ruby"

def bel_script_to_rdf(bel_script):
    with open('tmp.bel', 'wt') as fh:
        fh.write(bel_script)

    bel2rdf_cmd = "bel bel2rdf --bel tmp.bel > tmp.rdf"

    #bel2rdf_cmd = "%s %s --bel tmp.bel > tmp.rdf" % (RUBYPATH, BEL2RDFPATH)

    print "converting BELscript to BEL RDF:  %s" % bel2rdf_cmd

    # print str(bel2rdf_cmd.split(' '))

    DEVNULL = open(os.devnull, 'wb')

    with open('tmp.rdf', 'wt') as fh:
        start_time = time.time()
        subprocess.call(bel2rdf_cmd.split(' '), stdout=fh, stderr=DEVNULL)
        end_time = time.time()
        print "converted in %s" % ((end_time - start_time))

    # change formatting from original bel2rdf output
    with open('tmp.rdf', 'rt') as fh:
        rdf = fh.read()
    res = re.findall(r'_:([^ ]+)', rdf)
    for r in res:
        rdf = rdf.replace(r, r.replace('-', ''))
    return rdf

class BelCx:
    # Note that this class does NOT handle:
    # - reified edges
    # - translocations
    # - "None" modifications
    # - direct links from citations to edges. All edges are connected as: citation -> support -> edge
    # - supports or citations for nodes (ie. single term statements...)
    #
    def __init__(self, cx, verbose=False):
        self.cx = cx
        self.unused_cx = []
        self.citation_map = {}          # citation ids -> citations
        self.support_map = {}           # support ids -> supports
        self.function_term_map = {}     # node ids - function terms
        self.edge_map = {}              # edge ids -> edges  (which point to nodes)
        self.edge_attribute_map = {}
        self.context = {}               # context object for BEL namespaces
        self.node_label_map = {}        # node ids -> node labels
        self.node_to_upstream_edge_map = {}
        self.node_to_downstream_edge_map = {}
        self.support_to_edge_map= {}    # support ids -> edge id lists
        self.citation_to_support_map = {} # citation_ids -> support id lists
        self.unused_cx = []
        self.annotation_names = []

        for fragment in cx:
            if '@context' in fragment:
                elements = fragment['@context']
                self.context =  elements[0]
            # elif 'nodes' in fragment:
            #     for node in fragment.get('nodes'):
            #         id = node.get('@id')
            #         name = node['n'] if 'n' in node else None
            #         if name:
            #             self.add_node(id, name=name)
            #         else:
            #             self.add_node(id)
            #         represents = node.get('r') if 'r' in node else None
            #         if represents:
            #             self.node.get(id)['represents'] = represents

            elif 'edges' in fragment:
                for edge in fragment.get('edges'):
                    id = edge.get('@id')
                    interaction = edge['i'] if 'i' in edge else None
                    s = edge['s']
                    t = edge['t']
                    self.edge_map[id] = (s, t, interaction)
                    if s in self.node_to_downstream_edge_map:
                        source_edges = self.node_to_downstream_edge_map[s]
                    else:
                        source_edges = []
                    source_edges.append(id)
                    self.node_to_downstream_edge_map[s] = list(set(source_edges))

                    if t in self.node_to_upstream_edge_map:
                        target_edges = self.node_to_upstream_edge_map[t]
                    else:
                        target_edges = []
                    target_edges.append(id)
                    self.node_to_upstream_edge_map[t] = list(set(target_edges))

            elif 'functionTerms' in fragment:
                for function_term in fragment['functionTerms']:
                    self.node_label_map[function_term["po"]] = self.get_label_from_term(function_term)
                    self.function_term_map[function_term["po"]] = function_term

            elif 'citations' in fragment:
                for citation in fragment['citations']:
                    attributes = copy.deepcopy(citation)
                    attributes.pop("@id")
                    self.citation_map[citation["@id"]] = attributes

            elif 'supports' in fragment:
                for support in fragment['supports']:
                    attributes = copy.deepcopy(support)
                    attributes.pop("@id")
                    support_id = support["@id"]
                    self.support_map[support_id] = attributes
                    citation_id = support['citation']
                    if citation_id in self.citation_to_support_map:
                        citation_supports = self.citation_to_support_map[citation_id]
                    else:
                        citation_supports = []
                    citation_supports.append(support_id)
                    self.citation_to_support_map[citation_id] = list(set(citation_supports))

            elif 'edgeSupports' in fragment:
                for edge_support in fragment['edgeSupports']:
                    for support_id in edge_support["supports"]:
                        if support_id in self.support_to_edge_map:
                            edge_list = self.support_to_edge_map[support_id]
                            edge_list = list(set(edge_list + edge_support.get('po')))
                        else:
                            edge_list = edge_support.get('po')
                        self.support_to_edge_map[support_id] = edge_list

            else:
                self.unused_cx.append(fragment)

        for name,uri in self.context.iteritems():
            if uri.endswith('.belanno'):
                self.annotation_names.append(name)

        for fragment in self.cx:
            if 'edgeAttributes' in fragment:
                count = 0
                for edge_attribute in fragment['edgeAttributes']:
                    count = count + 1
                    if verbose and count % 100 == 0:
                        print str(count)

                    name = edge_attribute['n']
                    if name in self.annotation_names:
                        edge_id = edge_attribute['po']
                        if edge_id in self.edge_attribute_map:
                            attributes = self.edge_attribute_map[edge_id]
                        else:
                            attributes = {}
                        value = edge_attribute['v']
                        attributes[name] = value
                        self.edge_attribute_map[edge_id] = attributes

    def get_label_from_term(self, term):
        if isinstance(term, dict):
            function = term["f"].lower()
            if function.startswith('bel:'):
                function = function[4:len(function)]
            arg_labels = []
            for arg in term['args']:
                arg_label = self.get_label_from_term(arg)
                arg_labels.append(arg_label)
            return "%s(%s)" % (function, ",".join(arg_labels))
        return str(term)

    def get_statement_from_edge(self, edge_id):
        source_node_id, target_node_id, interaction = self.edge_map[edge_id]
        if interaction.startswith('bel:'):
            interaction = interaction[4:len(interaction)]
        if source_node_id in self.node_label_map and target_node_id in self.node_label_map:
            source_label = self.node_label_map[source_node_id]
            target_label = self.node_label_map[target_node_id]
            return "%s %s %s" % (source_label, interaction, target_label)
        else:
            print "either %s or %s node_ids are not in node_label_map" % (source_node_id, target_node_id)
            return False

    def get_nodes_referencing_term_strings(self, query_strings):
        node_ids = []
        strings = []
        for string in query_strings:
            strings.append(string.lower())
        for node_id, function_term in self.function_term_map.iteritems():
            if self.term_references_strings(function_term, strings):
                node_ids.append(node_id)
        return node_ids

    def term_references_strings(self, term, strings):
        # looking for a string argument that matches one of the strings
        # return as soon as one is found
        if isinstance(term, basestring):
            components = term.split(":")
            if len(components) > 1:
                string = components[1].lower()
                if string in strings:
                    return True

        if isinstance(term, dict) and 'args' in term:
            for arg in term['args']:
                if self.term_references_strings(arg, strings):
                    return True

        return False

    def get_edges_adjacent_to_nodes(self, node_ids):
        edge_ids = []
        for node_id in node_ids:
            edge_ids = edge_ids + self.get_edges_adjacent_to_node(node_id)
        return list(set(edge_ids))

    def get_edges_adjacent_to_node(self, node_id):
        edge_ids = []
        if node_id in self.node_to_upstream_edge_map:
            edge_ids = edge_ids + self.node_to_upstream_edge_map[node_id]
        if node_id in self.node_to_downstream_edge_map:
            edge_ids = edge_ids + self.node_to_downstream_edge_map[node_id]
        return edge_ids

    def get_supports_for_edges(self, query_edge_ids):
        support_ids = []
        for support_id, edge_ids in self.support_to_edge_map.iteritems():
            for edge_id in edge_ids:
                if edge_id in query_edge_ids:
                    support_ids.append(support_id)
                    break
        return list(set(support_ids))

    def get_citations_for_supports(self, query_support_ids):
        citation_ids = []
        for citation_id, support_ids in self.citation_to_support_map.iteritems():
            for support_id in support_ids:
                if support_id in query_support_ids:
                    citation_ids.append(citation_id)
                    break
        return list(set(citation_ids))

    def to_bel_script(self, citation_filter_ids=None, support_filter_ids=None, edge_filter_ids=None, use_annotations=False):
        output = StringIO.StringIO()

        write_utf(output,'#Properties section\n')
        write_utf(output,'SET DOCUMENT Name = "NDEx query result in BEL script"\n')
        write_utf(output,'SET DOCUMENT Description = "Query with ndex-python-client, one step neighborhood"\n')

        # In CX, the namespaces and annotations are in the @context aspect
        #
        #  output definitions in header
        write_utf(output,'\n# Definitions Section\n')

        # output namespaces
        for prefix,uri in self.context.iteritems():
            if uri.endswith('.belns'):
                write_utf(output,'DEFINE NAMESPACE %s AS URL "%s"\n' % (prefix,uri))

        # output annotations
        for prefix,uri in self.context.iteritems():
            if uri.endswith('.belanno'):
                write_utf(output,'DEFINE ANNOTATION %s AS URL "%s"\n' % (prefix,uri))

        # output BEL statements:
        # by citation
        #  by supports for citation
        #    by edges (statments) for supports
        write_utf(output,'\n#Statements section\n')

        for citation_id, citation in self.citation_map.iteritems():
            if citation_filter_ids and citation_id not in citation_filter_ids:
                continue
            if citation_id not in self.citation_to_support_map:
                continue
            # Start a group for the citation
            write_utf(output,'\nSET STATEMENT_GROUP = "Group %s"\n' % citation['dc:identifier'])

            # BEL citations are required to have titles and identifiers
            # we determine a type which is either PubMed or N/A
            try:
                citation_title = citation['dc:title']
                citation_identifier = citation['dc:identifier']
                citation_components = citation_identifier.split(':')
                if citation_components[0]=='pmid':
                    citation_type = 'PubMed'
                    citation_identifier = citation_components[1]
                else:
                    citation_type = 'N/A'
                    citation_identifier = citation['dc:identifier']
                write_utf(output,('SET Citation = {"%s","%s","%s"}\n\n' % (citation_type, citation_title, citation_identifier)))
            except KeyError:
                write_utf(output,'SET Citation = {"","",""}\n\n')

            # Iterate by evidence within each citation, using CX supports that point to the citation
            support_ids = []
            if support_filter_ids:
                for support_id in self.citation_to_support_map[citation_id]:
                    if support_id in support_filter_ids:
                        support_ids.append(support_id)
            else:
                support_ids = self.citation_to_support_map[citation_id]

            for support_id in support_ids:
                if support_id in self.support_to_edge_map:
                    support = self.support_map[support_id]
                    support_text = support['text'].replace('"','').replace('\n',' ')
                    write_utf(output,('\nSET Evidence = "%s"\n\n' % support_text))
                    edge_list = self.support_to_edge_map[support_id]
                    # output BEL statements
                    for edge_id in edge_list:
                        if edge_filter_ids and edge_id not in edge_filter_ids:
                            continue

                        statement_string = self.get_statement_from_edge(edge_id)

                        if statement_string: # ok, output this statement with annotations, if any
                            annotations = {}
                            if use_annotations and edge_id in self.edge_attribute_map:
                                annotations = self.edge_attribute_map[edge_id]

                            for name, value in annotations.iteritems():
                                write_utf(output, ('SET %s = %s\n' % (name, value)))

                            write_utf(output,"%s\n" % statement_string)

                            for name, _ in annotations.iteritems():
                                write_utf(output, ('UNSET %s\n' % (name)))

            write_utf(output,'\nUNSET STATEMENT_GROUP\n')

        return output.getvalue()

class BELQueryEngine:
    def __init__(self, special_network_ids=None):
        self.network_cache = {}
        if special_network_ids:
            self.special_network_ids = special_network_ids
        else:
            self.special_network_ids = []

        self.ndex = nc.Ndex()
        for network_id in self.special_network_ids:
            self.bel_cx_from_ndex(network_id)


    def bel_cx_from_ndex(self, network_id):
        start_time = time.time()
        response = self.ndex.get_network_as_cx_stream(network_id)
        end_time = time.time()
        cx = response.json()
        print "received CX in %s " % (end_time - start_time)

        start_time = time.time()
        bel_cx = BelCx(cx)
        end_time = time.time()
        print "created BelCx object in %s"  % (end_time - start_time)

        self.network_cache[network_id] = bel_cx
        return bel_cx

    def bel_neighborhood_query(self, network_id, query_string, verbose=False, use_annotations=False):
        if network_id in self.network_cache:
            # TODO check if cache is valid
            bel_cx = self.network_cache[network_id]
        else:
            bel_cx = self.bel_cx_from_ndex(network_id)
        # find the query nodes
        query_terms = query_string.split()
        query_node_ids = bel_cx.get_nodes_referencing_term_strings(query_terms)
        print "found %s nodes for query %s" % (len(query_node_ids), query_string)
        if verbose:
            for node_id in query_node_ids:
                ft = bel_cx.function_term_map[node_id]
                print "  %s" % bel_cx.get_label_from_term(ft)

        # find the search result edge ids and node ids
        edge_ids = bel_cx.get_edges_adjacent_to_nodes(query_node_ids)
        print "found %s adjacent edges" % (len(edge_ids))
        if verbose:
            for edge_id in edge_ids:
                print bel_cx.get_statement_from_edge(edge_id)

        # find the support ids for the edges
        support_ids = bel_cx.get_supports_for_edges(edge_ids)
        print "found %s supports for the edges" % (len(support_ids))
        if verbose:
            for support_id in support_ids:
                support = bel_cx.support_map[support_id]
                print "--------"
                print support.get('text')

        # find the citation ids for the supports
        citation_ids = bel_cx.get_citations_for_supports(support_ids)
        print "found %s citations for the supports" % (len(citation_ids))
        if verbose:
            for citation_id in citation_ids:
                citation = bel_cx.citation_map[citation_id]
                print citation['dc:title']

        # create BELscript from network while filtering on the citation, support, edge, and node ids
        return bel_cx.to_bel_script(citation_filter_ids=citation_ids, support_filter_ids=support_ids, edge_filter_ids=edge_ids, use_annotations=use_annotations)


#=======================================================

class NetworkWrapper:
    def __init__(self, ndexNetwork, removeNamespace=None):
        self.network = ndexNetwork
        self.supportToEdgeMap = {}
        self.citationToSupportMap = {}
        self.nodeLabelMap = {}
        self.termLabelMap = {}

        for nodeId, node in ndexNetwork['nodes'].iteritems():
            nodeLabel = self.getNodeLabel(node)
            removeNode = False
            for rn in removeNamespace:
                if nodeLabel.find(rn)!=-1:
                    removeNode = True

            if removeNode==False:
                self.nodeLabelMap[int(nodeId)] = self.getNodeLabel(node)

        for edge in ndexNetwork['edges'].values():
            for supportId in edge['supportIds']:
                supports = ndexNetwork['supports']
                support = supports[str(supportId)]
                if supportId in self.supportToEdgeMap:
                    edgeList = self.supportToEdgeMap[supportId]
                else:
                    edgeList = []
                edgeList.append(edge)
                self.supportToEdgeMap[supportId] = edgeList

        for supportId in self.supportToEdgeMap.keys():
            support = ndexNetwork['supports'][str(supportId)]
            citationId = support['citationId']
            if citationId in self.citationToSupportMap:
                supportIdList = self.citationToSupportMap[citationId]
            else:
                supportIdList = []
            supportIdList.append(supportId)
            self.citationToSupportMap[citationId] = supportIdList

    def getEdgeLabel(self, edge):
        subjectLabel = "missing"
        objectLabel = "missing"
        predicateLabel = "missing"
        subjectId = edge['subjectId']
        objectId = edge['objectId']
        if subjectId in self.nodeLabelMap:
            subjectLabel = self.nodeLabelMap[subjectId]
        if objectId in self.nodeLabelMap:
            objectLabel = self.nodeLabelMap[objectId]
        predicateId = edge['predicateId']
        predicateLabel = stripPrefixes(self.getTermLabel(predicateId))
        predicateLabel = getPredicateFull(predicateLabel)
        label = "%s %s %s" % (subjectLabel, predicateLabel, objectLabel)
        return label

    def getNodeLabel(self, node):
        if 'name' in node and node['name']:
            return node['name']

        elif 'represents' in node:
            return self.getTermLabel(node['represents'])

        else:
            return "node %s" % (node['id'])

    def getTermById(self, termId):
        termIdStr = str(termId)
        if termIdStr in self.network['baseTerms']:
            return self.network['baseTerms'][termIdStr]
        elif termIdStr in self.network['functionTerms']:
            return self.network['functionTerms'][termIdStr]
        elif termIdStr in self.network['reifiedEdgeTerms']:
            return self.network['reifiedEdgeTerms'][termIdStr]
        else:
            return None

    def determineTermType(self, term):
        if 'name' in term and 'namespaceId' in term:
            return 'baseterm'
        elif 'functionTermId' in term and 'parameterIds' in term:
            return 'functionterm'
        else:
            return 'reifiededgeterm'

    def getTermLabel(self, termId):
        if termId in self.termLabelMap:
            return self.termLabelMap[termId]
        else:
            label = "error"
            term = self.getTermById(termId)
            type = self.determineTermType(term)
            if type == "baseterm":
                name = term['name']
                if 'namespaceId' in term and term['namespaceId']:
                    namespaceId = term['namespaceId']
                    #namespace = self.network['namespaces'][namespaceId]
                    try:
                        namespace = self.network['namespaces'][str(namespaceId)]
                    except KeyError:
                        namespace = None

                    if namespace:
                        if namespace['prefix']:
                            if namespace['prefix']!='BEL':
                                if re.search('[^a-zA-Z0-9]',name) != None:
                                    name = '"'+name+'"'
                                label = "%s:%s" % (namespace['prefix'], name)
                            else:
                                label = name
                        elif namespace['uri']:
                            label = "%s%s" % (namespace['uri'], name)
                        else:
                            label = name
                    else:
                        label = name
                else:
                    label = name

            elif type == "functionterm":
                functionTermId = term['functionTermId']
                functionLabel = self.getTermLabel(functionTermId)
                #functionLabel = getFunctionAbbreviation(functionLabel)
                functionLabel = getFunctionFull(functionLabel)
                parameterLabels = []
                for parameterId in term['parameterIds']:
                    parameterLabel = self.getTermLabel(parameterId)
                    parameterLabels.append(parameterLabel)
                label = "%s(%s)" % (functionLabel, ",".join(parameterLabels))

            elif type == "reifiededgeterm":
                edgeId = term['edgeId']
                edges = self.network['edges']
                if edgeId in edges:
                    reifiedEdge = edges[edgeId]
                    label = "(%s)" % (self.getEdgeLabel(reifiedEdge))
                else:
                    label = "(reifiedEdge: %s)" % (edgeId)

            else:
                label = "term: %s" % (termId)

            self.termLabelMap[termId] = label
            return label

    def write_utf(self,output,string):
        output.write(string.encode('utf8','replace'))
        #output.write(string)
        
    def writeBELScript(self, fileName = None):
        output = StringIO.StringIO()
       
        self.write_utf(output,'#Properties section\n')
        self.write_utf(output,'SET DOCUMENT Name = "NDEx query result in BEL script"\n')
        self.write_utf(output,'SET DOCUMENT Description = "Query with ndex-python-client, one step neighborhood"\n')

        
        # Print definitions in header
        self.write_utf(output,'\n# Definitions Section\n')

        # Print namespaces
        for _,ns in self.network['namespaces'].iteritems():
            if ns['uri'].endswith('.belns'):
                self.write_utf(output,'DEFINE NAMESPACE %s AS URL "%s"\n' % (ns['prefix'],ns['uri']))
        
        # Print annotations
        for _,ann in self.network['namespaces'].iteritems():
            if ann['uri'].endswith('.belanno'):
                self.write_utf(output,'DEFINE ANNOTATION %s AS URL "%s"\n' % (ann['prefix'],ann['uri']))

        # Print BEL statements
        self.write_utf(output,'\n#Statements section\n')
    
        # Iterate by citation
        for citationId, supportIdList in self.citationToSupportMap.iteritems():
            # Start a group for each citation
            self.write_utf(output,'\nSET STATEMENT_GROUP = "Group %d"\n' % citationId)
            try:
                citation = self.network['citations'][str(citationId)]
                citation_title = citation['title']
                citation_terms = citation['identifier'].split(':')
                if citation_terms[0]=='pmid':
                    citation_type = 'PubMed'
                    citation_id = citation_terms[1]
                else:
                    citation_type = 'N/A'
                    citation_id = citation['identifier']
                self.write_utf(output,('SET Citation = {"%s","%s","%s"}\n' % (citation_type, citation_title, citation_id)))    
            except KeyError:
                self.write_utf(output,'SET Citation = {"","",""}\n')
           
            # Iterate by evidence within each citation
            for supportId in supportIdList:
                support = self.network['supports'][str(supportId)]
                supportText = support['text'].replace('"','').replace('\n',' ')
                self.write_utf(output,('\nSET Evidence = "%s"\n' % supportText))
                edgeList = self.supportToEdgeMap[supportId]
                # Print BEL statements 
                for edge in edgeList:
                    outstr = self.getEdgeLabel(edge)
                    if outstr.find('missing') != -1:
                        print "missing: " + outstr
                        continue

                    # Generate valid translocation statements - not used
                    #outstr = re.sub(r'GOCCACC:GO:(\d+),GOCCACC:GO:(\d+)',r'fromLoc(GOCCACC:\1),toLoc(GOCCACC:\2)',outstr)

                    # Reified edges not handled
                    if outstr.find('reifiedEdge') != -1:
                        print "reifiedEdge: " + outstr
                        continue

                    # Translocation not handled
                    if outstr.find('translocation') != -1:
                        print "translocation: " + outstr
                        continue

                    # 'None' modifiers not handled
                    if outstr.find('None') != -1:
                        print "None modifier: " + outstr
                        continue

                    # ok, output this statement
                    self.write_utf(output,"%s\n" % outstr)


            self.write_utf(output,'\nUNSET STATEMENT_GROUP\n')

        retstr = output.getvalue()
        if fileName:
            outfile = open(fileName, 'wt')
            outfile.write(retstr)
            outfile.close()

        output.close()
        return retstr

    def writeSummary(self, fileName = None):
        if fileName:
            output = open(fileName, 'w')
        else:
            output = sys.stdout
            
        for citationId, supportIdList in self.citationToSupportMap.iteritems():
            citations = self.network['citations']
            citation = citations[str(citationId)]
            citationId = citation['identifier']
            # Write Citation
            output.write("\n=========================================================================\n")
            output.write("        Citation: %s\n" % (citationId))
            output.write("=========================================================================\n\n")

            for supportId in supportIdList:
                support = self.network['supports'][str(supportId)]
                # Write Support
                output.write("_______________________________\n")
                output.write(("Evidence: %s\n\n" % support['text']).encode('utf8','replace'))

                edgeList = self.supportToEdgeMap[supportId]
                for edge in edgeList:
                    # Write Edge
                    output.write("       %s\n" % self.getEdgeLabel(edge))
                    for pv in edge['properties']:
                        output.write("                %s: %s\n" % (pv['predicateString'], pv['value']))

        if fileName:
            output.close()


