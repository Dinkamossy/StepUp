import os

import flask
import base64
from flask import Flask, g

from step_up import formula


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'stepUp.sqlite'),
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.template_filter('make_image')
    def make_image(image):
        return str(base64.b64encode(image), "utf-8")

    # Initialize the database
    import step_up.database as database
    database.init_app(app)

    @app.route('/')
    def mainpage():
        # Items for dashboard
        if g.user:
            steps = formula.get_steps(g.user['userid'])
            return flask.render_template('index.html', steps=steps)
        return flask.render_template('index.html')

    @app.route('/login')
    def login_page():
        return flask.render_template("auth/login.html")

    import step_up.auth as auth
    app.register_blueprint(auth.bp)

    return app
