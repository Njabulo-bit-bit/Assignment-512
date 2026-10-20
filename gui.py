import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime, timedelta

from classes import campus_data, Lecturer, CampusAdministrator, SystemOperator, create_user, get_policy

#Gui styles
def apply_styles(root):
    style = ttk.Style(root)

    try:
        style.theme_use('clam')

    except tk.TclError:
        pass

    navy = '#17365D'
    blue = '#0091FF'
    light_blue = '#80BEEE'
    panel_grey = '#DCDAD5'
    white = '#FFFFFF'
    dark_text = '#263A47'

    root.configure(background=light_blue)
    style.configure('TFrame', background=light_blue)
    style.configure('TLabel', background=light_blue, foreground=dark_text, font=('Arial', 10))
    style.configure('Title.TLabel', background=navy, foreground=white, font=('Arial', 17, 'bold'), padding=10)
    style.configure('TLabelFrame', background=panel_grey, foreground=navy, borderwidth=1, relief='solid')
    style.configure('TLabelFrame.Label', background=panel_grey, foreground=navy, font=('Arial', 10, 'bold'))
    style.configure('TButton', background=blue, foreground=white, padding=(9, 6), font=('Arial', 10, 'bold'))
    style.map('TButton', background=[('active', navy), ('pressed', navy)], foreground=[('disabled', '#D9E2F3')])
    style.configure('TEntry', fieldbackground=white, foreground=dark_text, padding=5)
    style.configure('TCombobox', fieldbackground=white, foreground=dark_text, padding=4)
    style.configure('TNotebook', background=light_blue, borderwidth=0)
    style.configure('TNotebook.Tab', background='#D5E6F5', foreground=navy, padding=(12, 7), font=('Arial', 10, 'bold'))
    style.map('TNotebook.Tab', background=[('selected', blue)], foreground=[('selected', white)])
    style.configure('Treeview', background=white, fieldbackground=white, foreground=dark_text, rowheight=25)
    style.configure('Treeview.Heading', background=navy, foreground=white, font=('Arial', 10, 'bold'))
    style.map('Treeview', background=[('selected', '#B7D7F0')], foreground=[('selected', dark_text)])

#Accounts setup
class SetupWindow:
    def __init__(self, root, database):
        self.root = root
        self.database = database
        self.entries = {}
        apply_styles(root)
        root.title('Setup')
        root.geometry('650x500')
        root.resizable(False, False)
        frame = ttk.Frame(root, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='First-time Setup', font=('Arial', 16, 'bold')).pack(pady=(0, 15))
        operator = ttk.LabelFrame(frame, text='System Operator', padding=10)
        operator.pack(fill='x', pady=(0, 12))
        ttk.Label(operator, text='Username:').grid(row=0, column=0, padx=5, pady=5)
        self.entries['operator_username'] = ttk.Entry(operator, width=24)
        self.entries['operator_username'].grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(operator, text='Password:').grid(row=0, column=2, padx=5, pady=5)
        self.entries['operator_password'] = ttk.Entry(operator, width=24, show='*')
        self.entries['operator_password'].grid(row=0, column=3, padx=5, pady=5)
        administrators = ttk.LabelFrame(frame, text='Campus Administrators', padding=10)
        administrators.pack(fill='x', pady=(0, 12))
        ttk.Label(administrators, text='Campus').grid(row=0, column=0, padx=5, pady=5)
        ttk.Label(administrators, text='Username').grid(row=0, column=1, padx=5, pady=5)
        ttk.Label(administrators, text='Password').grid(row=0, column=2, padx=5, pady=5)

        for row, campus in enumerate(campus_data, start=1):
            ttk.Label(administrators, text=campus['name']).grid(row=row, column=0, sticky='w', padx=5, pady=3)
            username = ttk.Entry(administrators, width=22)
            username.grid(row=row, column=1, padx=5, pady=3)
            password = ttk.Entry(administrators, width=22, show='*')
            password.grid(row=row, column=2, padx=5, pady=3)
            self.entries['admin_' + campus['id'] + '_username'] = username
            self.entries['admin_' + campus['id'] + '_password'] = password

        ttk.Button(frame, text='Create Accounts', command=self.create_accounts).pack(fill='x')

    def create_accounts(self):
        operator_username = self.entries['operator_username'].get().strip()
        operator_password = self.entries['operator_password'].get()

        if operator_username == '' or operator_password == '':
            messagebox.showerror('Setup error', 'Please complete the operator account.')
            return

        administrators = []
        usernames = [operator_username]

        for campus in campus_data:
            username = self.entries['admin_' + campus['id'] + '_username'].get().strip()
            password = self.entries['admin_' + campus['id'] + '_password'].get()

            if username == '' or password == '':
                messagebox.showerror('Setup error', 'Please complete all administrator accounts.')
                return
            
            usernames.append(username)
            administrators.append({'username': username, 'password': password, 'campus_id': campus['id']})

        if len(usernames) != len(set(usernames)):
            messagebox.showerror('Setup error', 'Each username must be different.')
            return

        success, message = self.database.create_initial_accounts(
            {'username': operator_username, 'password': operator_password},
            administrators)

        if not success:
            messagebox.showerror('Setup error', message)
            return

        messagebox.showinfo('Setup', message)
        self.clear_root()
        LoginWindow(self.root, self.database)

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

