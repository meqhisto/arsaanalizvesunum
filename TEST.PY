import pyodbc
cnxn = None
try:
    conn_str = (
        r'DRIVER={SQL Server};'
        r'SERVER=46.221.49.106;'
        r'DATABASE=arsa_db;'
        r'UID=altan;'
        r'PWD=Yxrkt2bb7q8.;'
    )



    cnxn = pyodbc.connect(conn_str)
    cursor = cnxn.cursor()
    cursor.execute("SELECT @@version;")
    row = cursor.fetchone()
    print(f"Bağlantı Başarılı: {row[0]}")
except pyodbc.Error as ex:
    sqlstate = ex.args[0]
    print(f"Bağlantı Hatası: {sqlstate}")
finally:
    if cnxn:
        cnxn.close()