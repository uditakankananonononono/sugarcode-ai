import threading
from http.server import BaseHTTPRequestHandler,HTTPServer
import pytest
from sugarcode.llm.providers import ChatClient,ProviderError

@pytest.fixture
def endpoint():
 class Handler(BaseHTTPRequestHandler):
  payload=b'{}'
  def do_POST(self):
   self.send_response(200);self.end_headers();self.wfile.write(self.payload)
  def log_message(self,*args):pass
 server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever);thread.start()
 yield Handler,ChatClient('test',f'http://127.0.0.1:{server.server_port}','test','local')
 server.shutdown();thread.join();server.server_close()

@pytest.mark.parametrize('payload',[b'[]',b'{bad',b'\xff',b'{"choices":[42]}',b'{"choices":[{"message":42}]}',b'['*2000+b'0'+b']'*2000,b'x'*1000001],ids=['array','invalid-json','invalid-utf8','choice-shape','message-shape','deep-json','oversize'])
def test_actual_http_bad_response_is_provider_refusal(endpoint,payload):
 handler,client=endpoint;handler.payload=payload
 with pytest.raises(ProviderError,match='response'):client.chat([{'role':'user','content':'test'}])

def test_actual_http_message_still_returns(endpoint):
 handler,client=endpoint;handler.payload=b'{"choices":[{"message":{"content":"42"}}]}'
 assert client.chat([])=={'content':'42'}
