"""
Application entrypoint for the NotationLearner Flask app.
"""

from app import create_app

app = create_app()


if __name__ == "__main__":
    print(f"Database ready ({app.config['SQLALCHEMY_DATABASE_URI'].split('://')[0]}).")
    app.run(debug=True, port=5001)

