import socket
from threading import Thread
import requests
from json import loads
from rethinkdb import RethinkDB

from time import sleep, time

import hashlib, random
from sys import exit

import urllib
conn_limit = {}
class ClientHandler (object):
    def __init__(self):
        self.instances = None

        self.clients = {}

    def auth(self, user_ip):
        with open('rotatingips.txt') as f:
            if user_ip in f.read():
                return True
        return False

    def get_client_hash(self, addr):
        return hashlib.new("md5", "{}".format(addr[0])).hexdigest()

    def get_proxy(self, addr):

        if not self.instances.get("Config")["ClientIdentification"]:
            return self.instances.get("ProxyMemory").random_proxy()

        client_hash = self.get_client_hash(addr)

        if self.clients.get(client_hash) is None:
            self.clients[client_hash] = {"proxy" : self.instances.get("ProxyMemory").random_proxy(), "is_refreshing" : False}

        return self.clients.get(client_hash)["proxy"]

    def renew_proxy(self, addr):
        client_hash = self.get_client_hash(addr)

        if self.clients[client_hash]["is_refreshing"]:
            while self.clients[client_hash]["is_refreshing"]:
                pass
            return self.clients[client_hash]["proxy"]

        self.clients[client_hash]["is_refreshing"] = True

        new_proxy = self.instances.get("ProxyMemory").random_proxy()

        self.clients[client_hash]["proxy"] = new_proxy
        self.clients[client_hash]["is_refreshing"] = False

        return new_proxy

    def handle(self, buffer):
        return buffer

    def data_thread(self, src, dst):
        try:
            while True:
                buffer = src.recv(0x400)

                if len(buffer) == 0:
                    break

                dst.send(self.handle(buffer))

            src.close()
            dst.close()
        except:
            src.close()
            dst.close()
            return

    def handle_client(self, client, addr):
        global conn_limit
        conn_limit["limit"] = 300
        if not self.auth(addr[0]):
            self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Client '{}' tried to connect without authentication.".format(addr[0]))
            return
        if  conn_limit.get(addr[0], 0) < 0:
            conn_limit[addr[0]] = 0

        conn_limit[addr[0]] = conn_limit.get(addr[0], 0) + 1
        if conn_limit[addr[0]] > conn_limit["limit"]:
            self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Client '{}' tried to connect but has reached the connection limit.".format(addr[0]))
            conn_limit[addr[0]] = conn_limit.get(addr[0], 0) - 1
            return

        
        proxy = self.get_proxy(addr)
        proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        proxy_socket.settimeout(self.instances.get("Config")["CheckTimeout"])

        if not self.instances.get("ProxyMemory").exists(proxy):
            if self.instances.get("Config")["ClientIdentification"]:
                proxy = self.renew_proxy(addr)
            else:
                while True:
                    proxy = self.instances.get("ProxyMemory").random_proxy()

                    if self.instances.get("ProxyMemory").exists(proxy):
                        break

        try:
            proxy_socket.connect((proxy["host"], int(proxy["port"])))
        except Exception as e:
            self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "The proxy connection failed in client '{}'. Deleting the proxy '{}:{}' and waiting to the next request. ({})".format(addr[0], proxy.get("host"), proxy.get("port"), str(e)))
            client.close()
            self.instances.get("ProxyMemory").remove_proxy(proxy)
            conn_limit[addr[0]] = conn_limit.get(addr[0], 0) - 1
            return

        try:
            client_to_proxy = Thread(target=self.data_thread, args=(client, proxy_socket,))
            proxy_to_client = Thread(target=self.data_thread, args=(proxy_socket, client))

            client_to_proxy.start()
            proxy_to_client.start()
            conn_limit[addr[0]] = conn_limit.get(addr[0], 0) - 1


        except Exception as e:
            self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "An error ocurred while transmitting data on client '{}' ({}).".format(addr[0], str(e)))
            conn_limit[addr[0]] = conn_limit.get(addr[0], 0) - 1
            return

    def set_instances(self, instances):
        self.instances = instances
    def run_on_start(self):
        return

