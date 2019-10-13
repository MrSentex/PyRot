# PyRot Plugins Support

PyRot have support for plugin for web and proxy gathering. Is very simple to write your own plugin
for increase the functionality of PyRot. If you program a good plugin don't be scared to share it.

## Types - Templates to use
    * proxies
    * web

## Examples

### Proxies
```python
class Main (object): # The name of the class mus be Main.

    NAME = ""
    AUTH = ""
    TYPE = "proxies"
    REFRESH = True
    REFRESH_ELAPSE = "50m" # m = Minutes | h = Hours | s = Seconds | d = Days

    def __init__(self, config_instance): # Build-In
        # Config instance to give to the plugin the capability to read the configuration file.
        self.config = config_instance

        # Default vars
        self.proxies = [] # [{"host" : "127.0.0.1", "port" : 1234}]

        # Personal vars for te plugin or autorun things (Like configuration, etc...)
        self.file = "" # Proxies list (host:port => format)

    def run (self): # Build-In
        get_proxies_from_file()

    def get_proxies_from_file(self):
        with open(self.file, "r") as proxies_obj:
            lines = proxies_obj.readlines()

            for line in lines:
                line = line.split(":")

                if len(line) > 1 and len(line) < 2:
                    proxy = {"host" : line[0], "port" : line[1]}
                    self.proxies.append(proxys)

              proxies_obj.close()

    def return_proxies(self, refresh=False):
        if refresh:
            self.proxies = []
            run()
        return self.proxies
```