#Login
class LoginWindow:
    def __init__(self, root, database):
        self.root = root
        self.database = database
        apply_styles(root)
        root.title('CampusConnect - Login')
        root.geometry('520x350')
        root.resizable(False, False)
        frame = ttk.Frame(root, padding=25)
        frame.pack(expand=True)
        ttk.Label(frame, text='CampusConnect', font=('Arial', 17, 'bold'), style='Title.TLabel').pack(pady=(0, 20))
        form = ttk.LabelFrame(frame, text='Login', padding=15)
        form.pack(fill='x')
        ttk.Label(form, text='Username:').grid(row=0, column=0, sticky='w', pady=7)
        self.username = ttk.Entry(form, width=30)
        self.username.grid(row=0, column=1, padx=10, pady=7)
        ttk.Label(form, text='Password:').grid(row=1, column=0, sticky='w', pady=7)
        self.password = ttk.Entry(form, width=30, show='*')
        self.password.grid(row=1, column=1, padx=10, pady=7)
        ttk.Button(form, text='Log in', command=self.login).grid(row=2, column=0, columnspan=2, sticky='ew', pady=(12, 6))
        ttk.Button(form, text='Register as Lecturer', command=self.register).grid(row=3, column=0, columnspan=2, sticky='ew')
        self.username.focus_set()

    def login(self):
        username = self.username.get().strip()
        password = self.password.get()

        if username == '' or password == '':
            messagebox.showerror('Login error', 'Please enter a username and password.')
            return

        row = self.database.login(username, password)

        if row is None:
            messagebox.showerror('Login error', 'Invalid username or password.')
            return

        user = create_user(row)
        self.clear_root()
        MainWindow(self.root, self.database, user)

    def register(self):
        RegisterWindow(self.root, self.database)

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

#Lecturer registration
class RegisterWindow(tk.Toplevel):
    def __init__(self, parent, database):
        super().__init__(parent)
        self.database = database
        apply_styles(parent)
        self.title('Lecturer Registration')
        self.geometry('410x270')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill='both', expand=True)
        labels = ['Full name:', 'Username:', 'Password:']
        self.entries = []

        for row, label in enumerate(labels):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', pady=7)
            entry = ttk.Entry(frame, width=28, show='*' if row == 2 else '')
            entry.grid(row=row, column=1, padx=10, pady=7)
            self.entries.append(entry)

        ttk.Button(frame, text='Create Account', command=self.create_account).grid(
            row=3, column=0, columnspan=2, sticky='ew', pady=(15, 0))

    def create_account(self):
        full_name = self.entries[0].get().strip()
        username = self.entries[1].get().strip()
        password = self.entries[2].get()

        if full_name == '' or username == '' or password == '':
            messagebox.showerror('Registration error', 'All fields are required.', parent=self)
            return

        success, message = self.database.register_lecturer(full_name, username, password)

        if success:
            messagebox.showinfo('Registration', message, parent=self)
            self.destroy()

        else:
            messagebox.showerror('Registration error', message, parent=self)

