import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from PIL import Image
import server

class SecurityAndContract(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(server.app, base_url='http://127.0.0.1:4174')
        self.headers = {'Origin':'http://127.0.0.1:4173', 'X-Seller-Frame':'local'}
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'fake.onnx'
        self.path.touch()
        self.model = patch.object(server, 'MODEL', self.path)
        self.model.start()
    def tearDown(self):
        self.model.stop(); self.temp.cleanup()
    def post(self, data=b'bad', headers=None):
        return self.client.post('/api/remove-background', files={'image':('image.png',data,'image/png')}, headers=self.headers if headers is None else headers)
    def test_health(self):
        self.assertTrue(self.client.get('/api/health').json()['ready'])
    def test_foreign_origin(self):
        self.assertEqual(self.post(headers={'Origin':'https://evil.example','X-Seller-Frame':'local'}).status_code,403)
    def test_missing_origin(self):
        self.assertEqual(self.post(headers={'X-Seller-Frame':'local'}).status_code,403)
    def test_missing_header(self):
        self.assertEqual(self.post(headers={'Origin':'http://127.0.0.1:4173'}).status_code,403)
    def test_bad_host(self):
        self.assertEqual(self.client.get('/api/health',headers={'Host':'evil.example'}).status_code,403)
    def test_preflight(self):
        r=self.client.options('/api/remove-background',headers=self.headers)
        self.assertEqual(r.status_code,204)
        self.assertEqual(r.headers['Access-Control-Allow-Origin'],self.headers['Origin'])
    def test_absent_model(self):
        self.path.unlink(); self.assertEqual(self.post().status_code,503)
    def test_invalid_bytes(self):
        self.assertEqual(self.post().status_code,400)
    def test_oversized(self):
        with patch.object(server,'MAX_BODY',128):
            self.assertEqual(self.post(b'x'*256).status_code,413)
    def test_gif_rejected(self):
        b=io.BytesIO(); Image.new('RGB',(8,8)).save(b,'GIF')
        self.assertEqual(self.post(b.getvalue()).status_code,415)
    def test_pixel_limit(self):
        b=io.BytesIO(); Image.new('RGB',(8,8)).save(b,'PNG')
        with patch.object(server,'MAX_PIXELS',32):
            self.assertEqual(self.post(b.getvalue()).status_code,415)
    def test_busy(self):
        server.LOCK.acquire()
        try:self.assertEqual(self.post().status_code,429)
        finally:server.LOCK.release()
    def test_contract_with_stub_not_model_quality(self):
        b=io.BytesIO(); Image.new('RGBA',(8,8),(255,0,0,128)).save(b,'PNG')
        with patch.object(server,'infer',return_value=b.getvalue()):
            r=self.post(b.getvalue())
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.headers['content-type'],'image/png')
        self.assertEqual(Image.open(io.BytesIO(r.content)).mode,'RGBA')
        self.assertEqual(r.headers['cache-control'],'no-store')
    def test_metadata_not_preserved(self):
        b=io.BytesIO(); Image.new('RGB',(8,8)).save(b,'PNG')
        self.assertEqual(server.decode_image(b.getvalue()).mode,'RGBA')

if __name__=='__main__': unittest.main()
