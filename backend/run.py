"""Point d'entree en developpement : python run.py

En production on prefere hypercorn :
    hypercorn --bind 0.0.0.0:5000 "app:create_app()"
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
