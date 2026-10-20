from datetime import datetime, timedelta

campus_data = [{'id': 'C01', 'name': 'Centurion', 'prefix': 'cen'},
               {'id': 'C02', 'name': 'Bryanston', 'prefix': 'bry'},
               {'id': 'C03', 'name': 'Pretoria', 'prefix': 'pta'},
               {'id': 'C04', 'name': 'Capetown', 'prefix': 'cpt'}]

class User:
    def __init__(self, user_id, username, full_name, role, campus_id=None):
        self.user_id = user_id
        self.username = username
        self.full_name = full_name
        self.role = role
        self.campus_id = campus_id

class Lecturer(User):
    def __init__(self, user_id, username, full_name):
        super().__init__(user_id, username, full_name, 'Lecturer')

class CampusAdministrator(User):
    def __init__(self, user_id, username, full_name, campus_id):
        super().__init__(user_id, username, full_name, 'Campus Administrator', campus_id)

class SystemOperator(User):
    def __init__(self, user_id, username, full_name):
        super().__init__(user_id, username, full_name, 'System Operator')

def create_user(row):
    if row['role'] == 'Lecturer':
        return Lecturer(row['id'], row['username'], row['full_name'])

    if row['role'] == 'Campus Administrator':
        return CampusAdministrator(row['id'], row['username'], row['full_name'], row['campus_id'])

    if row['role'] == 'System Operator':
        return SystemOperator(row['id'], row['username'], row['full_name'])

    raise ValueError('Invalid user role.')

class Campus:
    def __init__(self, campus_id, name, prefix):
        self.campus_id = campus_id
        self.name = name
        self.prefix = prefix

def get_campus(campus_id):
    for campus in campus_data:

        if campus['id'] == campus_id:
            return Campus(campus['id'], campus['name'], campus['prefix'])
        
    return None

class Resource:
    def __init__(self, resource_id, code, name, campus_id, active=True):
        self.resource_id = resource_id
        self.code = code
        self.name = name
        self.campus_id = campus_id
        self.active = active

class Booking:
    def __init__(self, booking_id, resource_id, user_id, campus_id, booking_date, start_time, end_time, duration, status):
        self.booking_id = booking_id
        self.resource_id = resource_id
        self.user_id = user_id
        self.campus_id = campus_id
        self.booking_date = booking_date
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.status = status

class BookingPolicy:
    max_duration = 120
    opening_time = '08:00'
    closing_time = '17:00'

    @classmethod
    def validate(cls, booking_date, start_time, duration):
        try:
            start = datetime.strptime(booking_date + ' ' + start_time,'%Y-%m-%d %H:%M')

        except ValueError:
            return (False, 'Use YYYY-MM-DD for the date and HH:MM for the time.')

        if duration <= 0:
            return False, 'Duration must be greater than 0 minutes.'

        if duration > cls.max_duration:
            return (False, 'The maximum booking duration is ' + str(cls.max_duration) + ' minutes.')

        opening = datetime.strptime(cls.opening_time, '%H:%M').time()

        closing = datetime.strptime(cls.closing_time, '%H:%M').time()

        end = start + timedelta(minutes=duration)

        if (start.time() < opening
            or end.time() > closing
            or end.date() != start.date()):

            return (False, 'Bookings must be between ' + cls.opening_time + ' and ' + cls.closing_time + '.')

        if start <= datetime.now():
            return False, 'The booking must be in the future.'

        return True, ''

    @classmethod
    def description(cls):
        return ('Maximum: ' + str(cls.max_duration) + ' minutes | Hours: ' + cls.opening_time + '-' + cls.closing_time)

class CenturionPolicy(BookingPolicy):
    max_duration = 240
    opening_time = '07:00'
    closing_time = '18:00'

class BryanstonPolicy(BookingPolicy):
    max_duration = 120
    opening_time = '08:00'
    closing_time = '16:00'

class PretoriaPolicy(BookingPolicy):
    max_duration = 180
    opening_time = '08:00'
    closing_time = '18:00'

class CapetownPolicy(BookingPolicy):
    max_duration = 180
    opening_time = '09:00'
    closing_time = '19:00'

policies = {'C01': CenturionPolicy,
            'C02': BryanstonPolicy,
            'C03': PretoriaPolicy,
            'C04': CapetownPolicy}

def get_policy(campus_id):
    return policies.get(campus_id, BookingPolicy)