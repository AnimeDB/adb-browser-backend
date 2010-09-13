import txamqp.protocol
import txamqp.client
import txamqp.content

from twisted.internet import defer, task, protocol


class Publisher(txamqp.protocol.AMQClient, object):
    def connectionMade(self):
        user = self.factory.config.get('amqp', 'user')
        password = self.factory.config.get('amqp', 'password')
        
        d = self.authenticate(user, password)
        d.addCallback(self._setup)
        
        super(Publisher, self).connectionMade()
    
    def connectionLost(self, reason):
        try:
            self.publishing.stop()
        except AttributeError:
            pass
        
        super(Publisher, self).connectionLost(reason)
    
    @defer.inlineCallbacks
    def _setup(self, _):
        self.factory.resetDelay()
        
        queue = self.factory.queue
        exchange = self.factory.config.get('amqp', 'exchange')
        routing_key = self.factory.config.get('amqp', 'routing-key')
        
        channel = yield self.channel(1)
        
        yield channel.channel_open()
        yield channel.exchange_declare(exchange=exchange, type="topic", durable=True, auto_delete=False)
        
        self.publishing = task.LoopingCall(self._publish, channel, exchange, routing_key, queue)
        self.publishing.start(0)
    
    @defer.inlineCallbacks
    def _publish(self, channel, exchange, routing_key, queue):
        message = yield queue.get()
        
        content = txamqp.content.Content(str(message))
        
        print message[:30]
        
        try:
            yield channel.basic_publish(
                content=content,
                exchange=exchange,
                routing_key=routing_key
            )
        except txamqp.client.Closed:
            # If the sending failed, put it in the queue
            queue.put(message)


class PublisherFactory(protocol.ReconnectingClientFactory):
    protocol = Publisher
    
    def __init__(self, config, queue, *args, **kwargs):
        self.config = config
        self.queue = queue
        self.args = args
        self.kwargs = kwargs
    
    def buildProtocol(self, addr):
        protocol = self.protocol(*self.args, **self.kwargs)
        protocol.factory = self
        return protocol

