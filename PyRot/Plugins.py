from os import path, listdir, getcwd
import importlib

class Plugins (object):
    def __init__(self):
        self.instances = None

        self.plugins = {
            "proxies" : []
        }

    def main(self):
        self.instances.get("Console").print_c(self.instances.get("Console").INFO, "Loading plugins...")
        files_in_dir = listdir(path.join(getcwd(), self.instances.get("Config")["PluginDir"]))

        plugins_length = 0
        plugins_loaded = 0

        for file in files_in_dir:
            if file != "__init__.py":
                if file.endswith(".py"):

                    plugins_length += 1

                    try:
                        plugin_package = importlib.import_module("{}.{}".format(self.instances.get("Config")["PluginDir"], file.replace(".py", "")))
                        plugin = plugin_package.Main(self.instances.get("Config"))

                        if self.plugins.get(plugin.TYPE) is None:
                            continue
                        else:
                            self.plugins.get(plugin.TYPE).append(plugin)
                            plugins_loaded += 1

                    except Exception as e:
                        self.instances.get("Console").print_c(self.instances.get("Console").ERROR, "An error ocurred while loading plugin '{}'. ({})".format(file, str(e)))
                        pass

        self.instances.get("Console").print_c(self.instances.get("Console").CORRECT , "Done!. {}/{} plugins loaded.".format(plugins_loaded, plugins_length))

    def get_plugins(self, type):
        return self.plugins.get(type)

    def set_instances(self, instances):
        self.instances = instances
    def run_on_start(self):
        self.main()
        return