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
    input_json = request.get_json()
    r = RecommendationTask().execute(input_json)

    return flask.jsonify(r)


@app.route('/api/v1/stack_aggregator', methods=['POST'])
def stack_aggregator():
    input_json = request.get_json()
    s = StackAggregator().execute(input_json)
    print(s)

    return flask.jsonify(s)


if __name__ == "__main__":
    app.run()
