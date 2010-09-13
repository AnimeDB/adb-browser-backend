import txbert
import txamqp
import txamqp.queue
from txbert.module import DecoratedModuleMixin

from twisted.application.service import Service
from twisted.internet import defer, reactor
from twisted.python import log
from twisted.internet.protocol import ClientCreator

from egocentric.parser import PostParser

from backend.amqp import get_spec


expose = DecoratedModuleMixin.expose

class Controller(Service, DecoratedModuleMixin):
    
    def __init__(self, options, config):
        super(Controller, self).__init__()
        
        self.options = options
        self.config = config
    
    @expose
    def insert(self, postid, threadid, userid, content, timestamp):
        log.msg("Release #{} added".format(threadid))
        
        parser = PostParser(content)
        import pprint
        pprint.pprint(parser.urls())
    
    @expose
    def update(self, id):
        print "Updated", id
    
    @expose
    def delete(self, id):
        print "Deleted", id
    
    @defer.inlineCallbacks
    def startService(self):
        super(Controller, self).startService()
        
        # Create AMQP connection
        spec = get_spec()
        delegate = txamqp.client.TwistedDelegate()
        vhost = '/'
        host = 'localhost'
        port = 5672
        exchange = 'bert'
        routing_key = 'test'
        
        conn = yield ClientCreator(reactor, txamqp.protocol.AMQClient,
            delegate=delegate, vhost=vhost, spec=spec).connectTCP(host, port)
        
        yield conn.authenticate('guest', 'guest')
        channel = yield conn.channel(1)
        
        yield channel.channel_open()
        yield channel.exchange_declare(exchange=exchange, type="fanout", durable=False, auto_delete=False)
        queue = yield channel.queue_declare(queue='cast', durable=False, exclusive=True, auto_delete=True)
        yield channel.queue_bind(queue=queue.queue, exchange='bert')
        tag = yield channel.basic_consume(consumer_tag='functions', queue=queue.queue, no_ack=True)
        queue = yield conn.queue('functions')
        
        print "\n" * 5
        
        while True:
            try:
                msg = yield queue.get()
            except txamqp.queue.Closed:
                break
            
            #print dir(msg)
            #print msg.fields
            #print msg.method
            print repr(msg.content)
            print msg.content.weight()
            
            
            print "\n" * 5
            #reactor.stop()
            #break
    
    #@defer.inlineCallbacks
    def stopService(self):
        super(Controller, self).stopService()

