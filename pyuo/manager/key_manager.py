import win32api, win32con
from itertools import imap, ifilter
from key_codes import codes
import time
import gevent

class BindError(Exception):
    pass

def getkey_int(key_int):
    i = win32api.GetAsyncKeyState(key_int)
    return i < 0

def getkey(key):
    key_int = codes[key]
    return getkey_int(key_int)

keys_list = set(codes.keys())

class CombinationListener(object):
    """Helper class to help in defining key combinations"""

    def __init__(self, release_time = .4):
        self.release_time = release_time
        self.pressed = {}

    def check_pressed(self):
        T = time.time()
        pressed = filter(getkey, keys_list)
        if not pressed:
            result = self.pressed.keys()
            self.pressed = {}
            return result
        for code in pressed:
            self.pressed[code] = T
        for code, value in self.pressed.items():
            if value < T - self.release_time:
                del self.pressed[code]
        return self.pressed.keys()

    def map_pressed(self):
        return [codes.keys()[codes.values().index(code)] for code in self.check_pressed()]


class KeyBinder(object):
    keys_list = set(codes.keys())

    def __init__(self, manager, allow_repeat = False):
        self.manager = manager
        self.keys = {key: None for key in self.keys_list}
        self.binds = {}
        self.paused = False
        self.last_combination = None

    def pause(self):
        self.paused = True

    def unpause(self):
        self.paused = False

    def uniform(self, keys_string):
        if not keys_string:
            return ''
        keys = [key.strip() for key in keys_string.split('+')]
        for key in keys:
            if key not in self.keys_list:
                raise BindError("[%s]: %s is unknown" % (keys_string, key))
        keys.sort()
        return '+'.join(keys)

    def bind(self, bind):
        keys = self.uniform(bind.keys)
        if keys in self.binds:
            raise BindError('%s is already bound, you need to unbind it first')
        self.binds[keys] = bind

    def unbind(self, bind):
        for key, bind_ in self.binds.items():
            if bind_ == bind:
                del self.binds[key]
                return
        raise BindError('bind `%s` for does not exist' % bind.name)

    def get_bind(self, keys):
        return self.binds.get(keys, None)

    def get_keys(self, bind):
        for key, bind_ in self.binds.iteritems():
            if bind_ is bind:
                return key
        return None

    def execute(self):
        if self.paused:
            return
        pressed = self.uniform('+'.join(ifilter(getkey, keys_list)))
        for (keys, bind) in self.binds.iteritems():
            if pressed == self.last_combination and not bind.allow_repeat:
                return
            if keys == pressed:
                self.manager.spawn(bind.__call__)
        self.last_combination = pressed

