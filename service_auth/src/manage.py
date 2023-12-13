from app import create_app
from config import flask_config

app = create_app(flask_config)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
