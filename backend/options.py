import ConfigParser
import inspect
import os

from twisted.python import usage


class SettingsOptions(usage.Options):
    optParameters = [
        ["settings", "s", False, "Path to the configuration file"],
    ]
    
    def getDefaultSettingsPath(self):
        default = inspect.getfile(self.__class__)
        default = os.path.dirname(os.path.realpath(default))
        return os.path.join(default, 'conf', 'default.ini')
    
    def postOptions(self):
        config = ConfigParser.SafeConfigParser()
        config.readfp(open(self.getDefaultSettingsPath()))
        
        if self['settings']:
            settings = os.path.realpath(self['settings'])
            
            try:
                config.readfp(open(settings))
            except Exception as e:
                raise usage.UsageError("The specified settings file could not be" \
                        " loaded (path: {}, error: {})".format(settings, str(e)))
        self['settings'] = config