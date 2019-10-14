from threading import Thread

class ThreadPool:
    def __init__(self, thread_number, target, arguments):
        self.thread_limit = thread_number
        self.threads = []
        self.target = target
        self.arguments = arguments

    def wait_threads(self):
        while len(self.threads) == self.thread_limit:
            for thread in self.threads:
                if not thread.isAlive():
                    self.threads.remove(thread)
        return

    def start_sync(self):
        act_arg = 0

        if len(self.arguments) < 1:
            return

        for arg in self.arguments:
            new_thread = Thread(target=self.target, args=(arg, ))
            self.threads.append(new_thread)
            new_thread.start()
            self.wait_threads()
            act_arg += 1



class Utils (object):
    def __init__(self):
        self.instances = None

    def is_integer(self, string):
        string = str(string)

        try:
            int(string)
        except Exception:
            return False

        return True

    def is_ip(self, string):
        ip_p = string.split(".")

        if 3 > len(ip_p) < 3:
            return False

        for i in ip_p:
            if not self.is_integer(i):
                return False
            if 3 < len(str(i)) > 1:
                return False

        return True

    def string_time_to_seconds(self, string):
        string = str(string)

        seconds = 0
        blocks = []
        current_block = ""

        for letter in list(string):
            if self.is_integer(letter):
                current_block += letter
            elif letter != " ":
                if not len(current_block) < 1:
                    current_block += letter
                    blocks.append(current_block)
                    current_block = ""

        for block in blocks:
            time = block[-1:].lower()
            number = block[0:len(block)-1]
            time_x = None

            if time == "m":
                time_x = 60
            elif time == "h":
                time_x = 3600
            elif time == "s":
                time_x = 1
            elif time == "d":
                time_x = 86400

            seconds += (int(number) * time_x)

        return seconds

    def string_time_to_miliseconds(self, string):
        return self.string_time_to_seconds(string) * 1000

    def create_thread_pool(self, thread_number, target, arguments):
        return ThreadPool(thread_number, target, arguments)

    def set_instances(self, instances):
        self.instances = instances
    def run_on_start(self):
        return