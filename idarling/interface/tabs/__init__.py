from .servers import _TabCfgServer
from .general import _TabCfgGeneral


def TabCfgServer(program, parent):
    return _TabCfgServer(program, parent).get()


def TabCfgGeneral(program, parent):
    return _TabCfgGeneral(program, parent).get()
