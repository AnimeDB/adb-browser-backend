import os
import MySQLdb as db

from twisted.application.service import Service
from twisted.internet import task, threads, defer


class Poller(Service, object):
    
    def __init__(self, options):
        super(Poller, self).__init__()
        
        self.options = options
        self.queue = defer.DeferredQueue()
    
    @defer.inlineCallbacks
    def startService(self):
        super(Poller, self).startService()
        
        # Connect to MySQL server
        options = {
            'host': self.options.get('database', 'host'),
            'port': int(self.options.get('database', 'port')),
            'user': self.options.get('database', 'user'),
            'passwd': self.options.get('database', 'password'),
            'db': self.options.get('database', 'temp'),
        }
        
        self.connection = yield threads.deferToThread(db.connect, **options)
        self.cursor = self.connection.cursor(db.cursors.DictCursor)
        
        self.startPolling()
        self.startProducing()
    
    def startPolling(self):
        def poll(cursor, query):
           cursor.execute(query)
           for row in cursor.fetchall():
               self.queue.put(row)
        
        query = "SELECT * FROM post_updates ORDER BY timestamp ASC LIMIT 0,{}".format(
           int(self.options.get('polling', 'rate')),
        )
        
        self.polling = task.LoopingCall(threads.deferToThread, poll, self.cursor, query)
        self.polling.start(int(self.options.get('polling', 'interval')))
    
    @defer.inlineCallbacks
    def startProducing(self):
        while True:
            event = yield self.queue.get()
            print event['postid']
    
    @defer.inlineCallbacks
    def stopService(self):
        super(Poller, self).stopService()
        
        self.polling.stop()
        
        yield threads.deferToThread(self.cursor.close)
        yield threads.deferToThread(self.connection.close)
    
    def install(self, options):
        # @todo: The following code is only an initial stub, we have to
        #        actually execute the SQL
        
        with open(os.path.join(os.path.dirname(__file__), 'conf', 'install.sql')) as fh:
            sql = fh.read()
        
        print sql.format(**{
            'master': self.options.get('database', 'master'),
            'temp': self.options.get('database', 'temp')
        })
    
    def uninstall(self, options):
        pass
    
    