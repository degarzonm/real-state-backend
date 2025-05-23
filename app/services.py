from . import data_access as _default_da
from . import config as _default_config_module


class PropertyService:

    def __init__(self, data_access_layer=_default_da, config_module=_default_config_module):
        """
        Args:
            data_access_layer: objeto (módulo o clase) con
                               `query_filtered_properties(**kwargs)`.
            config_module:    módulo o mock con las constantes DEFAULT_*.
        """
        self.data_access = data_access_layer
        self.cfg = config_module

    def get_properties(self, year=None, city=None, status=None,
                       page_number=None, page_size=None):
        """
        Obtiene propiedades disponibles, filtradas y paginadas.

        Args:
            year (int, str, optional): Año de construcción de la propiedad.
            city (str, optional): Ciudad de la propiedad.
            status (str, list, optional): Estado de la propiedad. Puede ser una cadena o una lista de cadenas.
            page_number (int, str, optional): Número de página solicitada.
            page_size (int, str, optional): Tamaño de la página.

        Returns:
            list: Lista de propiedades que coinciden con los filtros y paginación.
        """
        status_list = None
        if status:
            if isinstance(status, str):
                status_list = [status]
            elif isinstance(status, list):
                status_list = status
        if year:
            try:
                year = int(year)
                if year < 1700 or year > 2050:  # Inmuebles antiguos/futuros
                    print("Advertencia: year fuera de rango. Usando valor por defecto.")
                    year = self.cfg.DEFAULT_YEAR_FILTER
            except ValueError:
                print("Advertencia: year no es un entero válido. No se aplicara filtro.")
                year = None

        # Validar y convertir parámetros de paginación
        if page_number is None:
            page_number = self.cfg.DEFAULT_PAGE_NUMBER
        if page_size is None:
            page_size = self.cfg.DEFAULT_PAGE_SIZE
        try:
            page_number = int(page_number)
            page_size = int(page_size)
            if page_number < 1:
                page_number = self.cfg.DEFAULT_PAGE_NUMBER
            if page_size < 1 or page_size > 100:
                page_size = self.cfg.DEFAULT_PAGE_SIZE
        except ValueError:
            # Manejar error o usar defaults si no son números válidos
            print(
                "Advertencia: page_number o page_size no son enteros válidos. Usando defaults.")
            page_number = self.cfg.DEFAULT_PAGE_NUMBER
            page_size = self.cfg.DEFAULT_PAGE_SIZE

        properties_data = self.data_access.query_filtered_properties(
            year=year,
            city=city,
            status_names=status_list,
            page_number=page_number,
            page_size=page_size
        )

        if properties_data is None:
            print("Advertencia: data_access.query_filtered_properties devolvió None.")
            return []

        return properties_data
