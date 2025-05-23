from http.server import HTTPServer
from typing import Optional

from .handlers import make_handler
from .services import PropertyService
from . import config


__all__ = ["PropertyServer"]


class PropertyServer:
    """
    Encapsula la vida del `HTTPServer` para simplificar tests y arranque.
    """

    def __init__(
        self,
        host: str = config.SERVER_HOST,
        port: int = config.SERVER_PORT,
        service: Optional[PropertyService] = None,
    ):
        if service is None:
            service = PropertyService()

        handler_cls = make_handler(service)
        self._httpd = HTTPServer((host, port), handler_cls)
        # Exponer el servicio al handler
        self._httpd._service = service  # type: ignore[attr-defined]

    def serve_forever(self):  # Bloqueante
        """Inicia el servidor HTTP y espera peticiones."""
        addr = self._httpd.server_address
        print(f"🟢 Server Properties Listening on http://{addr[0]}:{addr[1]}")
        try:
            self._httpd.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            self._httpd.server_close()
            print("⛔️ Properties Server stopped.")
