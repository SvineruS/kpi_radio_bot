from .player_mopidy import PlayerMopidy
from .player_radioboss import PlayerRadioboss

Player = PlayerMopidy

__all__ = [
    'Player',
    'PlayerRadioboss', 'PlayerMopidy'
]
