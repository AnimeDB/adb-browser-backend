from zope.interface import implements

from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

import tipper
import tipper.options


class PollerFactory(object):
    implements(IServiceMaker, IPlugin)
    
    tapname = "tipper"
    description = "Poller service for the AnimeDB MySQL backend which publishes" \
                        " release updates to a service exposed over BERT-RPC"
    options = tipper.options.Options
    
    def makeService(self, options):
        service = tipper.Poller(options, options['settings'])
        
        return service


serviceFactory = PollerFactory()