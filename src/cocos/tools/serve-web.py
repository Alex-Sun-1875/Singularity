"""Local build preview using Python's standard static-file server."""
from argparse import ArgumentParser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

parser = ArgumentParser()
parser.add_argument('--port', type=int, default=7458)
parser.add_argument('--directory', type=Path, required=True)
args = parser.parse_args()
directory = args.directory.resolve(strict=True)
if not (directory / 'index.html').is_file():
    parser.error('The directory must contain a completed Web build.')

class PreviewHandler(SimpleHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

class PreviewServer(ThreadingHTTPServer):
    # A chapter starts several parallel asset requests per browser. The standard
    # server's queue of five refused connections during concurrent reviews.
    request_queue_size = 128

with PreviewServer(('127.0.0.1', args.port), partial(PreviewHandler, directory=str(directory))) as server:
    print(f'Local game: http://127.0.0.1:{args.port}/', flush=True)
    server.serve_forever()
