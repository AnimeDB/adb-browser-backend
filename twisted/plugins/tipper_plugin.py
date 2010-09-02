from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

import tipper
import os
import ConfigParser


class Options(usage.Options):
    optFlags = [
        ["install", "i", "Execute the MySQL initialization code on the master DB."],
    ]
    
    optParameters = [
        ["settings", "s", False, "Path to the configuration file"],
    ]
    
    def postOptions(self):
        default = os.path.dirname(os.path.realpath(tipper.__file__))
        default = os.path.join(default, 'conf', 'default.ini')
        
        config = ConfigParser.SafeConfigParser()
        config.readfp(open(default))
        
        if self['settings']:
            settings = os.path.realpath(self['settings'])
            
            try:
                config.readfp(open(settings))
            except Exception as e:
                raise usage.UsageError("The specified settings file could not be" \
                        " loaded (path: {}, error: {})".format(settings, str(e)))
        self['settings'] = config


class PollerFactory(object):
    implements(IServiceMaker, IPlugin)
    
    tapname = "tipper"
    description = "Poller service for the AnimeDB MySQL backend which publish" \
                        " release updates to a service exposed over BERT-RPC"
    options = Options
    
    def makeService(self, options):
        service = tipper.Poller(options['settings'])
        
        return service

serviceFactory = PollerFactory()