class ProxyMemory (object):
    def __init__(self):
        self.instances = None
        self.stored_proxies = {}
        self.refresh_tables = []
        self.plugins = []
        self.bad_proxies = 0

    def get_proxy_hash(self, proxy_obj):
        return hashlib.new("md5", "{}:{}:{}".format(proxy_obj.get("host"), proxy_obj.get("port"), proxy_obj.get("type"))).hexdigest()

    def exists(self, proxy):
        if type(proxy) is dict:
            proxy = self.get_proxy_hash(proxy)

        if self.stored_proxies.get(proxy):
            return True

        return False

    def check_proxy(self, proxy):

        if proxy is None:
            return False

        proxy_dict = {
            "http"  : "{}://{}:{}".format(proxy.get("type").lower(), proxy.get("host"), proxy.get("port")),
            "https" : "{}://{}:{}".format(proxy.get("type").lower(), proxy.get("host"), proxy.get("port")),
            "ftp" : "{}://{}:{}".format(proxy.get("type").lower(), proxy.get("host"), proxy.get("port"))
        }

        try:
            chk_request = requests.get(self.instances.get("Config")["CheckUrl"], proxies=proxy_dict, verify=True, timeout=self.instances.get("Config")["CheckTimeout"])

            if chk_request.status_code != 200:
                return False

            if self.instances.get("Config")["ExpectResponse"] == "json":
                response = loads(chk_request.text)
                ip = None

                for i in self.instances.get("Config")["JsonIpField"].replace(" ", "").split("|"):
                    if ip is None:
                        ip = response.get(i)
                    else:
                        ip = ip.get(i)

                if proxy.get("host") != ip:
                    return False
            elif self.instances.get("Config")["ExpectResponse"] == "plain":
                if proxy.get("host") != chk_request.text.replace(" ", ""):
                    return False

            return True
        except Exception:
            return False

    def remove_proxy_if_bad(self, proxy_hash):
        proxy = self.stored_proxies.get(proxy_hash)

        if proxy is None:
            return

        if not self.check_proxy(proxy):
            if self.stored_proxies.get(proxy_hash) is not None:
                del(self.stored_proxies[proxy_hash])
            self.bad_proxies += 1

        exit()

    def remove_proxy(self, proxy_hash):
        if type(proxy_hash) is dict:
            proxy_hash = hashlib.new("md5", "{}:{}:{}".format(proxy_hash.get("host"), proxy_hash.get("port"), proxy_hash.get("type"))).hexdigest()

        if self.stored_proxies.get(proxy_hash) is not None:
            del(self.stored_proxies[proxy_hash])

    def proxy_check_thread(self):
        sleep(3)
        while True:

            if self.instances.get("Config")["CheckThreads"] == 0:
                self.instances.get("Console").print_c(self.instances.get("Console").WARNING, "Proxy checking is disabled!.")
                break

            self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Starting new check to {} proxies in memory...".format(len(self.stored_proxies)))

            arguments = []

            for proxy in self.stored_proxies:
                arguments.append(proxy)

            thread_pool = self.instances.get("Utils").create_thread_pool(self.instances.get("Config")["CheckThreads"], self.remove_proxy_if_bad, arguments)
            thread_pool.start_sync()

            self.instances.get("Console").print_c(self.instances.get("Console").CORRECT, "Done!. {} bad proxies removed from memory. Waiting for the next check...".format(self.bad_proxies))

            self.bad_proxies = 0

            if self.instances.get("Config")["CheckElapse"]:
                sleep(self.instances.get("Utils").string_time_to_seconds(self.instances.get("Config")["CheckElapse"]))

    def refresh_thread(self):
        while True:
            actual_time = time()

            for plugin_obj in self.refresh_tables:
                if plugin_obj.get("time") <= actual_time:
                    self.instances.get("Console").print_c(self.instances.get("Console").WARNING, "Refreshing plugin '{}'...".format(plugin_obj.get("plugin").NAME))
                    proxies = plugin_obj.get("plugin").return_proxies(refresh=True)
                    urllib.urlretrieve ("https://api.proxyscrape.com/?request=rotatingips&auth=somethinghere", "rotatingips.txt")
                    proxies_loaded = 0

                    for proxy in proxies:

                        if proxy.get("type") is None:
                            proxy["type"] = self.instances.get("Config")["DefaultProxyType"]

                        hash = hashlib.md5("{}:{}:{}".format(proxy.get("host"), proxy.get("port"), proxy.get("type"))).hexdigest()

                        if self.stored_proxies.get(hash) is None:
                            self.stored_proxies[hash] = proxy
                            proxies_loaded += 1

                    plugin_obj["time"] = time() + self.instances.get("Utils").string_time_to_seconds(plugin_obj.get("plugin").REFRESH_ELAPSE)

                    self.instances.get("Console").print_c(self.instances.get("Console").CORRECT, "Done!. {} new proxies loaded from '{}'.".format(proxies_loaded, plugin_obj.get("plugin").NAME))

    def get_proxies_thread(self):
        self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Starting proxy gathering related plugins...")
        if len(self.plugins) < 1:
            self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "No plugins found for proxy gathering.")
            return

        plugins_loaded = 0

        for plugin in self.plugins:
            try:
                self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Executing proxy plugin '{}'...".format(plugin.NAME))
                plugin.run()
                proxies = plugin.return_proxies()

                proxies_loaded = 0

                for proxy in proxies:

                    if not self.instances.get("Utils").is_ip(proxy.get("host")):
                        continue
                    if not self.instances.get("Utils").is_integer(proxy.get("port")):
                        continue

                    proxy["port"] = int(proxy["port"])

                    if proxy.get("type") is None:
                        proxy[type] = self.instances.get("Config")["DefaultProxyType"]

                    hash = hashlib.md5("{}:{}:{}".format(proxy.get("host"), proxy.get("port"), proxy.get("type"))).hexdigest()

                    if self.stored_proxies.get(hash) is None:
                        self.stored_proxies[hash] = proxy
                        proxies_loaded += 1

                self.instances.get("Console").print_c(self.instances.get("Console").CORRECT, "{} -> {} proxies loaded.".format(plugin.NAME, proxies_loaded))

                if plugin.REFRESH and plugin.REFRESH_ELAPSE != "":
                    refresh_time = self.instances.get("Utils").string_time_to_seconds(plugin.REFRESH_ELAPSE)

                    if refresh_time == 0:
                        self.instances.get("Console").print_c(self.instances.get("Console").WARNING, "The plugin '{}' is refreshing all the {} seconds and can cause performance issues.".format(plugin.NAME, refresh_time))

                    self.refresh_tables.append({"plugin" : plugin, "time" : time() + refresh_time})

                plugins_loaded += 1
            except Exception as e:
                self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "Plugin {} throw an error while running it ({}).".format(plugin.NAME, str(e)))

        self.instances.get("Console").print_c(self.instances.get("Console").CORRECT, "Done! {}/{} plugins executed successfully ({} proxies)".format(plugins_loaded, len(self.plugins), len(self.stored_proxies)))

    def random_proxy(self):
        if len(self.stored_proxies) == 0:
            return None

        return self.stored_proxies[random.choice(self.stored_proxies.keys())]

    def set_instances(self, instances):
        self.instances = instances
    def run_on_start(self):
        if not self.instances.get("Config")["CheckUrl"].startswith("http") or not self.instances.get("Config")["CheckUrl"].startswith("https"):
            self.instances.get("Console").print_c(self.instances.get("Console").FATAL, "Invalid check url for proxy checking.")

        self.plugins = self.instances.get("Plugins").get_plugins("proxies")

        get_proxy_thread = Thread(target=self.get_proxies_thread)
        get_proxy_thread.start()

        if not self.instances.get("Config")["CheckThreads"] is False or None or 0:
            check_proxy_thread = Thread(target=self.proxy_check_thread)
            check_proxy_thread.start()

        refresh_thread = Thread(target=self.refresh_thread)
        refresh_thread.start()

        return

