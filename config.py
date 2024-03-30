import os
from dotenv import load_dotenv

load_dotenv()

class Config(object):
    SQLALCHEMY_DATABASE_URI= "sqlite:///data.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    SECRET_KEY = os.getenv('SECRET_KEY')
    UPLOAD_FOLDER = os.path.join(os.getcwd(),'db')
    DATASET_FOLDER = os.path.join(os.getcwd(),'db')
    TEMPLATES_AUTO_RELOAD = True


ALLOWED_EXTENSIONS = {'csv'}

    
