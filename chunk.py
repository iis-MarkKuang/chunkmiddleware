import SimpleHTTPServer
import SocketServer
import re, json, config, requests, copy, time, urlparse, redis

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


r = redis.Redis(host='127.0.0.1', port=6379)

class SETHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/progress"):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            # Send the html message
	    if '?' in self.path:
		self.queryString=self.path.split('?',1)[1]
		params=urlparse.parse_qs(self.queryString)
		order_no_param = params["order_no"][0] if "order_no" in params else None
		if order_no_param == None:
		    self.send_response(404)
		    self.send_header('Content-type', 'text/html')
		    self.end_headers()
		    # Send the html message
		    result = {}
		    result["error"] = "missing param order_no"
		    Self.wfile.write(json.dumps(result))
            	else:
		    total, curr = r.get(order_no_param + "_total"), r.get(order_no_param + "_curr")
		    self.wfile.write(round(int(curr) / float(total), 2))
	    else:
		self.send_response(404)
		self.send_header('Content-type', 'text/html')
		self.end_headers()
		result = {}
		result["error"] = "missing param order_no"
		Self.wfile.write(json.dumps(result))

            #self.wfile.write(str(ThreadedHTTPServer.completion))
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
		order_no = json_obj["main"]["orderno"]
                epc_sku_obj = {}
                size = 0
                total, curr = len(json_obj[config.chunk_field].items()), 0
		redis_total = r.get(order_no + "_total")
		if redis_total != None:
		    r.setex(order_no + "_total", total + int(redis_total), 86400)
		else:
		    r.setex(order_no + "_curr", 0, 86400)
		    r.setex(order_no + "_total", total, 86400)
		    print r.get(order_no + "_total")
		
		for attribute, value in json_obj[config.chunk_field].iteritems():
                    curr += 1
                    r.incr(order_no + "_curr")
		    print r.get(order_no + "_curr")
	            epc_sku_obj[attribute] = value
                    size += 1
                    #ThreadedHTTPServer.completion = round(curr / float(total), 2)
                    
                    if size == batch_size:
                        json_obj_current = copy.deepcopy(json_obj)
                        json_obj_current[config.chunk_field] = epc_sku_obj
			json_obj_final = {}
			json_obj_final["param"] = json.dumps(json_obj_current) 
			#response_inner = requests.post(config.dest_url + ":" + str(config.dest_port), data=json_obj_final)
                        response_inner = requests.post("http://139.196.183.93:8088/wms/wsAction_doInventorySubmit.action", data=json_obj_final)
			print "sending: " + json.dumps(json_obj_final)
			print response_inner.content
			print response_inner.status_code
			time.sleep(interval)
                        size = 0
                        epc_sku_obj = {}

                json_obj_current = copy.deepcopy(json_obj)
                json_obj_current[config.chunk_field] = epc_sku_obj
		json_obj_final = {}
		json_obj_final["param"] = json.dumps(json_obj_current)
                #response = requests.post(config.dest_url + ":" + str(config.dest_port) + config.dest_path, data=json_obj_final)
		response = requests.post("http://139.196.183.93:8088/wms/wsAction_doInventorySubmit.action", data=json_obj_final)
		print "sending: " + json.dumps(json_obj_final)
		print response.text

            except Exception, e:
		raise
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

