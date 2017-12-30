import flask
from flask import Flask, request
from flask_cors import CORS
import json
from recommender import RecommendationTask
from stack_aggregator import StackAggregator

app = Flask(__name__)
CORS(app)


@app.route('/api/v1/readiness')
def readiness():
    return flask.jsonify({}), 200


@app.route('/api/v1/liveness')
def liveness():
    return flask.jsonify({}), 200


@app.route('/api/v1/recommender', methods=['POST'])
def recommender():
    r = {'recommendation': 'failure', 'stack_id': None}
    input_json = request.get_json()
    if input_json:
        try:
            r = RecommendationTask().execute(input_json)
        except Exception as e:
            r = {
                'recommendation': 'unexpected error',
                'stack_id': input_json.get('external_request_id'),
                'message': '%s' % e
            }

    return flask.jsonify(r)


@app.route('/api/v1/stack_aggregator', methods=['POST'])
def stack_aggregator():
    s = {'stack_aggregator': 'failure', 'stack_id': None}
    input_json = request.get_json()
    if input_json:
        try:
            s = StackAggregator().execute(input_json)
        except Exception as e:
            s = {
                'stack_aggregator': 'unexpected error',
                'stack_id': input_json.get('external_request_id'),
                'message': '%s' % e
            }

    return flask.jsonify(s)


if __name__ == "__main__":
    app.run()
