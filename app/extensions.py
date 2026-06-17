"""Shared Flask extension instances (SQLAlchemy DB and Flask-Login manager) created once and reused app-wide."""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message_category = "error"
