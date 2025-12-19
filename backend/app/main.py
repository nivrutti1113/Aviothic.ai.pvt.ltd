# Main application entry point
from flask import Flask

def create_app():
    app = Flask(__name__)
    
    # Register blueprints
    from .routes import auth, predict, health
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(predict.bp)
    app.register_blueprint(health.bp)
    
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)