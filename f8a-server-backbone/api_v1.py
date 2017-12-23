import datetime
import functools
import uuid
import json
import requests
import re

from io import StringIO

import botocore
from flask import Blueprint, current_app, request, url_for, Response
from flask.json import jsonify
from flask_restful import Api, Resource, reqparse
from flask_cors import CORS
from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from . import rdb, cache
from .exceptions import HTTPError
from .schemas import load_all_server_schemas

from .resource import add_resource_no_matter_slashes

import os
import urllib

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')
rest_api_v1 = Api(api_v1)
CORS(api_v1)

original_handle_error = rest_api_v1.handle_error

ANALYTICS_API_VERSION = "v1.0"


# Resource Definition
add_resource_no_matter_slashes(StackAggreagor, '/stack-aggregator')
add_resource_no_matter_slashes(Analytics, '/analytics')


# workaround https://github.com/mitsuhiko/flask/issues/1498
# NOTE: this *must* come in the end, unless it'll overwrite rules defined after this
@api_v1.route('/<path:invalid_path>')
def api_404_handler(*args, **kwargs):
    return jsonify(error='Cannot match given query to any API v1 endpoint'), 404
