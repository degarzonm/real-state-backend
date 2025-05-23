from .server import PropertyServer


def main():
    """Función principal para iniciar el servidor de propiedades."""
    server = PropertyServer()
    server.serve_forever()


if __name__ == "__main__":
    main()
