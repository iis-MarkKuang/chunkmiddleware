# chunkmiddleware
a middleware based on python http server to handle post request with large json object and divide the json into small chunks and send them per interval


# How to run
if you don't have python 2.7 installed, please install python 2.7
if you don't have pip installed, please install pip

then

under commandline or shell:
  1. pip install requests
  
  2. cd to the chunkmiddleware folder
  
  3. python chunk.py
  
  4. python downstream.py

chunk.py contains the middleware which separates the large json in your original request into chunks, and send them to downstream.py, which is a dummy bottom request handling system pretending to do the sku checking.

the urls and ports of middleware server and downstream server are all configurable via config.py
config.py also allows you to define the key in json you want to cut into chunks, and interval between requests you want to wait, and the size of each request's json object's chunked field you want it to be.

