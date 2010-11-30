#!/usr/bin/python

from time import sleep

# change for appropriate database 
import MySQLdb as db

import serial

# Database config
DB = {
    'name' : 'jarvis',
    'user' : 'jarvis',
    'password' : '[sddeptf',
    'host' : 'localhost',
    'port' : '3306',

    'log_table' : 'door_control_rfidlogentry',
    'door_state_table' : 'door_control_doorstate',
    'user_profile_table' : 'door_control_userprofile',
    'queue_table' : 'door_control_queueentry',
}

conn = db.connect(host=DB['host'], user=DB['user'],
                  passwd=DB['password'], db=DB['name'])

# Low level config
DEFAULT_INTERFACE = '/dev/ttyUSB0'
BAUD = 57600
TIMEOUT = None
# should be 8 characters tag id OR 7 characters packet type and 1 character data
PACKET_SIZE = 8

TOGGLE = '0'
LOCK   = '1'
UNLOCK = '2'
INVALID = '3'
REQ_STATE = '4'
SET_LOCKED '5'
SET_UNLOCKED '6'

ACK_ID = 'ACK'
MAN_OPEN_ID = 'MAN'

FULL_PACKET_TIMEOUT = 12
PING_TIMEOUT = 700

# time delay for server loop in seconds (can be a float)
TIME_DELAY = 0.01

old_state = None

def main():
    # empty queue 
    while db_queue_items() > 0:
        db_dequeue_command()

    controller = setup_serial_connection(DEFAULT_INTERFACE)

    while True:
        # Timeout for the serial data. If it gets only partial data, it will 
        # eventually clear the buffer, instead of leaving it there to
        # mess up future reads
        if controller.inWaiting() == 0:
            full_packet_timeout_count = 0

        # Only some data read
        if controller.inWaiting() > 0 and controller.inWaiting() < PACKET_SIZE:
            full_packet_timeout_count += 1

        # Partially received packet timed out
        if full_packet_timeout_count == FULL_PACKET_TIMEOUT:
            full_packet_timeout_count = 0
            controller.read(controller.inWaiting())

        handle_incoming_packets(controller)

        process_db_queue(controller)

        # Don't hog all the processor time
        sleep(TIME_DELAY)

def process_db_queue(controller)
    while db_queue_items() > 0:
        # command is a string
        command = db_dequeue_command()
        controller.write(str(command))

def setup_serial_connection(interface)
    controller = serial.Serial(interface, BAUD, timeout = TIMEOUT);
    full_packet_timeout_count = 0

    while controller.inWaiting() == 0:
        # request door state
        controller.write(REQ_STATE)
        sleep(TIME_DELAY)

    controller.read(controller.inWaiting() - PACKET_SIZE)

def handle_incoming_packets(controller)
    # Handle all waiting packets
    while controller.inWaiting() >= PACKET_SIZE:
        full_packet_timeout_count = 0

        # Door state is true if closed
        data = controller.read(PACKET_SIZE)
        pkt_type = data[:3]

        if pkt_type == ACK_ID:
            db_update_door_state(data[-1:] == '1')
            if data[3:6] == MAN_OPEN_ID:
                db_write_log('MANUAL TOGGLE')
        else:
            db_write_log(data)
            auth = db_has_access(data)
            if auth:
                controller.write(TOGGLE)
            else:
                controller.write(INVALID)

# Decorator for try/except-ing SQL
def sql(f):
    def wrapped_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except db.Error, e:
            print "ERROR %d: %s" % (e.args[0], e.args[1])
            import sys
            sys.exit(1)
    return wrapped_f

@sql
def db_update_door_state(is_locked):
    global old_state
    if is_locked == old_state:
        return
    else:
        old_state = is_locked

    if is_locked:
        bool_str = 'TRUE'
    else:
        bool_str = 'FALSE'

    cursor = conn.cursor()
    cursor.execute('INSERT INTO %s(creation_time, is_locked) '
                   'VALUES(CURRENT_TIMESTAMP(), %s)'
                   % (DB['door_state_table'], bool_str))
    cursor.close()

@sql
def db_write_log(tag):
    cursor = conn.cursor()
    cursor.execute('INSERT INTO %s(creation_time, tag) '
                   'VALUES(CURRENT_TIMESTAMP(), \'%s\')'
                   % (DB['log_table'], tag))
    cursor.close()

@sql
def db_has_access(tag):
    cursor = conn.cursor()
    rows = cursor.execute('SELECT user_id FROM %s '
                          'WHERE rfid_tag=\'%s\' AND has_access=TRUE'
                          % (DB['user_profile_table'], tag))
    cursor.close()

    return rows > 0

@sql
def db_queue_items():
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM %s;' % DB['queue_table'])
    result = cursor.fetchone()
    cursor.close()

    return result[0]

@sql 
def db_dequeue_command():
    cursor = conn.cursor()
    cursor.execute('SELECT id, command FROM %s ORDER BY creation_time ASC LIMIT 1'
                   % DB['queue_table'])
    result = cursor.fetchone()
    cursor.close()

    cursor = conn.cursor()
    cursor.execute('DELETE FROM %s WHERE id=%d'
                  % (DB['queue_table'], result[0]))
    cursor.close()

    return result[1]

if __name__ == '__main__':
    main()
