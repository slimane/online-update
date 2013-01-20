# -*- coding: utf-8 -*-

from datetime import datetime
import logging
import os
import sys

if sys.version_info >= (3, 0, 0):
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError
else:
    from urllib2 import HTTPError, Request, urlopen

logger = logging.getLogger('downloader')

def header(pivot_time):
    if pivot_time == 0:
        return {}
    else:
        # FIXME: "9 * 3600" must be got from timezone.
        dt = datetime.fromtimestamp(pivot_time - 9 * 3600)
        since = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
        return { 'If-Modified-Since': since }

def save_as(response, path):
    # Dig a directory if not exists.
    (dir, name) = os.path.split(path)
    if len(dir) > 0 and not os.path.exists(dir):
        os.makedirs(dir)
    # Write response body to a file.
    f = open(path, 'wb')
    try:
        f.write(response.read())
    finally:
        f.close()

class Downloader:

    def __init__(self, remote_url=None, local_cache=None, pivot_time=0):
        if not remote_url:
            raise Exception('\'remote_url\' is not provided.')
        if not local_cache:
            raise Exception('\'local_cache\' is not provided.')
        self.remote_url = remote_url
        self.local_cache = local_cache
        self.pivot_time = pivot_time

    def has(self):
        return os.path.exists(self.local_cache)

    def download(self):
        # Emit a HTTP request.
        try:
            request = Request(self.remote_url, None, header(self.pivot_time))
            response = urlopen(request)
        except HTTPError as e:
            response = e
        # Parse a HTTP response.
        try:
            if response.code == 304:
                # No updates.
                return False
            elif response.code == 200:
                # Found update, download it.
                tmp = self.local_cache + '.download'
                save_as(response, tmp)
                self.clear()
                os.rename(tmp, self.local_cache)
            else:
                raise Exception('unexpected response: %d' % response.code)
        finally:
            if response:
                response.close()
        return True

    def clear(self):
        if self.has():
            os.remove(self.local_cache)
