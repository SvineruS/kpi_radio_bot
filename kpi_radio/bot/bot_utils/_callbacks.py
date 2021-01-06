import json

from consts.btns_text import CALLBACKS as CB


# callbackdata пробел base, не база данных
class _CallbackDataBase:
    DATA_FIELDS: tuple

    def __init__(self, *args):
        if len(args) != len(self.DATA_FIELDS):
            raise ValueError("Wrong callback data")
        for i, k in enumerate(self.DATA_FIELDS):
            self.__setattr__(k, args[i])
        self.data = args

    def __str__(self):
        return json.dumps((self.__class__.__name__, *self.data))

    @classmethod
    def from_str(cls, query_data: str):
        try:
            data = json.loads(query_data)
        except json.JSONDecodeError:
            return None
        action, *data = data
        if action != cls.__name__:
            return None
        return cls(*data)

    @classmethod
    def c(cls, action, data=()):
        action = ''.join(map(str, map(int, action)))
        attrs = {
            'DATA_FIELDS': data,
            **{k: None for k in data}
        }
        return type(action, (cls, ), attrs)


CBOrderDay = _CallbackDataBase.c((CB.ORDER, CB.DAY), ('day', ))
CBOrderTime = _CallbackDataBase.c((CB.ORDER, CB.TIME), ('day', 'time'))
CBOrderNoTime = _CallbackDataBase.c((CB.ORDER, CB.NOTIME), ('day', 'attempts'))
CBOrderBack = _CallbackDataBase.c((CB.ORDER, CB.BACK))
CBOrderCancel = _CallbackDataBase.c((CB.ORDER, CB.CANCEL))
CBOrderModerate = _CallbackDataBase.c((CB.ORDER, CB.MODERATE), ('day', 'time', 'status'))
CBOrderUnModerate = _CallbackDataBase.c((CB.ORDER, CB.UNMODERATE), ('day', 'time', 'status'))

CBPlaylistNext = _CallbackDataBase.c((CB.PLAYLIST, CB.NEXT))
CBPlaylistDay = _CallbackDataBase.c((CB.PLAYLIST, CB.DAY), ('day', ))
CBPlaylistTime = _CallbackDataBase.c((CB.PLAYLIST, CB.TIME), ('day', 'time'))
CBPlaylistBack = _CallbackDataBase.c((CB.PLAYLIST, CB.BACK))
CBPlaylistMove = _CallbackDataBase.c((CB.PLAYLIST, CB.MOVE), ('index', 'start_time'))

CBOtherHelp = _CallbackDataBase.c((CB.OTHER, CB.HELP), ('key', ))
