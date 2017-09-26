from flask import Flask, g
from flask_restful import Api


app = Flask(__name__)
app.config.from_object(__name__)
api = Api(app)

app.config.from_envvar('RESTFUL_GRAPH_SETTINGS', silent=True)


def connect_db():
    """Provides neo4j graph connection"""
    pass


def get_db():
    """
    Opens new graph connection if none exists for
    current application context
    """
    if not hasattr(g, 'graph_db'):
        g.graph_db = connect_db()
    return g.graph_db


@app.teardown_appcontext
def close_db(error):
    """Closes database at end of request context"""
    if hasattr(g, 'graph_db'):
        g.graph_db.close()
