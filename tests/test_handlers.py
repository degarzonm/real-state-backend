import json
import threading
import time
import unittest
from http.client import HTTPConnection

from app.server import PropertyServer


class DummyService:
    """Mock del servicio para el endpoint."""

    def __init__(self):
        self.last_call = None

    def get_properties(self, **kwargs):
        self.last_call = kwargs
        return [{
            "city":        "bogota",
            "address":     "Calle Falsa 123",
            "status":      "en_venta",
            "price":       350_000_000,
            "year":        2019,
            "description": "Mock property description"
        }]


class TestHTTPHandlers(unittest.TestCase):

    def setUp(self):
        """Inicia el servidor HTTP en un hilo separado."""
        self.mock_service = DummyService()
        self.server = PropertyServer(
            host="127.0.0.1", port=0, service=self.mock_service)
        self.port = self.server._httpd.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        # Esperar a que arranque
        time.sleep(0.1)

    def _request(self, path):
        """Realiza una petición HTTP al servidor."""
        conn = HTTPConnection("127.0.0.1", self.port)
        conn.request("GET", path)
        resp = conn.getresponse()
        body = resp.read().decode()
        return resp.status, json.loads(body)

    def test_properties_endpoint(self):
        """Prueba el endpoint de propiedades."""
        print("Running test_properties_endpoint...")
        status, body = self._request("/properties?city=bogota&page=2")
        self.assertEqual(status, 200)
        self.assertEqual(body, [{
            "city":        "bogota",
            "address":     "Calle Falsa 123",
            "status":      "en_venta",
            "price":       350_000_000,
            "year":        2019,
            "description": "Mock property description"
        }])
        # confirmar parámetro pasado al servicio
        self.assertEqual(self.mock_service.last_call["city"], "bogota")
        self.assertEqual(self.mock_service.last_call["page_number"], "2")
        print("test_properties_endpoint passed.\n")

    def test_not_found(self):
        """Prueba una ruta no válida."""
        print("Running test_not_found...")
        status, body = self._request("/unknown")
        self.assertEqual(status, 404)
        self.assertEqual(body["error"], "not_found")
        print("test_not_found passed.\n")


if __name__ == "__main__":
    unittest.main()
