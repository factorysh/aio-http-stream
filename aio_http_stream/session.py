"""
Store things and forget them.
"""


import time


class Session:
    """
    Session acts a dict, with a max size, and it forgets old items.

    Eviction is lazy, or explicit, with garbage collection.

    The code is compatible with asyncio.
    """

    def __init__(self, max_size: int = 0, max_age: int = 0) -> None:
        assert max_size >= 0, "Positive max_size, please"
        assert max_age >= 0, "Positive max_age, please"
        self.max_size = max_size
        self.max_age = max_age
        self.data = dict()

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        if key not in self.data:
            raise IndexError()
        ts = time.monotonic()
        last, value = self.data[key]
        if self.max_age > 0 and (ts - last) > self.max_age:
            "too old"
            del self.data[key]
            raise IndexError()
        self.data[key] = (ts, value)  # let refresh the timer
        return value

    def __delitem__(self, key):
        del self.data[key]

    def __setitem__(self, key, value):
        if (
            self.max_size > 0
            and key not in self.data
            and len(self.data) > self.max_size
        ):
            raise Exception("Your session is full")
        self.data[key] = (time.monotonic(), value)

    def __len__(self):
        return len(self.data)

    def garbage_collector(self) -> int:
        "Looking for rotten items and removing them. Returns number of evictions"
        assert self.max_age != 0, "Garbage collection with max_age=0 is a strange idea"
        ts = time.monotonic()
        garbage = list()
        for k, v in self.data.items():
            if (ts - v[0]) > self.max_age:
                garbage.append(k)
        for k in garbage:
            del self.data[k]
        return len(garbage)

    def keys(self):
        if self.max_age == 0:
            return self.data.keys()
        keys = list()
        old = list()
        ts = time.monotonic()
        for k in self.data.keys():
            if (ts - self.data[k][0]) > self.max_age:
                old.append(k)
            else:
                keys.append(k)
        for k in old:
            del self.data[k]
        return keys
