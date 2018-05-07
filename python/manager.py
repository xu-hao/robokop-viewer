#!/usr/bin/env python

"""ROBOKOP manager layer"""

import os
import sys

import requests
from flask_restplus import Resource

from setup import app, api
from logging_config import logger
from util import get_tasks, getAuthData
import questions_api
import q_api
import a_api
import feedback_api

@api.route('/tasks')
class Tasks(Resource):
    @api.response(200, 'Success')
    def get(self):
        """Get list of tasks (queued and completed)"""
        tasks = get_tasks()
        return tasks

@api.route('/t/<task_id>')
@api.param('task_id', 'A task id')
class TaskStatus(Resource):
    @api.response(200, 'Success')
    def get(self, task_id):
        """Get status for task"""
        # task = celery.AsyncResult(task_id)
        # return task.state

        flower_url = f'http://{os.environ["FLOWER_HOST"]}:{os.environ["FLOWER_PORT"]}/api/task/result/{task_id}'
        response = requests.get(flower_url, auth=(os.environ['FLOWER_USER'], os.environ['FLOWER_PASSWORD']))
        return response.json()

@api.route('/concepts')
class Concepts(Resource):
    @api.response(200, 'Success')
    def get(self):
        """Get known biomedical concepts"""
        r = requests.get(f"http://{os.environ['BUILDER_HOST']}:{os.environ['BUILDER_PORT']}/api/concepts")
        return r.json()

@api.route('/user')
class User(Resource):
    @api.response(200, 'Success')
    def get(self):
        """Get current user info"""
        user = getAuthData()
        return user
