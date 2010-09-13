import os
import subprocess
import tempfile
import ConfigParser

from twisted.python import log


def install(config):
    log.msg("Installing needed MySQL structures...")
    
    with open(os.path.join(os.path.dirname(__file__), 'conf', 'install.sql')) as fh:
        sql = fh.read()
    
    query = sql.format(**{
        'master': config.get('database', 'master'),
        'temp': config.get('database', 'temp')
    })
    
    # Create temporary file
    ff, path = tempfile.mkstemp(text=True)
    fh = os.fdopen(ff, 'r+')
    
    # Write configuration values
    tempconfig = ConfigParser.RawConfigParser()
    
    tempconfig.add_section('client')
    tempconfig.set('client', 'user', config.get('database', 'admin-user'))
    tempconfig.set('client', 'password', config.get('database', 'admin-password'))
    
    tempconfig.add_section('mysql')
    tempconfig.set('mysql', 'host', config.get('database', 'host'))
    tempconfig.set('mysql', 'port', config.get('database', 'port'))
    
    tempconfig.write(fh)
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