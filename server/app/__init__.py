from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///rag.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    print("Initializing app")
    
    db.init_app(app)
    migrate.init_app(app, db)
    
    CORS(app)


    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app