#Main window
class MainWindow:
    def __init__(self, root, database, user):
        self.root = root
        self.database = database
        self.user = user
        self.active_campus_id = None
        self.campus_lookup = {}
        apply_styles(root)
        root.title('CampusConnect')
        root.geometry('1200x720')
        root.minsize(1000, 620)
        self.build_header()
        self.build_campus_selector()
        self.build_tabs()

    def build_header(self):
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(fill='x')
        ttk.Label(frame, text='CampusConnect', font=('Arial', 17, 'bold')).pack(side='left')

        if isinstance(self.user, SystemOperator):
            role_text = 'Operator'

        elif isinstance(self.user, CampusAdministrator):
            campus = self.database.get_campus(self.user.campus_id)
            role_text = campus['name'] + ' Admin'

        else:
            role_text = self.user.full_name + ' | Lecturer'

        ttk.Label(frame, text=role_text, font=('Arial', 10, 'bold')).pack(side='right')

    def build_campus_selector(self):
        frame = ttk.LabelFrame(self.root, text='Campus', padding=8)
        frame.pack(fill='x', padx=12, pady=(0, 10))
        ttk.Label(frame, text='Active campus:').pack(side='left')
        self.campus_var = tk.StringVar()
        self.campus_combo = ttk.Combobox(frame, textvariable=self.campus_var, state='readonly', width=20)
        self.campus_combo.pack(side='left', padx=8)
        self.campus_combo.bind('<<ComboboxSelected>>', self.change_campus)
        self.policy_label = ttk.Label(frame, text='')
        self.policy_label.pack(side='left', padx=8)
        ttk.Button(frame, text='Log out', command=self.logout).pack(side='right')

        for campus in self.database.get_campuses():
            self.campus_lookup[campus['name']] = campus['id']

        names = list(self.campus_lookup.keys())

        if isinstance(self.user, CampusAdministrator):
            campus = self.database.get_campus(self.user.campus_id)
            self.campus_combo['values'] = [campus['name']]
            self.campus_var.set(campus['name'])
            self.active_campus_id = self.user.campus_id
            self.campus_combo.config(state='disabled')

        elif isinstance(self.user, SystemOperator):
            self.campus_combo['values'] = ['All Campuses'] + names
            self.campus_var.set('All Campuses')

        else:
            self.campus_combo['values'] = names

            if names:
                self.campus_var.set(names[0])
                self.active_campus_id = self.campus_lookup[names[0]]

        self.update_policy()

    def change_campus(self, event=None):
        name = self.campus_var.get()
        self.active_campus_id = None if name == 'All Campuses' else self.campus_lookup[name]
        self.update_policy()
        self.refresh_all()

    def update_policy(self):
        if self.active_campus_id is None:
            self.policy_label.config(text='Current policy: All Campuses')

        else:
            self.policy_label.config(text='Current policy: ' + get_policy(self.active_campus_id).description())

    def build_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=12, pady=(0, 12))

        if isinstance(self.user, Lecturer):
            self.build_lecturer_tabs()

        elif isinstance(self.user, CampusAdministrator):
            self.build_admin_tabs()

        else:
            self.build_operator_tabs()

    #Lecturer bookings
    def build_lecturer_tabs(self):
        booking_tab = ttk.Frame(self.notebook, padding=10)
        active_tab = ttk.Frame(self.notebook, padding=10)
        history_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(booking_tab, text='Book Resource')
        self.notebook.add(active_tab, text='Active Bookings')
        self.notebook.add(history_tab, text='Booking History')
        self.build_booking_tab(booking_tab)
        self.build_lecturer_booking_list(active_tab, True)
        self.build_lecturer_booking_list(history_tab, False)

    def build_booking_tab(self, tab):
        form = ttk.LabelFrame(tab, text='Booking', padding=10)
        form.pack(fill='x', pady=(0, 10))
        fields = [('Date (YYYY-MM-DD):', 'date', (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')),
                  ('Start time (HH:MM):', 'time', '09:00'),
                  ('Duration (minutes):', 'duration', '60')]
        
        self.booking_entries = {}

        for column, (label, key, default) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=0, column=column * 2, padx=5, pady=5)
            entry = ttk.Entry(form, width=14)
            entry.grid(row=0, column=column * 2 + 1, padx=5, pady=5)
            entry.insert(0, default)
            self.booking_entries[key] = entry

        ttk.Button(
            form,
            text='Book Selected',
            command=self.create_booking).grid(row=1, column=0, columnspan=6, sticky='ew', padx=5, pady=7)
        
        ttk.Label(tab, text='Resources', font=('Arial', 11, 'bold')).pack(anchor='w')

        self.available_tree = self.make_tree(
            tab,
            ('id', 'code', 'name', 'status'),
            ('ID', 'Identifier', 'Resource', 'Availability'),
            (50, 130, 350, 130))

        for entry in self.booking_entries.values():
            entry.bind('<KeyRelease>', lambda event: self.check_availability(False))

        self.check_availability(False)

    def get_booking_values(self):
        try:
            date_text = self.booking_entries['date'].get().strip()
            start_text = self.booking_entries['time'].get().strip()
            duration = int(self.booking_entries['duration'].get())
            start = datetime.strptime(date_text + ' ' + start_text, '%Y-%m-%d %H:%M')
            end = start + timedelta(minutes=duration)
            return date_text, start, end, duration
        
        except ValueError:
            return None, None, None, None

    def check_availability(self, show_error=True):
        self.clear_tree(self.available_tree)

        if self.active_campus_id is None:
            if show_error:
                messagebox.showerror('Availability error', 'Please select a campus.')

            return

        date_text, start, end, duration = self.get_booking_values()

        if start is None:
            if show_error:
                messagebox.showerror('Availability error', 'Please enter valid date, time and duration values.')

            return

        valid, message = get_policy(self.active_campus_id).validate(date_text, start.strftime('%H:%M'), duration)

        if not valid:
            if show_error:
                messagebox.showerror('Availability error', message)

            return

        for resource in self.database.get_resources(self.active_campus_id):
            booked = self.database.has_overlap(
                resource['id'],
                date_text,
                start.strftime('%H:%M'),
                end.strftime('%H:%M'))

            self.available_tree.insert(
                '',
                'end',
                values=(resource['id'],
                        resource['code'],
                        resource['name'],
                        'Unavailable' if booked else 'Available'))

    def create_booking(self):
        selected = self.available_tree.selection()

        if not selected:
            messagebox.showerror('Booking error', 'Please select a resource.')
            return

        values = self.available_tree.item(selected[0], 'values')

        if values[3] != 'Available':
            messagebox.showerror('Booking error', 'Please select an available resource.')
            return

        date_text, start, end, duration = self.get_booking_values()

        if start is None:
            messagebox.showerror('Booking error', 'Please enter valid date, time and duration values.')
            return

        valid, message = get_policy(self.active_campus_id).validate(date_text, start.strftime('%H:%M'), duration)

        if not valid:
            messagebox.showerror('Booking error', message)
            return

        success, message = self.database.add_booking(
            int(values[0]),
            self.user.user_id,
            self.active_campus_id,
            date_text,
            start.strftime('%H:%M'),
            end.strftime('%H:%M'),
            duration)

        if success:
            messagebox.showinfo('Booking', message)
            self.check_availability(False)
            self.refresh_active_bookings()
            self.refresh_history()

        else:
            messagebox.showerror('Booking error', message)

    def build_lecturer_booking_list(self, tab, active):
        buttons = ttk.Frame(tab)
        buttons.pack(fill='x', pady=(0, 8))
        ttk.Button(buttons,
                   text='Refresh',
                   command=self.refresh_active_bookings if active else self.refresh_history).pack(side='left')

        if active:
            ttk.Button(buttons, text='Cancel Selected', command=self.cancel_booking).pack(side='left', padx=8)

        tree = self.make_tree(tab,
                              ('id', 'date', 'start', 'end', 'duration', 'resource', 'campus', 'status'),
                              ('ID', 'Date', 'Start', 'End', 'Minutes', 'Resource', 'Campus', 'Status'),
                              (50, 100, 70, 70, 80, 280, 130, 100))

        if active:
            self.active_tree = tree
            self.refresh_active_bookings()

        else:
            self.history_tree = tree
            self.refresh_history()

    def refresh_active_bookings(self):
        self.clear_tree(self.active_tree)

        for row in self.database.get_active_user_bookings(self.user.user_id):
            self.insert_booking_row(self.active_tree, row)

    def refresh_history(self):
        self.clear_tree(self.history_tree)

        for row in self.database.get_user_bookings(self.user.user_id):
            self.insert_booking_row(self.history_tree, row)

    @staticmethod
    def insert_booking_row(tree, row):
        tree.insert('',
                    'end',
                    values=(row['id'],
                            row['booking_date'],
                            row['start_time'],
                            row['end_time'],
                            row['duration'],
                            row['resource_name'],
                            row['campus_name'],
                            row['status']))

    def cancel_booking(self):
        selected = self.active_tree.selection()

        if not selected:
            messagebox.showerror('Cancellation error', 'Please select a booking.')
            return

        booking_id = int(self.active_tree.item(selected[0], 'values')[0])
        success, message = self.database.cancel_booking(booking_id, self.user.user_id)

        if success:
            messagebox.showinfo('Cancellation', message)
            self.refresh_active_bookings()
            self.refresh_history()
            self.check_availability(False)

        else:
            messagebox.showerror('Cancellation error', message)

    #Campus administrator
    def build_admin_tabs(self):
        resources = ttk.Frame(self.notebook, padding=10)
        bookings = ttk.Frame(self.notebook, padding=10)
        reports = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(resources, text='Resources')
        self.notebook.add(bookings, text='Bookings')
        self.notebook.add(reports, text='Reports')
        self.build_resource_tab(resources)
        self.build_admin_bookings(bookings)
        self.build_admin_report(reports)

    def build_resource_tab(self, tab):
        buttons = ttk.Frame(tab)
        buttons.pack(fill='x', pady=(0, 8))
        ttk.Button(buttons, text='Add', command=self.add_resource).pack(side='left')
        ttk.Button(buttons, text='Update', command=self.update_resource).pack(side='left', padx=8)
        ttk.Button(buttons, text='Remove', command=self.remove_resource).pack(side='left')
        ttk.Button(buttons, text='Refresh', command=self.refresh_resources).pack(side='right')
        self.resource_tree = self.make_tree(tab,
                                            ('id', 'code', 'name', 'status'),
                                            ('ID', 'Identifier', 'Resource', 'Status'),
                                            (50, 140, 350, 110))

        self.refresh_resources()

    def refresh_resources(self):
        self.clear_tree(self.resource_tree)

        for row in self.database.get_resources(self.user.campus_id, True):
            self.resource_tree.insert(
                '',
                'end',
                values=(row['id'], row['code'], row['name'], 'Active' if row['active'] else 'Removed'))

    def add_resource(self):
        ResourceDialog(self.root, self.database, self.user.campus_id, None, self.refresh_resources)

    def update_resource(self):
        selected = self.resource_tree.selection()

        if not selected:
            messagebox.showerror('Resource error', 'Please select a resource.')
            return

        resource_id = int(self.resource_tree.item(selected[0], 'values')[0])

        for resource in self.database.get_resources(self.user.campus_id, True):
            if resource['id'] == resource_id:
                ResourceDialog(self.root, self.database, self.user.campus_id, resource, self.refresh_resources)
                return

    def remove_resource(self):
        selected = self.resource_tree.selection()

        if not selected:
            messagebox.showerror('Resource error', 'Please select a resource.')
            return

        values = self.resource_tree.item(selected[0], 'values')

        if values[3] == 'Removed':
            messagebox.showerror('Resource error', 'The resource has already been removed.')
            return

        success, message = self.database.remove_resource(int(values[0]))

        if success:
            messagebox.showinfo('Resource', message)
            self.refresh_resources()

        else:
            messagebox.showerror('Resource error', message)

    def build_admin_bookings(self, tab):
        ttk.Button(tab, text='Refresh', command=self.refresh_admin_bookings).pack(anchor='w', pady=(0, 8))

        self.admin_booking_tree = self.make_tree(
            tab,
            ('id', 'date', 'start', 'end', 'duration', 'resource', 'lecturer', 'status'),
            ('ID', 'Date', 'Start', 'End', 'Minutes', 'Resource', 'Lecturer', 'Status'),
            (50, 100, 70, 70, 75, 280, 150, 100))
        
        self.refresh_admin_bookings()

    def refresh_admin_bookings(self):
        self.clear_tree(self.admin_booking_tree)

        for row in self.database.get_campus_bookings(self.user.campus_id):
            self.admin_booking_tree.insert(
                '',
                'end',
                values=(row['id'],
                        row['booking_date'],
                        row['start_time'],
                        row['end_time'],
                        row['duration'],
                        row['resource_name'],
                        row['username'],
                        row['status']))

    def build_admin_report(self, tab):
        ttk.Button(tab, text='Refresh', command=self.refresh_campus_report).pack(anchor='w', pady=(0, 8))
        summary = ttk.Frame(tab)
        summary.pack(fill='x', pady=(0, 10))
        
        self.total_label = ttk.Label(summary, text='Total bookings: 0', font=('Arial', 11, 'bold'))
        self.total_label.pack(side='left', padx=(0, 35))
        self.average_label = ttk.Label(summary, text='Average booking duration: 0 minutes', font=('Arial', 11, 'bold'))
        self.average_label.pack(side='left')
        ttk.Label(tab, text='Most frequently used resources', font=('Arial', 11, 'bold')).pack(anchor='w')
        self.report_resource_tree = self.make_tree(
            tab,
            ('code', 'name', 'count'),
            ('Identifier', 'Resource', 'Bookings'),
            (130, 350, 120))

        self.report_resource_tree.pack(fill='x', pady=5)
        ttk.Label(tab, text='Booking trends', font=('Arial', 11, 'bold')).pack(anchor='w', pady=(10, 0))
        self.report_month_tree = self.make_tree(tab, ('month', 'count'), ('Month', 'Bookings'), (180, 120))
        self.report_month_tree.pack(fill='x', pady=5)
        self.refresh_campus_report()

    def refresh_campus_report(self):
        total, average, resources, monthly = self.database.get_campus_report(self.user.campus_id)
        self.total_label.config(text='Total bookings: ' + str(total))
        self.average_label.config(text='Average booking duration: ' + str(round(average, 2)) + ' minutes')
        self.clear_tree(self.report_resource_tree)

        if resources:
            for row in resources:
                self.report_resource_tree.insert('',
                                                 'end',
                                                 values=(row['code'], row['name'], row['booking_count']))

        else:
            self.report_resource_tree.insert('', 'end', values=('', 'No active booking data available', ''))

        self.clear_tree(self.report_month_tree)

        if monthly:
            for row in monthly:
                self.report_month_tree.insert('', 'end', values=(row['month'], row['booking_count']))

        else:
            self.report_month_tree.insert('', 'end', values=('No booking records available', ''))

    #System operator
    def build_operator_tabs(self):
        reports = ttk.Frame(self.notebook, padding=10)
        bookings = ttk.Frame(self.notebook, padding=10)
        resources = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(reports, text='Reports')
        self.notebook.add(bookings, text='Bookings')
        self.notebook.add(resources, text='Resources')
        self.build_operator_report(reports)
        self.build_operator_bookings(bookings)
        self.build_operator_resources(resources)

    def build_operator_report(self, tab):
        ttk.Button(tab, text='Refresh', command=self.refresh_operator_report).pack(anchor='w', pady=(0, 8))

        ttk.Label(tab, text='Campus comparison', font=('Arial', 11, 'bold')).pack(anchor='w')

        self.operator_report_tree = self.make_tree(
            tab,
            ('campus', 'total', 'average', 'policy'),
            ('Campus', 'Total Bookings', 'Average Booking Duration', 'Policy'),
            (180, 130, 150, 350))

        self.operator_report_tree.pack(fill='x', pady=5)

        ttk.Label(tab, text='Booking trends', font=('Arial', 11, 'bold')).pack(anchor='w', pady=(10, 0))

        self.operator_trend_tree = self.make_tree(
            tab,
            ('campus', 'month', 'count'),
            ('Campus', 'Month', 'Bookings'),
            (220, 150, 120))
        
        self.operator_trend_tree.pack(fill='both', expand=True, pady=5)
        self.refresh_operator_report()

    def refresh_operator_report(self):
        rows, trends = self.database.get_cross_campus_report()
        self.clear_tree(self.operator_report_tree)

        for row in rows:
            self.operator_report_tree.insert(
                '',
                'end',
                values=(row['campus_name'],
                        row['total_bookings'],
                        row['average_duration'] or 0,
                        get_policy(row['id']).description()))

        self.clear_tree(self.operator_trend_tree)
        visible_trends = [row for row in trends if row['month'] is not None]

        if visible_trends:
            for row in visible_trends:
                self.operator_trend_tree.insert(
                    '',
                    'end',
                    values=(row['campus_name'], row['month'], row['booking_count']))

        else:
            self.operator_trend_tree.insert('', 'end', values=('', 'No booking records available', ''))

    def build_operator_bookings(self, tab):
        ttk.Button(tab, text='Refresh', command=self.refresh_operator_bookings).pack(anchor='w', pady=(0, 8))

        self.operator_booking_tree = self.make_tree(
            tab,
            ('id', 'campus', 'resource', 'user', 'date', 'start', 'end', 'duration', 'status'),
            ('ID', 'Campus', 'Resource', 'Lecturer', 'Date', 'Start', 'End', 'Minutes', 'Status'),
            (45, 110, 220, 140, 100, 70, 70, 80, 100))
        
        self.refresh_operator_bookings()

    def refresh_operator_bookings(self):
        self.clear_tree(self.operator_booking_tree)

        for row in self.database.get_all_bookings():
            self.operator_booking_tree.insert(
                '',
                'end',
                values=(row['id'],
                        row['campus_name'],
                        row['resource_name'],
                        row['username'],
                        row['booking_date'],
                        row['start_time'],
                        row['end_time'],
                        row['duration'],
                        row['status']))

    def build_operator_resources(self, tab):
        ttk.Button(tab, text='Refresh', command=self.refresh_operator_resources).pack(anchor='w', pady=(0, 8))
        
        self.operator_resource_tree = self.make_tree(
            tab,
            ('code', 'name', 'campus', 'status'),
            ('Identifier', 'Resource', 'Campus', 'Status'),
            (140, 350, 150, 110))

        self.refresh_operator_resources()

    def refresh_operator_resources(self):
        self.clear_tree(self.operator_resource_tree)

        for row in self.database.get_resources(include_inactive=True):
            campus = self.database.get_campus(row['campus_id'])
            self.operator_resource_tree.insert(
                '',
                'end',
                values=(row['code'], row['name'], campus['name'], 'Active' if row['active'] else 'Removed'))

    def refresh_all(self):
        if isinstance(self.user, Lecturer):
            self.check_availability(False)
            self.refresh_active_bookings()
            self.refresh_history()
        elif isinstance(self.user, CampusAdministrator):
            self.refresh_resources()
            self.refresh_admin_bookings()
            self.refresh_campus_report()
        elif isinstance(self.user, SystemOperator):
            self.refresh_operator_report()
            self.refresh_operator_bookings()
            self.refresh_operator_resources()

    @staticmethod
    def clear_tree(tree):
        for item in tree.get_children():
            tree.delete(item)

    @staticmethod
    def make_tree(parent, columns, headings, widths):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(frame, columns=columns, show='headings')

        for column, heading, width in zip(columns, headings, widths):
            tree.heading(column, text=heading)
            tree.column(column, width=width, anchor='w')

        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        return tree

    def logout(self):
        self.clear_root()
        LoginWindow(self.root, self.database)

    def clear_root(self):
        for widget in self.root.winfo_children():
            widget.destroy()

#Resource editor
class ResourceDialog(tk.Toplevel):
    def __init__(self, parent, database, campus_id, resource, refresh_callback):
        super().__init__(parent)
        self.database = database
        self.campus_id = campus_id
        self.resource = resource
        self.refresh_callback = refresh_callback
        self.title('Add Resource' if resource is None else 'Update Resource')
        self.geometry('360x150')
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text='Resource name:').grid(row=0, column=0, sticky='w', pady=8)
        self.name = ttk.Entry(frame, width=25)
        self.name.grid(row=0, column=1, padx=10, pady=8)

        if resource is not None:
            self.name.insert(0, resource['name'])

        ttk.Button(frame, text='Save', command=self.save).grid(row=1, column=0, columnspan=2, sticky='ew', pady=(10, 0))

    def save(self):
        name = self.name.get().strip()

        if name == '':
            messagebox.showerror('Resource error', 'Resource name is required.', parent=self)
            return

        if self.resource is None:
            success, message = self.database.add_resource(name, self.campus_id)

        else:
            success, message = self.database.update_resource(self.resource['id'], name, self.campus_id)

        if success:
            messagebox.showinfo('Resource', message, parent=self)
            self.refresh_callback()
            self.destroy()

        else:
            messagebox.showerror('Resource error', message, parent=self)