from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_restful import Resource, Api
from config import Config, ALLOWED_EXTENSIONS
from flask_jwt_extended import JWTManager

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app=app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
api = Api(app)

from .models import *
from .routes import *
from .restapi import *
