import unittest
import mysql.connector
from app import data_access


class TestDataAccess(unittest.TestCase):

    def test_get_db_connection_success(self):
        """
        Prueba que se pueda establecer una conexión a la base de datos.
        Este es un test de INTEGRACIÓN, ya que realmente se conecta a la BD.
        """
        print(f"Test get_db_connection_success:")
        cnx = None
        try:
            cnx = data_access.get_db_connection()
            self.assertIsNotNone(
                cnx, "La conexión no debería ser None si tiene éxito.")
            self.assertTrue(cnx.is_connected(),
                            "La conexión debería estar activa.")
        except mysql.connector.Error as e:
            self.fail(f"La conexión a la BD falló con error: {e}")
        finally:
            if cnx:
                data_access.close_db_connection(cnx)

    def test_common_property(self, properties=[]):
        """
        Prueba común para validar propiedades devueltas por la función de acceso a datos.
        """
        # Verificar que todas las propiedades devueltas tienen un estado permitido
        allowed_statuses = {'pre_venta', 'en_venta', 'vendido'}
        print(f"Propiedades devueltas: {properties}")
        for prop in properties:
            self.assertIn('city', prop)
            self.assertIsNotNone(prop['city'])
            self.assertNotEqual(prop['city'], '')
            self.assertIn('address', prop)
            self.assertIsNotNone(prop['address'])
            self.assertNotEqual(prop['address'], '')
            self.assertIn('status', prop)
            self.assertIn(prop['status'], allowed_statuses)
            self.assertIn('price', prop)
            self.assertIsNotNone(prop['price'])
            self.assertIn('year', prop)
            self.assertIn('description', prop)

    def test_query_filtered_properties_no_filters(self):
        """Prueba obtener propiedades sin filtros adicionales (solo los base)."""
        print(f"Test query_filtered_properties_no_filters:")
        properties = data_access.query_filtered_properties(
            page_number=1, page_size=10)
        self.assertIsNotNone(
            properties, "Debería devolver una lista, no None.")
        self.assertIsInstance(properties, list, "Debería devolver una lista.")
        if properties:
            self.test_common_property(properties)

    def test_query_filtered_properties_with_year_filter(self):
        """Prueba filtrar propiedades por año."""
        print(f"Test query_filtered_properties_with_year_filter:")
        test_year = 2022
        properties = data_access.query_filtered_properties(
            year=test_year, page_number=1, page_size=1)
        self.assertIsNotNone(properties)
        if properties:
            self.test_common_property(properties)

    def test_query_filtered_properties_with_city_filter(self):
        """Prueba filtrar propiedades por ciudad."""
        print(f"Test query_filtered_properties_with_city_filter:")
        test_city = "bogota"  # Asumimos que hay propiedades en Bogotá con estado válido
        properties = data_access.query_filtered_properties(
            city=test_city, page_number=1, page_size=1)
        self.assertIsNotNone(properties)
        if properties:
            self.test_common_property(properties)

    def test_query_filtered_properties_with_status_filter(self):
        """Prueba filtrar propiedades por un estado específico (además de los base)."""
        print(f"Test query_filtered_properties_with_status_filter:")
        test_status = "en_venta"
        properties = data_access.query_filtered_properties(
            status_names=[test_status], page_number=1, page_size=1)
        self.assertIsNotNone(properties)
        if properties:
            self.test_common_property(properties)

    def test_query_filtered_properties_with_multiple_filters(self):
        """Prueba filtrar propiedades con múltiples filtros combinados."""
        print(f"Test query_filtered_properties_with_multiple_filters:")
        # Asume que existe al menos una propiedad en 'bogota' del año 2019 en 'en_venta'
        # (según datos de ejemplo, la propiedad con id 2 debería cumplir si su estado actual es en_venta)
        properties = data_access.query_filtered_properties(
            year=2011, city="bogota", status_names=["en_venta"], page_number=1, page_size=1)
        self.assertIsNotNone(properties)
        if properties:
            self.test_common_property(properties)

    def test_fetch_properties_no_results(self):
        """Prueba un filtro que no debería devolver resultados."""
        print(f"Test fetch_properties_no_results:")
        # Un año muy antiguo o una ciudad ficticia
        properties = data_access.query_filtered_properties(
            year=1000, city="ciudad gotica", page_number=1, page_size=1)
        # La función debe devolver una lista vacía, no None
        self.assertIsNotNone(properties)
        self.assertEqual(len(properties), 0)


if __name__ == '__main__':
    unittest.main()
