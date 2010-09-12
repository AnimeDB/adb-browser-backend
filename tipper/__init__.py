import os
import subprocess
import tempfile
import ConfigParser

import MySQLdb as db

from twisted.application.service import Service
from twisted.internet import task, threads, defer, reactor
from twisted.python import log


class Poller(Service, object):
    
    def __init__(self, options, config):
        super(Poller, self).__init__()
        
        self.options = options
        self.config = config
        self.queue = defer.DeferredQueue()
    
    def privilegedStartService(self):
        if self.options['install']:
            self.install()
    
    @defer.inlineCallbacks
    def startService(self):
        super(Poller, self).startService()
        
        # Connect to MySQL server
        config = {
            'host': self.config.get('database', 'host'),
            'port': int(self.config.get('database', 'port')),
            'user': self.config.get('database', 'user'),
            'passwd': self.config.get('database', 'password'),
            'db': self.config.get('database', 'temp'),
        }
        
        self.connection = yield threads.deferToThread(db.connect, **config)
        self.cursor = self.connection.cursor(db.cursors.DictCursor)
        
        self.startPolling()
        self.produce()
    
    def startPolling(self):
        def poll(cursor, query):
           cursor.execute(query)
           for row in cursor.fetchall():
               self.queue.put(row)
        
        query = "SELECT * FROM post_updates ORDER BY timestamp ASC LIMIT 0,{}".format(
           int(self.config.get('polling', 'rate')),
        )
        
        self.polling = task.LoopingCall(threads.deferToThread, poll, self.cursor, query)
        self.polling.start(int(self.config.get('polling', 'interval')))
    
    @defer.inlineCallbacks
    def produce(self):
        event = yield self.queue.get()
        print event['postid']
        
        reactor.callLater(0, self.produce)
    
    @defer.inlineCallbacks
    def stopService(self):
        super(Poller, self).stopService()
        
        self.polling.stop()
        
        yield threads.deferToThread(self.cursor.close)
        yield threads.deferToThread(self.connection.close)
    
    def install(self):
        log.msg("Installing needed MySQL structures...")
        
        with open(os.path.join(os.path.dirname(__file__), 'conf', 'install.sql')) as fh:
            sql = fh.read()
        
        query = sql.format(**{
            'master': self.config.get('database', 'master'),
            'temp': self.config.get('database', 'temp')
        })
        
        # Create temporary file
        ff, path = tempfile.mkstemp(text=True)
        fh = os.fdopen(ff, 'r+')
        
        # Write configuration values
        config = ConfigParser.RawConfigParser()
        
        config.add_section('client')
        config.set('client', 'user', self.config.get('database', 'admin-user'))
        config.set('client', 'password', self.config.get('database', 'admin-password'))
        
        config.add_section('mysql')
        config.set('mysql', 'host', self.config.get('database', 'host'))
        config.set('mysql', 'port', self.config.get('database', 'port'))
        
        config.write(fh)
        fh.flush()
        
        # Call MySQL subprocess
        process = subprocess.Popen(
            ['mysql', '--defaults-extra-file=%s' % path, '--batch'],
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        
        # Execute query
        out = process.communicate(query)
        
        # Check result
        if process.wait():
            log.msg("Install failed")
            log.msg(' - stdout: {}'.format(out[0]))
            log.msg(' - stderr: {}'.format(out[1]))
        else:
            log.msg("Install succeeded")
            
        # Clean up
        fh.close()
        os.remove(path)
    
    