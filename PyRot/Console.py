from colorama import Fore, init, Back
from os import path, _exit, fsync, access, W_OK
from time import strftime, time, sleep

from threading import Thread
import operator

class Console (object):
    FATAL = "[" + Back.RED + Fore.WHITE + "FATAL" + Back.RESET + Fore.RESET + "]"
    ERROR = "[" + Fore.RED + "-" + Fore.RESET + "]"
    INFO = "[" + Fore.BLUE + "#" + Fore.RESET + "]"
    WARNING = "[" + Fore.YELLOW + "!" + Fore.RESET + "]"
    CORRECT = "[" + Fore.LIGHTGREEN_EX + "+" + Fore.RESET + "]"

    NO_FATAL = "[FATAL]"
    NO_ERROR = "[-]"
    NO_INFO = "[#]"
    NO_WARNING = "[!]"
    NO_CORRECT = "[+]"

    def __init__(self):
        self.instances = None
        self.log_memory = []
        self.stop_thread = False

    def no_color(self, color):
        if color == Console.FATAL:
            return Console.NO_FATAL
        elif color == Console.ERROR:
            return Console.NO_ERROR
        elif color == Console.INFO:
            return Console.NO_INFO
        elif color == Console.WARNING:
            return Console.NO_WARNING
        elif color == Console.CORRECT:
            return Console.NO_CORRECT

        return color

    def print_c(self, type, string):
        if not self.instances.get("Config")["ConsoleColor"]:
            type = self.no_color(type)

        console_string = "{} {}".format(type, string)
        console_log = "{} {}\n".format(self.no_color(type), string)

        is_fatal = False

        if type == Console.FATAL or type == Console.NO_FATAL:
            is_fatal = True

        self.log_memory.append({"log" : console_log, "print" : console_string, "time" : time(), "is_fatal" : is_fatal})

    def log_thread(self):
        if self.instances.get("Config")["EnableLogFile"] and self.instances.get("Config")["LogName"] is not None:
            self.print_c(Console.INFO, "Opening log file...")

            log_obj = open(self.instances.get("Config")["LogName"], "a+")
            log_size = path.getsize((self.instances.get("Config")["LogName"])) / (1024 * 2)

            if log_size > 200:
                self.print_c(Console.WARNING, "The log file is bigger than 200 MB. Its recomended to erase the log file to increase performance (Actual size: {} MB).".format(log_size))

            if access(self.instances.get("Config")["LogName"], W_OK):
                self.print_c(Console.CORRECT, "Log file is ready!.")
            else:
                self.print_c(Console.FATAL, "Log file is not writeable.")

        while True:
            for log in sorted(self.log_memory, key=operator.itemgetter("time")):
                print(log.get("print"))
                if self.instances.get("Config")["EnableLogFile"] and self.instances.get("Config")["LogName"] is not None:
                    log_obj.write("[{}] {}".format(strftime("%d/%b/%Y - %H:%M:%S"), str(log.get("log"))))
                    log_obj.flush()
                    fsync(log_obj.fileno())
                self.log_memory.remove(log)

                if log.get("is_fatal"):
                    _exit(1)

            if self.stop_thread:
                break


    def set_instances(self, instances):
        self.instances = instances
    def run_on_start(self):
        init()

        self.print_c(Console.WARNING, "Starting PyRot...\n")

        log = Thread(target=self.log_thread, args=())
        log.start()

        sleep(1)

        return