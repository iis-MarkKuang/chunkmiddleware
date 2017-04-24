import SimpleHTTPServer
import SocketServer
import re, config

class TestDownStreamHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        print "GET"
        print self.headers

    def do_POST(self):
        print "POST"
        print self.headers
        length = int(self.headers.getheader('content-length'))
        print self.rfile.read(length)
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        # Send the html message
        self.wfile.write("Hello World !")
        return

httpd_downstream = SocketServer.TCPServer(("", config.dest_port), TestDownStreamHandler)
print "test downstream serving at port", config.dest_port
httpd_downstream.serve_forever()