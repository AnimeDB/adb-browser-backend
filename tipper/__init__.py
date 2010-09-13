import json
import time

import MySQLdb as db

from twisted.application.service import Service
from twisted.internet import task, threads, defer, reactor
from twisted.python import log

from txamqp.client import TwistedDelegate

from backend.amqp import get_spec

from tipper.publisher import PublisherFactory
from tipper.installer import install


class Poller(Service, object):
    def __init__(self, options, config):
        super(Poller, self).__init__()
        
        self.options = options
        self.config = config
        
        self.polling_call = None
        self.sql_connection = None
        self.publisher_factory = None
    
    def privilegedStartService(self):
        if self.options['install']:
            install(self.config)
    
    @defer.inlineCallbacks
    def startService(self):
        super(Poller, self).startService()
        
        queue = defer.DeferredQueue()
        
        # Init AMQP connection
        kwargs = {
            'config': self.config,
            'queue': queue,
            'delegate': TwistedDelegate(),
            'vhost': self.config.get('amqp', 'vhost'),
            'spec': get_spec(),
        }
        
        self.publisher_factory = PublisherFactory(**kwargs)
        reactor.connectTCP(
            self.config.get('amqp', 'host'),
            int(self.config.get('amqp', 'port')),
            self.publisher_factory
        )
        
        # Init MySQL connection
        kwargs = {
            'host': self.config.get('database', 'host'),
            'port': int(self.config.get('database', 'port')),
            'user': self.config.get('database', 'user'),
            'passwd': self.config.get('database', 'password'),
            'db': self.config.get('database', 'temp'),
            'use_unicode': True
        }
        
        self.sql_connection = yield threads.deferToThread(db.connect, **kwargs)
        
        def poll(cursor, query, rate):
            cursor.execute(query, (rate,))
            for row in cursor.fetchall():
                row = json.dumps(row)
                threads.blockingCallFromThread(reactor, queue.put, row)
        
        self.polling_call = task.LoopingCall(
            threads.deferToThread,
            poll,
            self.sql_connection.cursor(),
            "SELECT * FROM post_updates ORDER BY timestamp ASC LIMIT 0,%d",
            int(self.config.get('polling', 'rate'))
        )
        self.polling_call.start(int(self.config.get('polling', 'interval')))
    
    @defer.inlineCallbacks
    def stopService(self):
        super(Poller, self).stopService()
        
        if self.publisher_factory:
            self.publisher_factory.stopTrying()
        
        if self.polling_call and self.polling_call.running:
            self.polling_call.stop()
            
            log.msg("Waiting for all SQL requests to terminate...")
            yield threads.deferToThread(time.sleep, 2)
        
        if self.sql_connection:
            yield threads.deferToThread(self.sql_connection.close)

    