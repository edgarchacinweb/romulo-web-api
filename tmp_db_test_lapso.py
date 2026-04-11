import sys
import os
sys.path.append(os.getcwd())

import utils.config # this probably load env variables
from utils.lapso_rules import LapsoRules
from database.connection import Connection
import pprint

print("Evaluating lapsos config...")
conn = Connection().get_connection()
cursor = conn.cursor()
cursor.execute('SELECT "LapsoId", "Numero", "FechaInicio", "FechaFin" FROM "Lapso" ORDER BY "Numero" ASC;')
rows = cursor.fetchall()
print("ROWS in DB:")
pprint.pprint(rows)
cursor.close()

print("Evaluating...")
res = LapsoRules.is_calification_open()
print("Result:")
pprint.pprint(res)
