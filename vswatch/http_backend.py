#base on the range htp server thingy
from http.server import BaseHTTPRequestHandler, HTTPServer
import functools
import socketserver
import re
from typing import List

__all__ = [ "launch_http_backend"]

BYTE_RANGE_RE = re.compile(r'bytes=(\d+)-(\d+)?$')

def parse_byte_range(byte_range):
    """Returns the two numbers in 'bytes=123-456' or throws ValueError.

    The last number or both numbers may be None.
    """
    if byte_range.strip() == '':
        return None, None

    m = BYTE_RANGE_RE.match(byte_range)
    if not m:
        raise ValueError('Invalid byte range %s' % byte_range)

    first, last = [x and int(x) for x in m.groups()]
    if last and last < first:
        raise ValueError('Invalid byte range %s' % byte_range)
    return first, last


class MyServer(BaseHTTPRequestHandler):
    def __init__(self, inner_stuff, *args, **kwargs):
        self.inner_files = inner_stuff
        super().__init__(*args, **kwargs)

    def handle(self) -> None:
        try:
            return super().handle()
        except:
            pass

    def do_GET(self):
        assert ("Range" in self.headers)
        first,last  = parse_byte_range(self.headers["Range"])
        
        for inner in self.inner_files:
            if self.path == f"/{inner.name}":
                file_len = inner.full_file_len

                if last is None or last >= file_len:
                    last = file_len - 1

                response_length = last-first+1

                self.send_response(206)
                self.send_header("Content-type", "application/octet-stream")
                self.send_header('Content-Range',
                                 'bytes %s-%s/%s' % (first, last, file_len))
                self.send_header('Content-Length', str(response_length))
                self.send_header('Accept-Ranges', 'bytes')
                self.end_headers()

                try:
                    currnt = first
                    left = last+1-first
                    while left > 0:
                        read_size = min(inner.fetch_buffer_size,min(left,file_len - currnt))
                        buf = inner.read(currnt, read_size)
                        if not buf:
                            break
                        self.wfile.write(buf)

                        left -= read_size
                        currnt += read_size
                except:
                    pass
                finally:
                    self.wfile.close()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""


def launch_http_backend(hostName: str,serverPort: int,files: List[object]):
    handler  = functools.partial(MyServer,files)
    webServer = ThreadedHTTPServer((hostName, serverPort), handler)

    return webServer