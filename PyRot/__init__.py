from Plugins import Plugins
from Config import Config
from Console import Console
from Proxy import ProxyHandler, ProxyMemory, ClientHandler
from Utils import Utils

from collections import OrderedDict

# class Example (object):
#     def __init__(self):
#         self.instances = None
#
#     def set_instances(self, instances):
#         self.instances = instances
#     def run_on_start(self):
#         return

global Instances

class Instances (object):
    def __init__(self):
        self.instances_dict = OrderedDict([
            ("Config" , Config()),
            ("Console", Console()),
            ("Plugins", Plugins()),
            ("ProxyHandler", ProxyHandler()),
            ("ProxyMemory", ProxyMemory()),
            ("ClientHandler", ClientHandler()),
            ("Utils", Utils())
        ])

        for instance in self.instances_dict:
            self.instances_dict[instance].set_instances(self.instances_dict)

        for instance in self.instances_dict:
            self.instances_dict[instance].run_on_start()

    def __getitem__(self, item):
        return self.get_instance(item)

    def get_instance(self, name):
        if self.instances_dict.get(name) is None:
            raise TypeError("Instance not found!.")
            return False
        else:
            return self.instances_dict.get(name)

Instances()