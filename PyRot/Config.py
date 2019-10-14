from os import path

CONFIG_FILE = "config.cfg"

class Config (object):
    def __init__(self):
        self.plain_text = None
        self.parsed_config = {}

        self.needed_params = [
            "PluginDir",
            "ProxyBindAddress",
            "ProxyBindPort",
            "DefaultProxyType",
            "CheckUrl",
        ]

        self.read()

    def remove_last_espace(self, string):
        if string[len(string)-1:len(string)] == " ":
            return string[:-1]

        return string

    def remove_first_espace(self, string):
        if len(string) < 2:
            return string

        if string[0:1] == " ":
            return string[1:]

        return string

    def read(self):
        if not path.exists(CONFIG_FILE):
            raise TypeError("Config file '{}' not found in app root path.".format(CONFIG_FILE))
        if not path.isfile(CONFIG_FILE):
            raise TypeError("Config file '{}' is not a file.".format(CONFIG_FILE))

        with open(CONFIG_FILE, "r") as config_obj:
            lines = config_obj.read().split("\n")

            for line in lines:

                if line.startswith("#"):
                    continue

                conf = line.replace("\n", "").replace("\r", "").split("=")
                var = None
                value = None

                if len(conf) == 0:
                    pass
                elif len(conf) < 2 and len(conf) >= 1:
                    var = self.remove_last_espace(conf[0])
                    value = None
                else:
                    var = self.remove_last_espace(conf[0])
                    value = self.remove_first_espace("".join(conf[1:len(conf)]))

                if value != None:
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.lower() == "none":
                        value = None

                try:
                    value = int(value)
                except Exception:
                    pass

                if value is not None and type(value) is str:
                    value = value.replace("\r", "")


                self.parsed_config[var] = value

            config_obj.close()

        for param in self.needed_params:
            if self.parsed_config.get(param) is None:
                raise TypeError("Config file is not complete. Var '{}' is not set and must be specified.".format(param))

    def __getitem__(self, item):
        return self.parsed_config.get(item)

    def run_on_start(self):
        return

    def set_instances(self, instances):
        self.instances = instances