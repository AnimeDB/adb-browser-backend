from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

from tipper import Poller

import os
import ConfigParser


class Options(usage.Options):
    optFlags = [
        ["install", "i", "Execute the MySQL initialization code on the master DB."],
    ]
    
    optParameters = [
        ["settings", "s", 'config.ini', "Path to the configuration file"],
    ]
    
    def postOptions(self):
        settings = os.path.realpath(self['settings'])
        
        try:
            config = ConfigParser.SafeConfigParser()
            config.readfp(open(settings))
        except Exception as e:
            raise usage.UsageError("The specified settings file could not be" \
                    " loaded (path: {}, error: {})".format(settings, str(e)))
        else:
            self['settings'] = config


class PollerFactory(object):
    implements(IServiceMaker, IPlugin)
    
    tapname = "tipper"
    description = "Poller service for the AnimeDB MySQL backend which publish" \
                        " release updates to a service exposed over BERT-RPC"
    options = Options
    
    def makeService(self, options):
        service = Poller(options['settings'])
        
        return service

serviceFactory = PollerFactory()