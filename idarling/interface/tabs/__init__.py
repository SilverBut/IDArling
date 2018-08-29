from .servers import _TabCfgServer
from .general import _TabCfgGeneral
from .network import _TabCfgNetwork


def TabCfgServer(program, parent):
    return _TabCfgServer(program, parent).get()


def TabCfgGeneral(program, parent):
    return _TabCfgGeneral(program, parent).get()


def TabCfgNetwork(program, parent):
    return _TabCfgNetwork(program, parent).get()
