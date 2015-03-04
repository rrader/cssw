from weakref import WeakMethod
from inspect import ismethod

BUS_LIST = {}


def bus_name(ns, bus):
    return "{}::{}".format(ns, bus)


def notify(bus, msg, ns="DEFAULT"):
    handlers = BUS_LIST.get(bus_name(ns, bus), [])
    handlers += BUS_LIST.get(bus_name("ALL", bus), [])
    for handler in handlers:
        handler_func = handler()
        if handler_func:
            try:
                handler_func(msg)
            except TypeError:
                handler_func(msg, ns)


def subscribe(bus, handler, ns="DEFAULT"):
    handlers = BUS_LIST.get(bus_name(ns, bus), [])
    if ismethod(handler):
        handlers.append(WeakMethod(handler))
    else:
        handlers.append(lambda: handler)
    BUS_LIST[bus_name(ns, bus)] = handlers


def unsubscribe(bus, handler, ns="DEFAULT"):
    handlers = BUS_LIST.get(bus_name(ns, bus), [])
    if handler in handlers:
        handlers.remove(handler)


def unsubscribe_all(obj, ns="DEFAULT"):
    for bus in BUS_LIST:
        for handler in BUS_LIST[bus]:
            try:
                if handler.__self__ == obj:
                    unsubscribe(bus.replace(ns+"::", ""), handler, ns=ns)
            except AttributeError:
                pass
