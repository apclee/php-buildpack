import urllib2
import re
import logging
from subprocess import Popen
from subprocess import PIPE


class Downloader(object):

    def __init__(self, config):
        self._ctx = config
        self._log = logging.getLogger('downloads')
        self._init_proxy()

    def _init_proxy(self):
        handlers = {}
        print 'Setting proxy'
        for key in self._ctx.keys():
            if key.lower().endswith('_proxy'):
                handlers[key.split('_')[0]] = self._ctx[key]
        self._log.debug('Loaded proxy handlers [%s]', handlers)
        openers = []
        if handlers:
            openers.append(urllib2.ProxyHandler(handlers))
            for handler in handlers.values():
                print handler
                if '@' in handler:
                    openers.append(urllib2.ProxyBasicAuthHandler())
            opener = urllib2.build_opener(*openers)
            urllib2.install_opener(opener)

    def download(self, url, toFile):
        print 'Donwloading package...'
        headers = {'User-agent' : 'Mozilla/5.0'}
        req = urllib2.Request(url, None, headers)
        res = urllib2.urlopen(req)
        with open(toFile, 'w') as f:
            f.write(res.read())
        print 'Downloaded [%s] to [%s]' % (url, toFile)
        self._log.info('Downloaded [%s] to [%s]', url, toFile)

    def download_direct(self, url):
        print 'Donwloading package...'
        headers = {'User-agent' : 'Mozilla/5.0'}
        buf = urllib2.Request(url, None, headers).read()
        self._log.info('Downloaded [%s] to memory', url)
        self._log.debug("Downloaded [%s] [%s]", url, buf)
        return buf


class CurlDownloader(object):

    def __init__(self, config):
        self._ctx = config
        self._status_pattern = re.compile(r'^(.*)<!-- Status: (\d+) -->$',
                                          re.DOTALL)
        self._log = logging.getLogger('downloads')

    def download(self, url, toFile):
        cmd = ["curl", "-s",
               "-o", toFile,
               "-w", '%{http_code}']
        for key in self._ctx.keys():
            if key.lower().endswith('_proxy'):
                cmd.extend(['-x', self._ctx[key]])
        cmd.append(url)
        self._log.debug("Running [%s]", cmd)
        proc = Popen(cmd, stdout=PIPE)
        output, unused_err = proc.communicate()
        proc.poll()
        self._log.debug("Curl returned [%s]", output)
        if output and \
                (output.startswith('4') or
                 output.startswith('5')):
            raise RuntimeError("curl says [%s]" % output)
        print 'Downloaded [%s] to [%s]' % (url, toFile)
        self._log.info('Downloaded [%s] to [%s]', url, toFile)

    def download_direct(self, url):
        cmd = ["curl", "-s",
               "-w", '<!-- Status: %{http_code} -->']
        for key in self._ctx.keys():
            if key.lower().endswith('_proxy'):
                cmd.extend(['-x', self._ctx[key]])
        cmd.append(url)
        self._log.debug("Running [%s]", cmd)
        proc = Popen(cmd, stdout=PIPE)
        output, unused_err = proc.communicate()
        proc.poll()
        m = self._status_pattern.match(output)
        if m:
            resp = m.group(1)
            code = m.group(2)
            self._log.debug("Curl returned [%s]", code)
            if (code.startswith('4') or code.startswith('5')):
                raise RuntimeError("curl says [%s]" % output)
            self._log.info('Downloaded [%s] to memory', url)
            self._log.debug('Downloaded [%s] [%s]', url, resp)
            return resp
