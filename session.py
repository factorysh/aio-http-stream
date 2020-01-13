import time


class Session:
    def __init__(self, max_size=0, max_age=0):
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
        return value

    def __delitem(self, key):
        del self.data[key]

    def __setitem__(self, key, value):
        if self.max_size > 0 and key not in self.data and len(self.data) > self.max_size:
            raise Exception("Your session is full")
        self.data[key] = (time.monotonic(), value)

    def __len__(self):
        return len(self.data)

    def garbage_collector(self):
        if self.max_age == 0:
            raise Exception("Garbage collection with max_age=0 is a strange idea")
        ts = time.monotonic()
        garbage = list()
        for k, v in self.data.items():
            if (ts - v[0]) > self.max_age:
                garbage.append(k)
        for k in garbage:
            del self.data[k]
        return len(garbage)
