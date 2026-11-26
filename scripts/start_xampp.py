"""Run Flask with the local XAMPP MySQL/MariaDB server."""
import os
os.environ.setdefault('DB_ENGINE','mysql')
os.environ.setdefault('DB_HOST','127.0.0.1')
os.environ.setdefault('DB_PORT','3306')
os.environ.setdefault('DB_NAME','jobboard')
os.environ.setdefault('DB_USER','root')
os.environ.setdefault('DB_PASSWORD','')
from scripts.start_local import app
if __name__=='__main__':app.run(host='127.0.0.1',port=8000,debug=False)
