from flask import Flask
from routes.routes import api
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
# Set a secret key for the application
app.secret_key = 'p@ssw0rd'

# Register routes
app.register_blueprint(api, url_prefix='/api')

if __name__ == '__main__':
    app.run(port=8080)