class Main (object): # The name of the class mus be Main.

    NAME = "GetProxiesFromFile"
    AUTH = "MrSentex"
    TYPE = "proxies"
    REFRESH = True
    REFRESH_ELAPSE = "1m" # m = Minutes | h = Hours | s = Seconds | d = Days

    def __init__(self, config_instance): # Build-In
        # Config instance to give to the plugin the capability to read the configuration file.
        self.config = config_instance

        # Default vars
        self.proxies = [] # [{"host" : "127.0.0.1", "port" : 1234}]

        # Personal vars for te plugin or autorun things (Like configuration, etc...)
        self.file = "proxies.txt" # Proxies list (host:port => format)
        self.file_proxy_types = "http" # Types -> socks4, socks5, http, https

    def run (self): # Build-In
        self.get_proxies_from_file()

    def get_proxies_from_file(self):
        with open(self.file, "r") as proxies_obj:
            lines = proxies_obj.readlines()

            for line in lines:
                line = line.replace("\n", "").split(":")


                if len(line) == 2:
                    proxy = {"host" : line[0], "port" : line[1], "type" : self.file_proxy_types}
                    self.proxies.append(proxy)

            proxies_obj.close()

    def return_proxies(self, refresh=False):
        if refresh:
            self.proxies = []
            self.run()
        return self.proxies