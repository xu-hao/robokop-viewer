'''
Question definition
'''

# standard modules
import os
import sys
import json
import hashlib
import warnings

# 3rd-party modules
from sqlalchemy.types import JSON
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

# our modules
from universalgraph import UniversalGraph
from knowledgegraph import KnowledgeGraph
from answer import Answer, AnswerSet, list_answersets_by_question_hash
from user import User
from setup import db, rosetta
from logging_config import logger

# robokop-rank modules
sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'robokop-rank'))
from nagaProto import ProtocopRank

# robokop-build modules
builder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'robokop-build', 'builder')
sys.path.insert(0, builder_path)
from lookup_utils import lookup_identifier

# robokop-interfaces modules
greent_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'robokop-interfaces')
sys.path.insert(0, greent_path)
from greent import node_types
from greent.graph_components import KNode
from greent.synonymizers.disease_synonymizer import synonymize


class Question(db.Model):
    '''
    Represents a question such as "What genetic condition provides protection against disease X?"

    methods:
    * answer() - a struct containing the ranked answer paths
    * cypher() - the appropriate Cypher query for the Knowledge Graph
    '''

    __tablename__ = 'question'
    id = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    natural_question = Column(String)
    notes = Column(String)
    name = Column(String)
    nodes = Column(JSON)
    edges = Column(JSON)
    name = Column(String)
    hash = Column(String)
    
    user = relationship(
        User,
        backref=backref('questions',
                        uselist=True,
                        cascade='delete,all'))

    def __init__(self, *args, **kwargs):
        '''
        keyword arguments: id, user, notes, natural_question, nodes, edges
        q = Question(kw0=value, ...)
        q = Question(struct, ...)
        '''

        # initialize all properties
        self.user_id = None
        self.id = None
        self.notes = None
        self.name = None
        self.natural_question = None
        self.name = None
        self.nodes = [] # list of nodes
        self.edges = [] # list of edges
        self.hash = None

        # apply json properties to existing attributes
        attributes = self.__dict__.keys()
        if args:
            struct = args[0]
            for key in struct:
                if key in attributes:
                    setattr(self, key, struct[key])
                else:
                    warnings.warn("JSON field {} ignored.".format(key))

        # override any json properties with the named ones
        for key in kwargs:
            if key in attributes:
                setattr(self, key, kwargs[key])
            else:
                warnings.warn("Keyword argument {} ignored.".format(key))

        # replace input node names with identifiers
        for n in self.nodes:
            if n['nodeSpecType'] == 'Named Node':
                # identifiers = lookup_identifier(n['label'], n['type'], rosetta.core)
                identifiers = [n['meta']['identifier']]
                n['identifiers'] = identifiers
            else:
                n['identifiers'] = None

        self.hash = self.compute_hash()

        db.session.add(self)
        db.session.commit()

    @staticmethod
    def dictionary_to_graph(dictionary):
        '''
        Convert struct from blackboards database to nodes and edges structs
        '''

        query = dictionary

        # convert to list of nodes (with conditions) and edges with lengths
        nodes = [dict(n, **{"id":i}) for i, n in enumerate(query)\
            if not n['nodeSpecType'] == 'Unspecified Nodes']
        edges = [dict(start=i-1, end=i, length=[query[i-1]['meta']['numNodesMin']+1, query[i-1]['meta']['numNodesMax']+1])\
            if i > 0 and query[i-1]['nodeSpecType'] == 'Unspecified Nodes'\
            else dict(start=i-1, end=i, length=[1])\
            for i, n in enumerate(query)\
            if i > 0 and not n['nodeSpecType'] == 'Unspecified Nodes']

        return nodes, edges

    @property
    def answersets(self):
        return list_answersets_by_question_hash(self.hash)

    def compute_hash(self):
        '''
        Generate an MD5 hash of the machine readable question interpretation
        i.e. the nodes and edges attributes
        '''

        json_spec = {
            "nodes":self.nodes,
            "edges":self.edges
        }
        m = hashlib.md5()
        m.update(json.dumps(json_spec).encode('utf-8'))
        return m.hexdigest()

    def __str__(self):
        return "<ROBOKOP Question id={}>".format(self.id)

    def toJSON(self):
        keys = [str(column).split('.')[-1] for column in self.__table__.columns]
        struct = {key:getattr(self, key) for key in keys}
        return struct

    def relevant_subgraph(self):
        # get the subgraph relevant to the question from the knowledge graph
        database = KnowledgeGraph()
        subgraph_networkx = database.queryToGraph(self.subgraph_with_support())
        del database
        subgraph = UniversalGraph(subgraph_networkx)
        return {"nodes":subgraph.nodes,\
            "edges":subgraph.edges}

    def answer(self):
        '''
        Answer the question.

        Returns the answer struct, something along the lines of:
        https://docs.google.com/document/d/1O6_sVSdSjgMmXacyI44JJfEVQLATagal9ydWLBgi-vE
        '''
        
        # get all subgraphs relevant to the question from the knowledge graph
        database = KnowledgeGraph()
        subgraphs = database.query(self) # list of lists of nodes with 'id' and 'bound'
        answer_set_subgraph = database.queryToGraph(self.subgraph_with_support())
        del database

        # compute scores with NAGA, export to json
        pr = ProtocopRank(answer_set_subgraph)
        score_struct, subgraphs = pr.report_scores_dict(subgraphs) # returned subgraphs are sorted by rank

        aset = AnswerSet(question_hash=self.compute_hash())
        for substruct, subgraph in zip(score_struct, subgraphs):
            graph = UniversalGraph(nodes=substruct['nodes'], edges=substruct['edges'])
            graph.merge_multiedges()
            graph.to_answer_walk(subgraph)

            answer = Answer(nodes=graph.nodes,\
                    edges=graph.edges,\
                    score=substruct['score'])
            # TODO: move node/edge details to AnswerSet
            # node_ids = [node['id'] for node in graph.nodes]
            # edge_ids = [edge['id'] for edge in graph.edges]
            # answer = Answer(nodes=node_ids,\
            #         edges=edge_ids,\
            #         score=0)
            aset += answer #substruct['score'])

        return aset

    def cypher_match_string(self):

        nodes, edges = self.nodes, self.edges

        edge_types = ['Result' for e in edges]

        node_count = len(nodes)
        edge_count = len(edges)

        # generate internal node and edge variable names
        node_names = ['n{:d}'.format(i) for i in range(node_count)]
        edge_names = ['r{0:d}{1:d}'.format(i, i+1) for i in range(edge_count)]

        node_conditions = []
        for node in nodes:
            node_conds = []
            if 'identifiers' in node and node['identifiers']:
                node_conds.append([{'prop':'id', 'val':l, 'op':'=', 'cond':True} for l in node['identifiers']])
            if 'type' in node and node['type']:
                node_conds += [[{'prop':'node_type', 'val':node['type'].replace(' ', ''), 'op':'=', 'cond':True}]]
            node_conditions += [node_conds]

        # generate MATCH command string to get paths of the appropriate size
        match_strings = ['MATCH '+'({})'.format(node_names[0])]
        match_strings += ['MATCH '+'({})-'.format(node_names[i])+'[{0}:{2}*{3}..{4}]-({1})'.format(edge_names[i], node_names[i+1], edge_types[i], edges[i]['length'][0], edges[i]['length'][-1]) for i in range(edge_count)]
        with_strings = ['WITH DISTINCT '+', '.join(node_names[:i+1]) for i in range(edge_count)]

        # generate WHERE command string to prune paths to those containing the desired nodes/node types
        node_conditions = [
            [
                [
                    {
                        k:(c[k] if k != 'cond'\
            else '' if c[k]\
                        else 'NOT ')\
                        for k in c
                    } for c in d
                ] for d in conds
            ] for conds in node_conditions
        ]
        node_cond_strings = [['('+' OR '.join(['{0}{1}.{2}{3}\'{4}\''.format(c['cond'], node_names[i], c['prop'], c['op'], c['val'])\
            for c in d])+')'\
            for d in conds]\
            for i, conds in enumerate(node_conditions)]
        where_strings = ['WHERE '+' AND '.join(c) for c in node_cond_strings]
        match_string = match_strings[0]+' '+where_strings[0]+' '+' '.join([w+' '+m+' '+d for w, m, d in zip(with_strings, match_strings[1:], where_strings[1:])])
        return match_string

    def cypher(self):
        '''
        Generate a Cypher query to extract the portion of the Knowledge Graph necessary to answer the question.

        Returns the query as a string.
        '''

        match_string = self.cypher_match_string()

        # generate internal node and edge variable names
        node_names = ['n{:d}'.format(i) for i in range(len(self.nodes))]
        edge_names = ['r{0:d}{1:d}'.format(i, i+1) for i in range(len(self.edges))]

        # define bound nodes (no edges are bound)
        node_bound = ['identifiers' in n and n['identifiers'] for n in self.nodes]
        node_bound = ["True" if b else "False" for b in node_bound]

        # add bound fields and return map
        answer_return_string = f"RETURN [{', '.join([f'{{id:{n}.id, bound:{b}}}' for n, b in zip(node_names, node_bound)])}] as nodes"

        # return subgraphs matching query
        query_string = ' '.join([match_string, answer_return_string])
        logger.info(query_string)

        # print(query_string)
        return query_string

    def subgraph_with_support(self):
        match_string = self.cypher_match_string()

        # generate internal node and edge variable names
        node_names = ['n{:d}'.format(i) for i in range(len(self.nodes))]

        collection_string = f"WITH {'+'.join([f'collect({n})' for n in node_names])} as nodes" + "\n" + \
            "UNWIND nodes as n WITH collect(distinct n) as nodes"
        support_string = 'CALL apoc.path.subgraphAll(nodes, {maxLevel:0}) YIELD relationships as rels' + "\n" +\
            "WITH [r in rels | r{.*, start:startNode(r).id, end:endNode(r).id, type:type(r), id:id(r)}] as rels, nodes"
        return_string = 'RETURN nodes, rels'
        query_string = "\n".join([match_string, collection_string, support_string, return_string])
        logger.info(query_string)

        return query_string

    def subgraph(self):
        match_string = self.cypher_match_string()

        # generate internal node and edge variable names
        node_names = ['n{:d}'.format(i) for i in range(len(self.nodes))]
        edge_names = ['r{0:d}{1:d}'.format(i, i+1) for i in range(len(self.edges))]

        # just return a list of nodes and edges
        collection_string = f"WITH {'+'.join([f'collect({e})' for e in edge_names])} as rels, {'+'.join([f'collect({n})' for n in node_names])} as nodes"
        unique_string = 'UNWIND nodes as n WITH collect(distinct n) as nodes, rels UNWIND rels as r WITH nodes, collect(distinct r) as rels'
        return_string = "\n".join([collection_string, unique_string, 'RETURN nodes, rels'])

        query_string = "\n".join([match_string, return_string])
        logger.info(query_string)

        return query_string

def list_questions():
    return db.session.query(Question).all()

def list_questions_by_hash(hash):
    return db.session.query(Question).filter(Question.hash == hash).all()

def list_questions_by_username(username, invert=False):
    if invert:
        return db.session.query(Question).join(Question.user).filter(User.username != username).all()
    else:
        return db.session.query(Question).join(Question.user).filter(User.username == username).all()

def list_questions_by_user_id(user_id, invert=False):
    if invert:
        return db.session.query(Question).filter(Question.user_id != user_id).all()
    else:
        return db.session.query(Question).filter(Question.user_id == user_id).all()

def get_question_by_id(id):
    question = db.session.query(Question).filter(Question.id == id).first()
    if not question:
        raise KeyError("No such question.")
    return question