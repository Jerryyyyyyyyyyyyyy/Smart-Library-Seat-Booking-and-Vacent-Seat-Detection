import mysql.connector
from datetime import datetime
import os
import logging

# Setup logging
logging.basicConfig(filename='cleanup.log', level=logging.INFO, format='%(asctime)s - %(message)s')

try:
    # MySQL connection
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password=os.getenv("DB_PASS", "yourpassword"),  # Load from env or fallback
        database="library"
    )
    cursor = conn.cursor()

    # Find expired bookings
    cursor.execute("SELECT seat_id FROM Bookings WHERE end_time < NOW()")
    expired = cursor.fetchall()

    for (seat_id,) in expired:
        # Check if seat is still occupied
        cursor.execute("SELECT status FROM Seats WHERE seat_id=%s", (seat_id,))
        status = cursor.fetchone()[0]
        if status != "Occupied":
            cursor.execute("UPDATE Seats SET status='Vacant' WHERE seat_id=%s", (seat_id,))
            logging.info(f"Seat {seat_id} released.")
        else:
            logging.info(f"Seat {seat_id} still occupied, not released.")

    # Delete expired bookings
    cursor.execute("DELETE FROM Bookings WHERE end_time < NOW()")
    conn.commit()

except mysql.connector.Error as e:
    logging.error(f"Database error: {e}")
finally:
    cursor.close()
    conn.close()

