import os
import txamqp.spec


default_spec = 'conf/amqp0-9-1.xml'

def get_spec(spec=None):
    if not spec:
        spec = os.path.join(os.path.dirname(os.path.realpath(__file__)), default_spec)
    
    return txamqp.spec.load(spec)