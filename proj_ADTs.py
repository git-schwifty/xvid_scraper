from queue import PriorityQueue
from heapq import heapify
import time

class MyQueue:
    """
    Allows you to both pop dictionaries and other kinds of data onto
    the queue as well as bumps the lowest-priority item when at max
    queue size and 'put' is called.
    """
    def __init__(self, maxsize=25):
        self._id = 0
        self.maxsize = maxsize
        self._q    = PriorityQueue()
        self._p    = PriorityQueue()  # reversed q
        self._data = {}

    def put(self, value, priority):
        self._id += 1
        priority = round(priority, 2)  # float comparisons can be weird
        to_put = (priority, self._id)
        to_put_low = (-1*to_put[0], to_put[1])
        if self.full():
            worst = self._p.get()
            worst = (worst[0] * -1, worst[1])
            del self._q.queue[self._q.queue.index(worst)]
        self._q.put(to_put)
        self._p.put(to_put_low)
        self._data[self._id] = value

    def get(self):
        while self.empty():
            time.sleep(3)
        priority, identifier = self._q.get()
        low_version = (-priority, identifier)
        del self._p.queue[self._p.queue.index(low_version)]
        return self._data[identifier]

    def empty(self):
        return self._q.empty()

    def full(self):
        return self._q.qsize() >= self.maxsize

    def not_full(self):
        return not self.full()

    def qsize(self):
        return len(self._q)

