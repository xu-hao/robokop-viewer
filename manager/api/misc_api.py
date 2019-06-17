#!/usr/bin/env python

"""ROBOKOP manager layer"""

import os
import sys
import json
import time

import requests
from flask import request, Response
from flask_restful import Resource, abort

from manager.setup import app, api
from manager.logging_config import logger


concept_map = {}
try:
    with app.open_resource('api/concept_map.json') as map_file:
        concept_map = json.load(map_file)
        logger.warning('Successfully read concept_map.json')
except Exception as e:
    logger.error(
        'misc_api.py:: Could not '
        f'find/read concept_map.json - {e}')

class Concepts(Resource):
    def get(self):
        """
        Get known biomedical concepts
        ---
        tags: [util]
        responses:
            200:
                description: concepts
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """
        r = requests.get(f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/concepts")
        concepts = r.json()
        bad_concepts =['NAME.DISEASE', 'NAME.PHENOTYPE', 'NAME.DRUG']
        concepts = [c for c in concepts if not c in bad_concepts]
        concepts.sort()

        return concepts

api.add_resource(Concepts, '/concepts/')


class Omnicorp(Resource):
    def get(self, id1, id2):
        """
        Get publications for a pair of identifiers
        ---
        tags: [util]
        parameters:
          - in: path
            name: id1
            description: "curie of first term"
            schema:
                type: string
            required: true
            default: "MONDO:0005737"
          - in: path
            name: id2
            description: "curie of second term"
            schema:
                type: string
            required: true
            default: "HGNC:7897"
        responses:
            200:
                description: publications
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """

        r = requests.get(f"http://{os.environ['RANKER_HOST']}:{os.environ['RANKER_PORT']}/api/omnicorp/{id1}/{id2}")
        return r.json()

api.add_resource(Omnicorp, '/omnicorp/<id1>/<id2>')


class Omnicorp1(Resource):
    def get(self, id1):
        """
        Get publications for one identifier
        ---
        tags: [util]
        parameters:
          - in: path
            name: id1
            description: "curie of first term"
            schema:
                type: string
            required: true
            default: "MONDO:0005737"
        responses:
            200:
                description: publications
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """

        r = requests.get(f"http://{os.environ['RANKER_HOST']}:{os.environ['RANKER_PORT']}/api/omnicorp/{id1}")
        return r.json()

api.add_resource(Omnicorp1, '/omnicorp/<id1>')


class Connections(Resource):
    def get(self):
        """
        Get possible connections between biomedical concepts
        ---
        tags: [util]
        responses:
            200:
                description: concepts
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """
        r = requests.get(f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/connections")
        connections = r.json()

        return connections

api.add_resource(Connections, '/connections/')
    
class Operations(Resource):
    def get(self):
        """
        Get a machine readable list of all connections between biomedical concepts with sources
        ---
        tags: [util]
        responses:
            200:
                description: concepts
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """
        r = requests.get(f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/operations")
        operations = r.json()

        return operations

api.add_resource(Operations, '/operations/')

class Predicates(Resource):
    def get(self):
        """
        Get a machine readable list of all predicates for a source-target pair
        ---
        tags: [util]
        responses:
            200:
                description: predicates
                content:
                    application/json:
                        schema:
                            type: object
        """
        get_url = f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/predicates"
        r = requests.get(get_url)
        operations = r.json()

        return operations

    def post(self):
        """
        Force update of source-target predicate list from neo4j database
        ---
        tags: [util]
        responses:
            200:
                description: "Here's your updated source-target predicate list"
                content:
                    application/json:
                        schema:
                            type: object
            400:
                description: "Something went wrong. Old predicate list will be retained"
                content:
                    text/plain:
                        schema:
                            type: string
        """
        post_url = f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/predicates"
        logger.debug(f'Predicates:post:: Trying to post to: {post_url}')
        response = requests.post(post_url)
        return Response(response.content, response.status_code)

api.add_resource(Predicates, '/predicates/')

class Properties(Resource):
    def get(self):
        """
        Get a machine readable list of potential node proeprties in the knowledge graph
        ---
        tags: [util]
        responses:
            200:
                description: concepts
                content:
                    application/json:
        """
        r = requests.get(f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/properties")
        props = r.json()

        return props

api.add_resource(Properties, '/properties/')

class Pubmed(Resource):
    def get(self, pmid):
        """
        Get pubmed publication from id
        ---
        tags: [util]
        parameters:
          - in: path
            name: pmid
            description: ID of pubmed publication
            schema:
                type: string
            required: true
            default: "10924274"
        responses:
            200:
                description: pubmed publication
                content:
                    application/json:
        """
        
        # logger.debug(f'Fetching pubmed info for pmid {pmid}')

        pubmed_redis_client = redis.Redis(
            host=os.environ['PUBMED_CACHE_HOST'],
            port=os.environ['PUBMED_CACHE_PORT'],
            db=os.environ['PUBMED_CACHE_DB'],
            password=os.environ['PUBMED_CACHE_PASSWORD'])

        pubmed_cache_key = f'robokop_pubmed_cache_{pmid}'
        pm_string = pubmed_redis_client.get(pubmed_cache_key)
        if pm_string is None:
            # logger.debug(f'Pubmed info for {pmid} not found in cache. Fetching from pubmed')

            result = fetch_pubmed_info.apply_async(
                args=[pmid, pubmed_cache_key]
            )
            
            try:
                task_status = result.get() # Blocking call to wait for task completion
            except (redis.exceptions.InvalidResponse, redis.exceptions.ConnectionError) as err:
                return "Celery results is bad: " + str(err), 500

            if task_status != 'cached':
                return task_status, 500
            
            pm_string = pubmed_redis_client.get(pubmed_cache_key)
            if pm_string is None:
                return 'Pubmed info could not be found', 500
        
        pubmed_info = json.loads(pm_string)
        # logger.debug(f'Pubmed info for {pmid} found in cache.')
        
        return pubmed_info, 200

api.add_resource(Pubmed, '/pubmed/<pmid>')

class Search(Resource):
    def get(self, term, category):
        """
        Look up biomedical search term using bionames service
        ---
        tags: [util]
        parameters:
          - in: path
            name: term
            description: "biomedical term"
            schema:
                type: string
            required: true
            example: ebola
          - in: path
            name: category
            description: "biomedical concept category"
            schema:
                type: string
            required: true
            example: disease
        responses:
            200:
                description: "biomedical identifiers"
                content:
                    application/json:
                        schema:
                            type: array
                            items:
                                type: string
        """
        if category not in concept_map:
            abort(400, error_message=f'Unsupported category: {category} provided')
        bionames = concept_map[category]
        
        if not bionames: # No matching biolink name for this category
            return []
        
        results = []
        error_status = {'isError': False}
        for bioname in bionames:
            url = f"https://bionames.renci.org/lookup/{term}/{bioname}/"
            r = requests.get(url)
            if r.ok:
                all_results = r.json()
                for r in all_results:
                    if not 'id' in r:
                        continue
                    if 'label' in r:
                        r['label'] = r['label'] or r['id']
                    elif 'desc' in r:
                        r['label'] = r['desc'] or r['id']
                        r.pop('desc')
                    else:
                        continue
                    results.append(r)
            else:
                error_status['isError'] = True
                error_status['code'] = r.status_code

        results = list({r['id']:r for r in results}.values())
        if not results and error_status['isError'] :
            abort(error_status['code'], message=f"Bionames lookup endpoint returned {error_status['code']} error code")
        else:
            return results

api.add_resource(Search, '/search/<term>/<category>/')

