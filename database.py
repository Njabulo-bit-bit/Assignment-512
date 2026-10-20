import sqlite3
from datetime import datetime

from classes import campus_data, get_campus

#Database
class Database:
    def __init__(self, database_name='database.db'):
        self.database_name = database_name

    #Database connection
    def connect(self):
        connection = sqlite3.connect(self.database_name)
        connection.row_factory = sqlite3.Row
        connection.execute('PRAGMA foreign_keys = ON')
        return connection

    def setup_database(self):
        connection = self.connect()
        connection.executescript(
            '''
            CREATE TABLE IF NOT EXISTS campuses (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                prefix TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                campus_id TEXT,
                FOREIGN KEY (campus_id) REFERENCES campuses(id)
            );
            CREATE TABLE IF NOT EXISTS resources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                campus_id TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (campus_id) REFERENCES campuses(id)
            );
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                campus_id TEXT NOT NULL,
                booking_date TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'Active',
                FOREIGN KEY (resource_id) REFERENCES resources(id),
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (campus_id) REFERENCES campuses(id)
            );
            ''')
        
        connection.commit()
        connection.close()
        self.add_campuses()

    #Campus initialising
    def add_campuses(self):
        connection = self.connect()

        for campus in campus_data:
            connection.execute(
                '''
                INSERT INTO campuses (id, name, prefix)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    prefix = excluded.prefix
                ''',
                (campus['id'], campus['name'], campus['prefix']))

        connection.commit()
        connection.close()

    #Accounts
    def user_count(self):
        connection = self.connect()
        count = connection.execute('SELECT COUNT(*) AS count FROM users').fetchone()['count']
        connection.close()
        return count

    def create_initial_accounts(self, operator, administrators):
        connection = self.connect()

        try:
            usernames = [operator['username']]
            usernames.extend(administrator['username'] for administrator in administrators)

            if len(usernames) != len(set(usernames)):
                return False, 'Each account must have a different username.'

            for username in usernames:
                row = connection.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()

                if row is not None:
                    return (False, 'The username ' + username + ' already exists.')
                
            connection.execute(
                '''
                INSERT INTO users
                (username, password, full_name, role, campus_id)
                VALUES (?, ?, ?, 'System Operator', NULL)
                ''',
                (operator['username'], operator['password'], 'System Operator'))

            for administrator in administrators:
                campus = get_campus(administrator['campus_id'])
                connection.execute(
                    '''
                    INSERT INTO users
                    (username, password, full_name, role, campus_id)
                    VALUES (?, ?, ?, 'Campus Administrator', ?)
                    ''',
                    (administrator['username'],
                     administrator['password'],
                     campus.name + ' Administrator',
                     administrator['campus_id']))
                
            connection.commit()
            return True, 'Accounts created successfully.'
        
        except sqlite3.Error:
            connection.rollback()
            return False, 'The accounts could not be created.'
        
        finally:
            connection.close()

    def login(self, username, password):
        connection = self.connect()
        row = connection.execute(
            '''
            SELECT *
            FROM users
            WHERE username = ?
            AND password = ?
            ''',
            (username, password)).fetchone()
        
        connection.close()

        if row is None:
            return None

        return dict(row)

    def register_lecturer(self, full_name, username, password):
        connection = self.connect()

        try:
            connection.execute(
                '''
                INSERT INTO users
                (username, password, full_name, role, campus_id)
                VALUES (?, ?, ?, 'Lecturer', NULL)
                ''',
                (username, password, full_name))
            
            connection.commit()
            return True, 'Lecturer account created successfully.'
        
        except sqlite3.IntegrityError:
            return False, 'That username already exists.'
        
        finally:
            connection.close()

    #Campus and resources
    def get_campuses(self):
        connection = self.connect()
        rows = connection.execute('SELECT * FROM campuses ORDER BY name').fetchall()
        connection.close()
        return [dict(row) for row in rows]

    def get_campus(self, campus_id):
        connection = self.connect()
        row = connection.execute('SELECT * FROM campuses WHERE id = ?', (campus_id,)).fetchone()
        connection.close()
        return dict(row) if row else None

    def get_resources(self, campus_id=None, include_inactive=False):
        connection = self.connect()
        query = 'SELECT * FROM resources'
        values = []

        if campus_id is not None:
            query += ' WHERE campus_id = ?'
            values.append(campus_id)

            if not include_inactive:
                query += ' AND active = 1'
                
        elif not include_inactive:
            query += ' WHERE active = 1'

        query += ' ORDER BY code'
        rows = connection.execute(query, values).fetchall()
        connection.close()
        return [dict(row) for row in rows]

    #Resource management
    def duplicate_resource(self, name, campus_id, resource_id=None):
        connection = self.connect()
        query = '''
            SELECT id
            FROM resources
            WHERE LOWER(name) = LOWER(?)
            AND campus_id = ?
            AND active = 1
        '''
        values = [name, campus_id]

        if resource_id is not None:
            query += ' AND id != ?'
            values.append(resource_id)

        row = connection.execute(query, values).fetchone()
        connection.close()
        return row is not None

    def generate_resource_code(self, campus_id):
        connection = self.connect()
        campus = connection.execute('SELECT prefix FROM campuses WHERE id = ?', (campus_id,)).fetchone()

        if campus is None:
            connection.close()
            return None

        prefix = campus['prefix'] + '-'
        rows = connection.execute('SELECT code FROM resources WHERE code LIKE ?', (prefix + '%',)).fetchall()
        connection.close()
        highest = 0

        for row in rows:
            number = row['code'].replace(prefix, '')

            if number.isdigit():
                highest = max(highest, int(number))

        return prefix + str(highest + 1).zfill(3)

    def add_resource(self, name, campus_id):
        name = name.strip()

        if name == '':
            return False, 'Resource name is required.'

        if self.duplicate_resource(name, campus_id):
            return (False, 'A resource with that name already exists at this campus.')

        code = self.generate_resource_code(campus_id)
        connection = self.connect()

        try:
            connection.execute(
                '''
                INSERT INTO resources
                (code, name, campus_id, active)
                VALUES (?, ?, ?, 1)
                ''',
                (code, name, campus_id))
            
            connection.commit()
            return True, 'Resource added successfully.'
        
        except sqlite3.IntegrityError:
            return False, 'The resource identifier already exists.'

        finally:
            connection.close()

    def update_resource(self, resource_id, name, campus_id):
        name = name.strip()

        if name == '':
            return False, 'Resource name is required.'

        if self.duplicate_resource(name, campus_id, resource_id):
            return (False, 'A resource with that name already exists at this campus.')

        connection = self.connect()
        connection.execute(
            '''
            UPDATE resources
            SET name = ?
            WHERE id = ?
            AND campus_id = ?
            ''',
            (name, resource_id, campus_id))

        connection.commit()
        connection.close()
        return True, 'Resource updated successfully.'

    def remove_resource(self, resource_id):
        connection = self.connect()
        future_booking = connection.execute(
            '''
            SELECT id
            FROM bookings
            WHERE resource_id = ?
            AND status = 'Active'
            AND (
                booking_date || ' ' || start_time
            ) >= datetime('now', 'localtime')
            LIMIT 1
            ''',
            (resource_id,)).fetchone()

        if future_booking is not None:
            connection.close()
            return False, 'The resource has a future active booking.'

        connection.execute(
            '''
            UPDATE resources
            SET active = 0
            WHERE id = ?
            ''',
            (resource_id,))
            
        connection.commit()
        connection.close()
        return True, 'Resource removed successfully.'

    #Add booking and availability
    def has_overlap(self, resource_id, booking_date, start_time, end_time):
        connection = self.connect()
        row = connection.execute(
            '''
            SELECT id
            FROM bookings
            WHERE resource_id = ?
            AND booking_date = ?
            AND status = 'Active'
            AND start_time < ?
            AND end_time > ?
            LIMIT 1
            ''',
            (resource_id,
             booking_date,
             end_time,
             start_time)).fetchone()
                
        connection.close()
        return row is not None

    def add_booking(self, resource_id, user_id, campus_id, booking_date, start_time, end_time, duration):
        connection = self.connect()
        resource = connection.execute(
            '''
            SELECT id
            FROM resources
            WHERE id = ?
            AND campus_id = ?
            AND active = 1
            ''',
            (resource_id, campus_id)).fetchone()

        if resource is None:
            connection.close()
            return False, 'The selected resource is not available.'

        overlap = connection.execute(
            '''
            SELECT id
            FROM bookings
            WHERE resource_id = ?
            AND booking_date = ?
            AND status = 'Active'
            AND start_time < ?
            AND end_time > ?
            LIMIT 1
            ''',
            (resource_id, booking_date, end_time, start_time)).fetchone()

        if overlap is not None:
            connection.close()
            return False, 'The resource already has an overlapping booking.'

        connection.execute(
            '''
            INSERT INTO bookings
            (
                resource_id,
                user_id,
                campus_id,
                booking_date,
                start_time,
                end_time,
                duration,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Active')
            ''',
            (resource_id,
             user_id,
             campus_id,
             booking_date,
             start_time,
             end_time,duration))

        connection.commit()
        connection.close()
        return True, 'Booking created successfully.'

    #Booking history
    def get_user_bookings(self, user_id):
        connection = self.connect()
        rows = connection.execute(
            '''
            SELECT
                b.id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.duration,
                b.status,
                r.code AS resource_code,
                r.name AS resource_name,
                c.name AS campus_name
            FROM bookings b
            JOIN resources r ON b.resource_id = r.id
            JOIN campuses c ON b.campus_id = c.id
            WHERE b.user_id = ?
            ORDER BY b.booking_date DESC, b.start_time DESC
            ''',
            (user_id,)).fetchall()

        connection.close()
        return [dict(row) for row in rows]

    def get_active_user_bookings(self, user_id):
        connection = self.connect()
        rows = connection.execute(
            '''
            SELECT
                b.id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.duration,
                b.status,
                r.code AS resource_code,
                r.name AS resource_name,
                c.name AS campus_name
            FROM bookings b
            JOIN resources r ON b.resource_id = r.id
            JOIN campuses c ON b.campus_id = c.id
            WHERE b.user_id = ?
            AND b.status = 'Active'
            AND (
                b.booking_date || ' ' || b.start_time
            ) >= datetime('now', 'localtime')
            ORDER BY b.booking_date, b.start_time
            ''',
            (user_id,)).fetchall()

        connection.close()
        return [dict(row) for row in rows]

    def cancel_booking(self, booking_id, user_id):
        connection = self.connect()
        row = connection.execute(
            '''
            SELECT *
            FROM bookings
            WHERE id = ?
            AND user_id = ?
            AND status = 'Active'
            ''',
            (booking_id, user_id)).fetchone()

        if row is None:
            connection.close()
            return False, 'Booking not found.'

        booking_start = datetime.strptime(row['booking_date'] + ' ' + row['start_time'], '%Y-%m-%d %H:%M')

        if booking_start <= datetime.now():
            connection.close()
            return False, 'Only future bookings can be cancelled.'

        connection.execute(
            '''
            UPDATE bookings
            SET status = 'Cancelled'
            WHERE id = ?
            ''',
            (booking_id,))

        connection.commit()
        connection.close()
        return True, 'Booking cancelled successfully.'

    def get_campus_bookings(self, campus_id):
        connection = self.connect()
        rows = connection.execute(
            '''
            SELECT
                b.id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.duration,
                b.status,
                r.code AS resource_code,
                r.name AS resource_name,
                u.username
            FROM bookings b
            JOIN resources r ON b.resource_id = r.id
            JOIN users u ON b.user_id = u.id
            WHERE b.campus_id = ?
            ORDER BY b.booking_date DESC, b.start_time DESC
            ''',
            (campus_id,)).fetchall()

        connection.close()
        return [dict(row) for row in rows]

    def get_all_bookings(self):
        connection = self.connect()
        rows = connection.execute(
            '''
            SELECT
                b.id,
                b.booking_date,
                b.start_time,
                b.end_time,
                b.duration,
                b.status,
                r.code AS resource_code,
                r.name AS resource_name,
                c.name AS campus_name,
                u.username
            FROM bookings b
            JOIN resources r ON b.resource_id = r.id
            JOIN campuses c ON b.campus_id = c.id
            JOIN users u ON b.user_id = u.id
            ORDER BY b.booking_date DESC, b.start_time DESC
            ''').fetchall()

        connection.close()
        return [dict(row) for row in rows]

    #Usage and campus reports
    def get_campus_report(self, campus_id):
        connection = self.connect()

        #Recorded bookings count
        total = connection.execute(
            '''
            SELECT COUNT(*) AS total
            FROM bookings
            WHERE campus_id = ?
            ''',
            (campus_id,)).fetchone()['total']

        average = connection.execute(
            '''
            SELECT AVG(duration) AS average
            FROM bookings
            WHERE campus_id = ?
            ''',
            (campus_id,)).fetchone()['average'] or 0

        most_used = connection.execute(
            '''
            SELECT
                r.code,
                r.name,
                COUNT(b.id) AS booking_count
            FROM bookings b
            JOIN resources r ON b.resource_id = r.id
            WHERE b.campus_id = ?
            GROUP BY r.id
            ORDER BY booking_count DESC, r.name
            LIMIT 5
            ''',
            (campus_id,)).fetchall()

        monthly = connection.execute(
            '''
            SELECT
                substr(booking_date, 1, 7) AS month,
                COUNT(*) AS booking_count
            FROM bookings
            WHERE campus_id = ?
            GROUP BY month
            ORDER BY month DESC
            ''',
            (campus_id,)).fetchall()

        connection.close()
        return (total, average, [dict(row) for row in most_used], [dict(row) for row in monthly])

    def get_cross_campus_report(self):
        connection = self.connect()
        campuses = connection.execute(
            '''
            SELECT
                c.id,
                c.name AS campus_name,
                COUNT(b.id) AS total_bookings,
                ROUND(AVG(b.duration), 2) AS average_duration
            FROM campuses c
            LEFT JOIN bookings b ON c.id = b.campus_id
            GROUP BY c.id
            ORDER BY c.name
            ''').fetchall()

        trends = connection.execute(
            '''
            SELECT
                c.name AS campus_name,
                substr(b.booking_date, 1, 7) AS month,
                COUNT(b.id) AS booking_count
            FROM campuses c
            LEFT JOIN bookings b
                ON c.id = b.campus_id
            GROUP BY c.id, month
            ORDER BY month DESC, c.name
            ''').fetchall()

        connection.close()
        return ([dict(row) for row in campuses], [dict(row) for row in trends])