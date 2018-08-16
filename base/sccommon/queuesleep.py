import queue

class QueueSleepMixin():

    def __init__(self):
        self.wakequeue = queue.Queue()

    def shutdown(self):
        self.wakequeue.put(True)

    def poke(self):
        self.wakequeue.put(False)

    def qwait(self, timeout):
        """ Wait for timeout seconds.  Wake immediately if something is dropped in the queue """
        try:
            self.done = self.wakequeue.get(timeout=timeout)
        except:
            pass

