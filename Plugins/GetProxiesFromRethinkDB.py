from rethinkdb import RethinkDB
import time

class Main (object): # The name of the class must be Main.

    NAME = "GetProxiesFromRethinkDB"
    AUTH = "Thiplol"
    TYPE = "proxies"
    REFRESH = True
    REFRESH_ELAPSE = "10s" # m = Minutes | h = Hours | s = Seconds | d = Days

    def __init__(self, config_instance): # Build-In
        # Config instance to give to the plugin the capability to read the configuration file.
        self.config = config_instance

        # Default vars
        self.proxies = [] # [{"host" : "127.0.0.1", "port" : 1234}]

        # Personal vars for te plugin or autorun things (Like configuration, etc...)
        self.r = RethinkDB()
        self.host = yourrethinkdbip
        self.port = yourrethinkdbport
        while True:
            try:
                print("Trying to connect to database.")
                self.connection = self.r.connect(host=self.host, port=self.port, db="proxyscrape")
                print("Successfully connected to database.")
            except Exception as e:
                print(e)
                print("Failed to connect to database, retrying...")
                time.sleep(1)
                continue
            break
        self.file_proxy_types = "socks4" # Types -> socks4, socks5, http, https

    def run (self): # Build-In
        self.get_proxies_from_file()

    def get_proxies_from_file(self):
        while True:
            try:
                dbproxies = self.r.table("proxies").filter((self.r.row["last_seen"] >= (time.time() - 15)) & (self.r.row["protocol"] == self.file_proxy_types) & (self.r.row["timeout"] <= 5000) & (self.r.row["uptime"] >= 50) & (self.r.row["alive"] == True)).run(self.connection)

            except Exception as e:
                if "Connection is closed" in str(e):
                    print("Connection to database lost... retrying to connect")
                    while True:
                        try:
                            self.connection = self.r.connect(host=self.host, port=self.port, db="proxyscrape")
                        except Exception as e:
                            print(e)
                            print("Failed to connect to database, retrying...")
                            time.sleep(1)
                            continue
                        break
                    continue
                else:
                    print(e)
                    print("Selecting proxies from database failed, retrying...")
                    time.sleep(1)
                    continue
            break
        for dbproxy in dbproxies:
            dbproxy = dbproxy["proxy"].split(":")
            if len(dbproxy) == 2:
                proxy = {"host" : dbproxy[0], "port" : dbproxy[1], "type" : self.file_proxy_types}
                self.proxies.append(proxy)


    def return_proxies(self, refresh=False):
        if refresh:
            self.proxies = []
            self.run()
        return self.proxies
