from .analysis_api import register_analysis_api_routes
from .auth import register_auth_routes
from .game_api import register_game_api_routes
from .pages import register_page_routes
from .room_api import register_room_api_routes


def register_routes(app):
    register_page_routes(app)
    register_auth_routes(app)
    register_game_api_routes(app)
    register_analysis_api_routes(app)
    register_room_api_routes(app)
