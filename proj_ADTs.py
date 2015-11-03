from queue import PriorityQueue
from heapq import heapify

class MyQueue:
    """
    Allows you to both pop dictionaries and other kinds of data onto
    the queue as well as bumps the lowest-priority item when at max
    queue size and 'put' is called.
    """
    def __init__(self, maxsize=25):
        self.maxsize = maxsize
        self._q    = PriorityQueue()
        self._p    = PriorityQueue()  # reversed q
        self._data = {}

    def put(self, value, priority):
        if self.full():
            lowest_priority = self._p.get()
            del self._q.queue[lowest_priority]
            heapify(self._q.queue)
        self._q.put(value["url"],  priority)
        self._p.put(value["url"], -priority)
        self._data[value["url"]] = value

    def get(self):
        url = self._q.get()
        return self._data[url]

    def empty(self):
        return self._q.empty()

    def full(self):
        return self._q.qsize() >= self.maxsize

    def not_full(self):
        return not self.full()

    def qsize(self):
        return len(self._q)

