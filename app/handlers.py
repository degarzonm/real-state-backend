import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs


__all__ = ["make_handler"]


class _PropertyRequestHandler(BaseHTTPRequestHandler):
    """
    Handler concreto para el endpoint `/properties`.
    Se instancia a través de `make_handler`, que inyecta `service`.
    """

    def _send_json(self, code: int, payload):
        """ Helper para enviar una respuesta JSON. 
        Args:
            code (int): Código de estado HTTP.
            payload (dict): Cuerpo de la respuesta en formato JSON.
        Returns:
            None
        """
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    # Routeo de peticiones HTTP
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path.rstrip("/") == "/properties":
            self._handle_properties(parsed)
        else:
            self._send_json(404, {"error": "not_found"})

    # Endpoint: /properties
    def _handle_properties(self, parsed):
        """ Maneja la petición GET a /properties.
        Args:
            parsed (ParseResult): Resultado del parseo de la URL.
        Returns:
            None
        """
        qs = parse_qs(parsed.query or "")

        year = qs.get("year",      [None])[0]
        city = qs.get("city",      [None])[0]
        status_param = qs.get("status",    [])
        page_number = qs.get("page",      [None])[0]
        page_size = qs.get("size",      [None])[0]

        # Permitimos “status=a,b,c” o repetidos ?status=a&status=b
        status = (
            status_param[0].split(",") if len(status_param) == 1
            else status_param or None
        )

        try:
            result = self.server._service.get_properties(
                year=year,
                city=city,
                status=status,
                page_number=page_number,
                page_size=page_size,
            )
            self._send_json(200, result)
        except Exception as exc:
            self._send_json(
                500, {"error": "internal_error", "detail": str(exc)})


def make_handler(service):
    """
    Devuelve una subclase de `BaseHTTPRequestHandler` con la instancia
    `service` inyectada a través del servidor (atributo privado).
    """

    class Handler(_PropertyRequestHandler):
        pass

    return Handler
