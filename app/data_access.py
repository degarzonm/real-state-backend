import mysql.connector
from mysql.connector import errorcode
from . import config as _default_config_module


def get_db_connection(connector=mysql.connector.connect, cfg=_default_config_module):
    """
    Establece y devuelve una conexión a la base de datos MySQL.
    Args:
        connector: Función de conexión de mysql.connector.
        cfg: Módulo de configuración con credenciales de la base de datos.
    Returns:
        cnx: Conexión a la base de datos.
    """
    try:
        cnx = connector(
            user=cfg.DB_USER,
            password=cfg.DB_PASSWORD,
            host=cfg.DB_HOST,
            port=cfg.DB_PORT,
            database=cfg.DB_NAME)
        print("Conexión a la base de datos exitosa.")
        return cnx
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print(
                f"Error de acceso: Usuario o contraseña incorrectos para '{cfg.DB_USER}'")
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print(f"Error: La base de datos '{cfg.DB_NAME}' no existe.")
        else:
            print(f"Error al conectar a la base de datos: {err}")
        return None


def close_db_connection(cnx, cursor=None):
    """Cierra el cursor y la conexión a la base de datos si están abiertos.
    Args:
        cnx: Conexión a la base de datos.
        cursor: Cursor de la base de datos.
    Returns:
        None
    """
    if cursor:
        try:
            cursor.close()
        except mysql.connector.Error as err:
            print(f"Error al cerrar el cursor: {err}")
    if cnx and cnx.is_connected():
        try:
            cnx.close()
            print("Conexión a la base de datos cerrada.")
        except mysql.connector.Error as err:
            print(f"Error al cerrar la conexión: {err}")


def query_filtered_properties(year=None, city=None, status_names=None,
                              page_number=None, page_size=None,
                              connector=mysql.connector.connect,
                              cfg=_default_config_module):
    """
    Obtiene propiedades de la base de datos filtradas por año, ciudad o nombres de estado.
    El estado actual de la propiedad se determina como el último en status_history.
    Dadas algunas inconsistencias en registros en la tabla properties, consideramos lo siguiente:
    omitimos propiedades sin: addres, city o price.
    Los estados base ('pre_venta', 'en_venta', 'vendido') siempre se aplican para los usuarios externos.
    El filtro 'status_names' refina sobre estos estados base.

    Args:
        year (int, optional): Año de construcción para filtrar.
        city (str, optional): Ciudad para filtrar.
        status_names (list, optional): Lista de nombres de estado para filtrar.
        page_number (int, optional): Número de página solicitada, 1 inicial.
        page_size (int, optional): Tamaño de la página, máximo 200.

    Returns:
        list: Lista de diccionarios, cada uno representando una propiedad,
              o None si ocurre un error.
    """
    cnx = get_db_connection(connector=connector, cfg=cfg)
    if not cnx:
        return None

    cursor = None
    try:
        # Para obtener resultados como dicts
        cursor = cnx.cursor(dictionary=True)

        # Construcción de la query base
        base_query = """
            WITH LatestStatus AS (
                SELECT
                    sh.property_id,
                    sh.status_id,
                    sh.update_date,
                    ROW_NUMBER() OVER (PARTITION BY sh.property_id ORDER BY sh.update_date DESC) as rn
                FROM status_history sh
            )
            SELECT
                p.city,
                p.address,
                s.name AS status,
                p.price,
                p.year,
                p.description
            FROM
                property p
            JOIN
                LatestStatus ls ON p.id = ls.property_id
            JOIN
                status s ON ls.status_id = s.id
            WHERE
                ls.rn = 1
                AND s.name IN ('pre_venta', 'en_venta', 'vendido')
                AND p.address IS NOT NULL 
                AND p.address <> ''
                AND p.city IS NOT NULL AND p.city <> ''
                AND p.price IS NOT NULL AND p.price > 0
        """

        # Lista para almacenar las condiciones de los filtros adicionales
        conditions = []
        # Lista para almacenar los parámetros de la query para evitar SQL injection , algunos frameworks lo hacen automáticamente
        params = []

        if year:
            conditions.append("p.year = %s")
            params.append(year)
        if city:
            # Usamos LIKE para búsquedas insensibles a mayúsculas/minúsculas, deberíamos
            # tener en bd y el sistema en general un lenguaje estándar para las ciudades.
            conditions.append("p.city LIKE LOWER(%s)")
            params.append(city)
        if status_names:  # Luego de haber filtrado los estados visibles, refinamos basado en el filtro del usuario
            if isinstance(status_names, str):  # Si solo viene un estado
                status_names = [status_names]
            if status_names:  # Asegurarse que la lista no está vacía
                # Crear placeholders (%s) para cada estado en la lista (%s, %s, %s, ...)
                status_list = ', '.join(['%s'] * len(status_names))
                conditions.append(f"s.name IN ({status_list})")
                params.extend(status_names)

        # Si hay condiciones adicionales, las añadimos a la query base
        if conditions:
            query = f"{base_query} AND {' AND '.join(conditions)}"
        else:
            query = base_query

        # Para consistencia en los resultados y paginacion, TODO: ordenamiento por precio u otro
        query += " ORDER BY p.id"
        # Manejo de paginación
        offset = (page_number - 1) * page_size
        query += " LIMIT %s OFFSET %s;"
        params.append(page_size)
        params.append(offset)

        cursor.execute(query, tuple(params))
        properties = cursor.fetchall()
        return properties

    except mysql.connector.Error as err:
        print(f"Error al obtener propiedades: {err}")
        return None
    finally:
        close_db_connection(cnx, cursor)
