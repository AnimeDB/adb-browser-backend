from zope.interface import implements

from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker

import egocentric
import egocentric.options


class ControllerFactory(object):
    implements(IServiceMaker, IPlugin)
    
    tapname = "egocentric"
    description = "Controller for the AnimeDB backend which waits for release-related" \
                    " events to aggregate and publish the information to the frontend."
    options = egocentric.options.Options
    
    def makeService(self, options):
        service = egocentric.Controller(options, options['settings'])
        
        return service


serviceFactory = ControllerFactory()