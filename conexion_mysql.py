# conexion_mysql.py
import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="b1xlkbmpaoezy6hfkope-mysql.services.clever-cloud.com",
        user="uqgwdbj7tpvqfmo3",
        password="eMknQIeBP7XOltyeKT2a",
        database="b1xlkbmpaoezy6hfkope",
        port=3306
    )
