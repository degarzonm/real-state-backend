import unittest
from app.services import PropertyService


# -------------------------- Mocks -------------------------------------
class MockConfig:
    DEFAULT_PAGE_NUMBER = 1
    DEFAULT_PAGE_SIZE = 10
    DEFAULT_YEAR_FILTER = 2019


class MockDataAccess:
    """Captura las llamadas y devuelve un resultado fijo."""

    def __init__(self):
        self.last_kwargs = None

    def query_filtered_properties(self, **kwargs):
        self.last_kwargs = kwargs
        return [{
            "city":        "bogota",
            "address":     "Calle Falsa 123",
            "status":      "en_venta",
            "price":       350_000_000,
            "year":        2019,
            "description": "Mock property description"
        }]


class TestPropertyService(unittest.TestCase):

    def setUp(self):
        self.mock_da = MockDataAccess()
        self.service = PropertyService(
            data_access_layer=self.mock_da,
            config_module=MockConfig
        )

    def test_get_properties_default(self):
        """Prueba obtener propiedades sin filtros adicionales (solo los base)."""
        print("Running test_get_properties_default...")
        props = self.service.get_properties()
        print(f"Properties returned: {props}")
        self.assertEqual(len(props), 1)
        self.assertEqual(self.mock_da.last_kwargs["page_number"],
                         MockConfig.DEFAULT_PAGE_NUMBER)
        print("test_get_properties_default passed.\n")

    def test_status_str_convertido_a_lista(self):
        """Prueba que el estado se convierte a lista."""
        print("Running test_status_str_convertido_a_lista...")
        self.service.get_properties(status="pre_venta")
        print(f"Last kwargs: {self.mock_da.last_kwargs}")
        self.assertEqual(self.mock_da.last_kwargs["status_names"],
                         ["pre_venta"])
        print("test_status_str_convertido_a_lista passed.\n")

    def test_year_fuera_de_rango(self):
        """Prueba que el año fuera de rango se convierte al valor por defecto."""
        print("Running test_year_fuera_de_rango...")
        self.service.get_properties(year=2019)
        print(f"Last kwargs: {self.mock_da.last_kwargs}")
        self.assertEqual(self.mock_da.last_kwargs["year"],
                         MockConfig.DEFAULT_YEAR_FILTER)
        print("test_year_fuera_de_rango passed.\n")

    def test_page_number_negativo(self):
        """Prueba que el número de página negativo se convierte al valor por defecto."""
        print("Running test_page_number_negativo...")
        self.service.get_properties(page_number="-5", page_size="3")
        print(f"Last kwargs: {self.mock_da.last_kwargs}")
        self.assertEqual(self.mock_da.last_kwargs["page_number"],
                         MockConfig.DEFAULT_PAGE_NUMBER)
        self.assertEqual(self.mock_da.last_kwargs["page_size"], 3)
        print("test_page_number_negativo passed.\n")

    def test_filtros_combinados(self):
        """Prueba que los filtros combinados funcionan correctamente."""
        print("Running test_filtros_combinados...")
        self.service.get_properties(year=2019, city="bogota",
                                    status=["en_venta", "vendido"],
                                    page_number=2, page_size=15)

        kw = self.mock_da.last_kwargs
        print(f"Last kwargs: {kw}")
        self.assertEqual(kw["year"], 2019)
        self.assertEqual(kw["city"], "bogota")
        self.assertEqual(kw["status_names"], ["en_venta", "vendido"])
        self.assertEqual(kw["page_number"], 2)
        self.assertEqual(kw["page_size"], 15)
        print("test_filtros_combinados passed.\n")


if __name__ == "__main__":
    unittest.main()
