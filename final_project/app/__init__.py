from flask import Flask
from app.routes.generate import generate_blueprint

def create_app():
    app = Flask(__name__)
    app.register_blueprint(generate_blueprint)
    return app
