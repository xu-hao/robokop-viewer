'''
Blueprint for /api/simple/* endpoints
'''

import os
import sys
import json
import time
import re
from uuid import uuid4
import logging
from datetime import datetime
import requests
from flask import jsonify, request
from flask_security import auth_required
from flask_restful import Resource

from manager.setup import api

logger = logging.getLogger(__name__)

view_storage_dir = f"{os.environ['ROBOKOP_HOME']}/uploads/"
if not os.path.exists(view_storage_dir):
    os.mkdir(view_storage_dir)

output_formats = ['DENSE', 'MESSAGE', 'CSV', 'ANSWERS']

def parse_args_output_format(req_args):
    output_format = req_args.get('output_format', default=output_formats[1])
    if output_format.upper() not in output_formats:
        raise RuntimeError(f'output_format must be one of [{" ".join(output_formats)}]')
    
    return output_format

def parse_args_max_results(req_args):
    max_results = req_args.get('max_results', default=None)
    max_results = max_results if max_results is not None else 250
    return max_results

def parse_args_max_connectivity(req_args):
    max_connectivity = req_args.get('max_connectivity', default=None)
    
    if max_connectivity and isinstance(max_connectivity, str):
        if max_connectivity.lower() == 'none':
            max_connectivity = None
        else:
            try:
                max_connectivity = int(max_connectivity)
            except ValueError:
                raise RuntimeError(f'max_connectivity should be an integer')
            except:
                raise
            if max_connectivity < 0:
                max_connectivity = None

    return max_connectivity

def parse_args_rebuild(req_args):
    rebuild = request.args.get('rebuild', default='false')
    
    if not (rebuild.lower() in ['true', 'false']):
        raise RuntimeError(f'rebuild must be "true" or "false"')

    return rebuild.lower()


class View(Resource):
    def post(self):
        """
        Upload an answerset for a question to view
        ---
        tags: [simple]
        requestBody:
            name: Answerset
            description: The machine-readable question graph.
            content:
                application/json:
                    schema:
                        $ref: '#/components/schemas/Message'
            required: true
        responses:
            200:
                description: A URL for further viewing
        """
        
        logger.info('Recieving Answerset for storage and later viewing')
        message = request.json
        
        # Save the message to archive folder
        for _ in range(25):
            try:
                uid = str(uuid4())
                this_file = os.path.join(view_storage_dir, f'{uid}.json')
                with open(this_file, 'x') as answerset_file:
                    logger.info('Saving Message')
                    json.dump(message, answerset_file)
                break
            except:
                logger.info('Error encountered writting file. Retrying')
                pass
        else:
            logger.info('Error encountered writting file')
            return "Failed to save resource. Internal server error", 500
        
        return uid, 200

api.add_resource(View, '/simple/view/')