class ProxyHandler (object):
    def __init__(self):
        self.proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = []
        self.instances = None

    def proxy_handler_thread(self):
        self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Initializing the proxy...")

        if not self.instances.get("Utils").is_ip(self.instances.get("Config")["ProxyBindAddress"]):
            self.instances.get("Console").print_c(self.instances.get("Console").FATAL, "Proxy bind address is not a valid ip ({}).".format(self.instances.get("Config")["ProxyBindAddress"]))
        if not self.instances.get("Utils").is_integer(self.instances.get("Config")["ProxyBindPort"]):
            self.instances.get("Console").print_c(self.instances.get("Console").FATAL, "Proxy bind port is not valid ({})".format(self.instances.get("Config")["ProxyBindPort"]))

        try:
            self.proxy_socket.bind((self.instances.get("Config")["ProxyBindAddress"], self.instances.get("Config")["ProxyBindPort"]))
            self.proxy_socket.listen(10000)

            self.instances.get("Console").print_c(self.instances.get("Console").CORRECT, "Done!. Proxy is listening on {}:{}...".format(self.instances.get("Config")["ProxyBindAddress"], self.instances.get("Config")["ProxyBindPort"]))

            while True:
                if self.proxy_socket is None:
                    break

                try:

                    client, addr = self.proxy_socket.accept()

                    # self.instances.get("Console").print_c(self.instances.get("Console").INFO, "New connection to the proxy from '{}:{}'".format(addr[0], addr[1]))

                    if self.instances.get("Config")["DisableLocalConnections"]:
                        self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "The local computer connected to the proxy and is disabled. Closing the socket...")
                        client.close()
                        continue

                    if len(self.instances.get("ProxyMemory").stored_proxies) is 0:
                        self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "No proxies in memory for clients. Closing the connection for the client '{}:{}'".format(addr[0], addr[1]))
                        client.close()
                    else:
                        client_thread = Thread(target=self.instances.get("ClientHandler").handle_client, args=(client, addr))
                        client_thread.start()
                except Exception as e:
                    self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "Proxy handler is working correctly but a connection throw an error ({}).".format(str(e)))
        except Exception as e:
            self.instances.get("Console").print_c(self.instances.get("Console").FATAL, "An error ocurred while binding the proxy on '{}:{}' ({}).".format(self.instances.get("Config")["ProxyBindAddress"], self.instances.get("Config")["ProxyBindPort"], str(e)))

    def set_instances(self, instances):
        self.instances = instances
    def run_on_start(self):

        proxy_handler_thread = Thread(target=self.proxy_handler_thread)
        proxy_handler_thread.start()

        return
