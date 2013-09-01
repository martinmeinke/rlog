import sqlite3
import random
import time

db_connection = sqlite3.connect("sensor.db")
db_cursor  = db_connection.cursor()

while True:
	for dId in range(1,4):
		q_string = (
		"INSERT INTO charts_solarentrytick "
		"VALUES (NULL, datetime('now', 'localtime'),"+str(dId)+",1,1,1,1,1,"+str(random.randint(80,120)*dId)+",10,500)")
		db_cursor.execute(q_string)

	db_connection.commit()
	time.sleep(10)
