from ._connector import DB
from .stats import Stats
from .users import Users
from .tracklist import Tracklist

DB.create_tables([Stats, Users, Tracklist])


__all__ = [
    'Users', 'Stats', 'Tracklist'
]
