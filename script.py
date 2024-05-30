import serial
import mysql.connector

ser = serial.Serial('COM5', 9600)
db_config = {'host':'localhost', 'user':'root', 'password':'', 'database':'hackathon'}
try:
    conn = mysql.connector.connect()
    while True:
        data = ser.readline().decode('utf-8').strip()
        print(data)
except KeyboardInterrupt:
    pass
finally:
    ser.close()
