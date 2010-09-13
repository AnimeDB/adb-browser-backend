# -*- coding: utf-8 -*-

import re
import urlparse

class PostParser(object):
    url_regex = r'''(?xi)
        \b
        (                           # Capture 1: entire matched URL
          (?:
            [a-z][\w-]+:                # URL protocol and colon
            (?:
              /{1,3}                        # 1-3 slashes
              #|                             #   or
              #[a-z0-9%]                     # Single letter or digit or '%'
                                            # (Trying not to match e.g. "URI::Escape")
            )
            |                           #   or
            www\d{0,3}[.]               # "www.", "www1.", "www2." … "www999."
            |                           #   or
            [a-z0-9.\-]+[.][a-z]{2,4}/  # looks like domain name followed by a slash
          )
          (?:                           # One or more:
            [^][\s()^<>]+                      # Run of non-space, non-()<>
            |                               #   or
            \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
          )+
          (?:                           # End with:
            \(([^\s()<>]+|(\([^\s()<>]+\)))*\)  # balanced parens, up to 2 levels
            |                                   #   or
            [^\s`!()\[\]{};:'".,<>?«»“”‘’]        # not a space or one of these punct chars
          )
        )'''
        
    groups = {
        'wikipedia': r'^http://(?:[a-z]{2,3}.)?wikipedia.org/',
        'megavideo': r'^http://(?:www.)?megavideo.com/',
    }
    
    def __init__(self, text):
        self.text = text
    
    def urls(self):
        urls = set([u[0] for u in re.findall(self.url_regex, self.text)])
        groups = {}
        
        for url in urls:
            matched = False
            for group, pattern in self.groups.iteritems():
                if re.match(pattern, url):
                    matched = True
                    groups.setdefault(group, set()).add(url)
            if not matched:
                groups.setdefault('other', set()).add(url)
        
        return groups
        