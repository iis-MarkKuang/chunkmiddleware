import SimpleHTTPServer
import SocketServer
import re
import json
import config
import requests
import copy
import time
import urlparse

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer, test as _test
from SocketServer import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    completion = 0.00
    pass

def htc(m):
    return chr(int(m.group(1), 16))


def urldecode(url):
    rex = re.compile('%([0-9a-hA-H][0-9a-hA-H])', re.M)
    return rex.sub(htc, url)


class SETHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print "GET"
        print self.headers
        if self.path == "/progress":
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Send the html message
            self.wfile.write(str(ThreadedHTTPServer.completion))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Send the html message
            result = {}
            result["error"] = "wrong request path"
            self.wfile.write(json.dumps(result))
        return

    def do_POST(self):
        print "POST"
        print self.headers
        if self.path.startswith("/skus/check"):
	    batch_size_param = None
	    interval_param = None
            if '?' in self.path:
                self.queryString=self.path.split('?',1)[1]    
                #name=str(bytes(params['name'][0],'GBK'),'utf-8')     
                params=urlparse.parse_qs(self.queryString)     
                print(params)     
                batch_size_param=params["batch_size"][0] if "batch_size" in params else None 
                interval_param=params["interval"][0] if "interval" in params else None
	    try:
		batch_size = int(batch_size_param) if batch_size_param is not None else config.batch_size
	    except Exception, e:
		print e.message
		batch_size = config.batch_size

	    try:
		interval = int(interval_param) if interval_param is not None else config.interval 
            except Exception, e:
		print e.message
		interval = config.interval
					

	    length = int(self.headers.getheader('content-length'))
            qs = self.rfile.read(length)
            body = urldecode(qs)
            print body
            try:
                json_obj = json.loads(body)
                epc_sku_obj = {}
                size = 0
                total, curr = len(json_obj[config.chunk_field].items()), 0
                for attribute, value in json_obj[config.chunk_field].iteritems():
                    print attribute
                    print value
                    curr += 1
                    epc_sku_obj[attribute] = value
                    size += 1
                    ThreadedHTTPServer.completion = round(curr / float(total), 2)
                    print ThreadedHTTPServer.completion
                    if size == batch_size:
                        json_obj_current = copy.deepcopy(json_obj)
                        json_obj_current[config.chunk_field] = epc_sku_obj
                        json_obj_current[config.chunk_field] = epc_sku_obj
                        requests.post(config.dest_url + ":" + str(config.dest_port), data=json.dumps(json_obj_current))
                        time.sleep(interval)
                        size = 0
                        epc_sku_obj = {}

                json_obj_current = copy.deepcopy(json_obj)
                json_obj_current[config.chunk_field] = epc_sku_obj
                requests.post(config.dest_url + ":" + str(config.dest_port) + config.dest_path, data=json.dumps(json_obj_current))


            except Exception, e:
                self.send_response(412)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                result = {}
                result["error"] = e.message
                self.wfile.write(json.dumps(result))
            else:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                result = {}
                result["result"] = "Finished"
                self.wfile.write(json.dumps(result))
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Send the html message
            result = {}
            result["error"] = "wrong request path"
            self.wfile.write(json.dumps(result))

        return

Handler = SETHandler
PORT = config.local_port
httpd = ThreadedHTTPServer(("", PORT), Handler)
print "serving at port", PORT
httpd.serve_forever()

