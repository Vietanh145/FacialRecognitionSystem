import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, date, timedelta
import psycopg2
from db_config import DB_CONFIG
from tkinter import filedialog
import pandas as pd
from tkcalendar import DateEntry


class LoginScreen:
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success

        window_width = 400
        window_height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")

        self.root.title("Admin Login")

        # Main frame
        self.frame = ttk.Frame(root, padding="20")
        self.frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(self.frame, text="Admin Login", font=('Arial', 20, 'bold'))
        title.pack(pady=20)

        # Username
        username_frame = ttk.Frame(self.frame)
        username_frame.pack(fill='x', pady=5)
        ttk.Label(username_frame, text="Username:").pack(side='left')
        self.username_entry = ttk.Entry(username_frame)
        self.username_entry.pack(side='right', expand=True, fill='x')

        # Password
        password_frame = ttk.Frame(self.frame)
        password_frame.pack(fill='x', pady=5)
        ttk.Label(password_frame, text="Password:").pack(side='left')
        self.password_entry = ttk.Entry(password_frame, show="*")
        self.password_entry.pack(side='right', expand=True, fill='x')

        # Login button
        ttk.Button(self.frame, text="Login", command=self.login).pack(pady=20)

        # Error message
        self.error_label = ttk.Label(self.frame, text="", foreground="red")
        self.error_label.pack()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Check user credentials and role
            cursor.execute("""
                    SELECT id, role FROM users 
                    WHERE user_name = %s AND password = %s
                """, (username, password))

            result = cursor.fetchone()

            if result and result[1].lower() == 'hr':
                # Login successful and user has HR role
                self.frame.destroy()
                self.on_login_success()
            else:
                self.error_label.config(text="Invalid credentials or insufficient permissions")

        except Exception as e:
            self.error_label.config(text="Login error occurred")
            print(f"Login error: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()


class DetailedStatisticsWindow:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Detailed Statistics - Last 30 Days")
        self.window.geometry("1200x800")

        # Center the window
        self.window.transient(parent)
        self.window.grab_set()

        # Variables
        self.selected_user_id = tk.StringVar()
        self.users_data = []

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.window, padding="20")
        main_frame.pack(fill='both', expand=True)

        # Title
        title = ttk.Label(main_frame, text="Detailed Statistics - Last 30 Days",
                          font=('Arial', 18, 'bold'))
        title.pack(pady=(0, 20))

        # User selection frame
        user_frame = ttk.LabelFrame(main_frame, text="Select Employee", padding="10")
        user_frame.pack(fill='x', pady=(0, 20))

        ttk.Label(user_frame, text="Employee:").pack(side='left', padx=(0, 10))
        self.user_combobox = ttk.Combobox(user_frame, textvariable=self.selected_user_id,
                                          state="readonly", width=40)
        self.user_combobox.pack(side='left', padx=(0, 10))
        self.user_combobox.bind("<<ComboboxSelected>>", self.on_user_selected)

        ttk.Button(user_frame, text="View Statistics", command=self.load_statistics).pack(side='left', padx=10)

        # Statistics display frame
        stats_frame = ttk.LabelFrame(main_frame, text="Detailed Statistics", padding="10")
        stats_frame.pack(fill='both', expand=True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(stats_frame)
        self.notebook.pack(fill='both', expand=True)

        # Summary tab
        self.summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.summary_frame, text="Summary")

        # Detailed tab
        self.detailed_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.detailed_frame, text="Daily Details")

        # Leave requests tab
        self.leave_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.leave_frame, text="Leave Requests")

    def load_users(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            cursor.execute("""
                    SELECT id, user_name, email, role FROM users 
                    ORDER BY user_name
                """)

            users = cursor.fetchall()
            self.users_data = users

            # Populate combobox with all users (show role)
            user_options = [f"{user[1]} ({user[2]}) - {user[3]}" for user in users]
            self.user_combobox['values'] = user_options

        except Exception as e:
            messagebox.showerror("Error", f"Cannot load user list: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def on_user_selected(self, event=None):
        if self.selected_user_id.get():
            self.load_statistics()

    def load_statistics(self):
        if not self.selected_user_id.get():
            messagebox.showwarning("Warning", "Please select a user")
            return

        # Get user ID from selection
        selected_text = self.selected_user_id.get()
        user_id = None
        for user in self.users_data:
            if f"{user[1]} ({user[2]}) - {user[3]}" == selected_text:
                user_id = user[0]
                break

        if not user_id:
            return

        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Calculate date range (30 days from today)
            end_date = date.today()
            start_date = end_date - timedelta(days=30)

            # Get attendance data
            cursor.execute("""
                    SELECT date, time_in, time_out, status 
                    FROM logs 
                    WHERE user_id = %s AND date >= %s AND date <= %s
                    ORDER BY date
                """, (user_id, start_date, end_date))

            attendance_data = cursor.fetchall()

            # Get leave requests
            cursor.execute("""
                    SELECT start_date, end_date, reason, status 
                    FROM leave_requests 
                    WHERE user_id = %s AND start_date >= %s AND end_date <= %s
                    ORDER BY start_date
                """, (user_id, start_date, end_date))

            leave_data = cursor.fetchall()

            # Calculate statistics
            stats = self.calculate_statistics(attendance_data, leave_data, start_date, end_date)

            # Display statistics
            self.display_summary(stats)
            self.display_detailed(attendance_data, leave_data, start_date, end_date)
            self.display_leave_requests(leave_data)

        except Exception as e:
            messagebox.showerror("Error", f"Cannot load statistics: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def calculate_statistics(self, attendance_data, leave_data, start_date, end_date):
        stats = {
            'total_days': 30,
            'on_time': 0,
            'late': 0,
            'absent_with_leave': 0,
            'absent_without_leave': 0,
            'leave_reasons': []
        }

        # Giờ chuẩn check-in (08:00)
        standard_time = datetime.strptime('08:00:00', '%H:%M:%S').time()

        # Create a set of dates with leave requests
        leave_dates = set()
        for leave in leave_data:
            current_date = leave[0]
            while current_date <= leave[1]:
                leave_dates.add(current_date)
                current_date += timedelta(days=1)

        # Lấy lần check-in đầu tiên mỗi ngày
        first_checkins = {}
        for record in attendance_data:
            record_date = record[0]
            time_in = record[1]
            if record_date not in first_checkins or (time_in and time_in < first_checkins[record_date]):
                first_checkins[record_date] = time_in

        # Đếm on_time/late dựa trên lần check-in đầu tiên
        for record_date, time_in in first_checkins.items():
            if time_in:
                if time_in.time() <= standard_time:
                    stats['on_time'] += 1
                else:
                    stats['late'] += 1

        # Calculate absences
        current_date = start_date
        while current_date <= end_date:
            if current_date not in first_checkins:
                if current_date in leave_dates:
                    stats['absent_with_leave'] += 1
                    # Find reason for this date
                    for leave in leave_data:
                        if leave[0] <= current_date <= leave[1]:
                            stats['leave_reasons'].append({
                                'date': current_date,
                                'reason': leave[2],
                                'status': leave[3]
                            })
                            break
                else:
                    stats['absent_without_leave'] += 1
            current_date += timedelta(days=1)

        return stats

    def display_summary(self, stats):
        # Clear previous content
        for widget in self.summary_frame.winfo_children():
            widget.destroy()

        # Create summary display
        summary_text = f"""
Detailed Statistics Summary - Last 30 days

Total Days: {stats['total_days']} days

ATTENDANCE:
• On Time: {stats['on_time']} times
• Late: {stats['late']} times

ABSENCE:
• Absence: {stats['absent_with_leave'] + stats['absent_without_leave']} times

PERCENTAGES:
• On Time Rate: {(stats['on_time'] / stats['total_days'] * 100):.1f}%
• Late Rate: {(stats['late'] / stats['total_days'] * 100):.1f}%
• Absence Rate: {((stats['absent_with_leave'] + stats['absent_without_leave']) / stats['total_days'] * 100):.1f}%
        """

        text_widget = tk.Text(self.summary_frame, wrap=tk.WORD, font=('Arial', 12))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', summary_text)
        text_widget.config(state='disabled')

    def display_detailed(self, attendance_data, leave_data, start_date, end_date):
        # Clear previous content
        for widget in self.detailed_frame.winfo_children():
            widget.destroy()

        # Create treeview for detailed view
        columns = ('Date', 'Status', 'Time In', 'Time Out', 'Notes')
        tree = ttk.Treeview(self.detailed_frame, columns=columns, show='headings', height=20)

        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.detailed_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Create a set of leave dates for quick lookup
        leave_dict = {}
        for leave in leave_data:
            current_date = leave[0]
            while current_date <= leave[1]:
                leave_dict[current_date] = {
                    'reason': leave[2],
                    'status': leave[3]
                }
                current_date += timedelta(days=1)

        # Populate treeview
        current_date = start_date
        while current_date <= end_date:
            # Find attendance record for this date
            attendance_record = None
            for record in attendance_data:
                if record[0] == current_date:
                    attendance_record = record
                    break

            if attendance_record:
                # Has attendance
                time_in = attendance_record[1].strftime('%H:%M:%S') if attendance_record[1] else 'N/A'
                time_out = attendance_record[2].strftime('%H:%M:%S') if attendance_record[2] else 'N/A'
                status = attendance_record[3]
                note = ''
            else:
                # No attendance
                time_in = 'N/A'
                time_out = 'N/A'
                status = 'Absence'
                note = ''

            tree.insert('', 'end', values=(
                current_date.strftime('%d/%m/%Y'),
                status,
                time_in,
                time_out,
                note
            ))

            current_date += timedelta(days=1)

    def display_leave_requests(self, leave_data):
        # Clear previous content
        for widget in self.leave_frame.winfo_children():
            widget.destroy()

        if not leave_data:
            ttk.Label(self.leave_frame, text="No leave requests found in the last 30 days",
                      font=('Arial', 12)).pack(pady=50)
            return

        # Create treeview for leave requests
        columns = ('Start Date', 'End Date', 'Reason', 'Status')
        tree = ttk.Treeview(self.leave_frame, columns=columns, show='headings', height=15)

        # Configure columns
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.leave_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Populate treeview
        for leave in leave_data:
            tree.insert('', 'end', values=(
                leave[0].strftime('%d/%m/%Y'),
                leave[1].strftime('%d/%m/%Y'),
                leave[2][:50] + '...' if len(leave[2]) > 50 else leave[2],
                leave[3]
            ))


class AdminInterface:
    @staticmethod
    def start(root):
        def on_login_success():
            AdminInterface(root)

        LoginScreen(root, on_login_success)

    def __init__(self, root):
        self.root = root
        self.root.title("Employee Management")
        self.root.geometry("1400x800")

        # Pagination variables
        self.rows_per_page = 30
        self.current_page = 1

        # Date filtering variables
        self.date_filter_enabled = tk.BooleanVar(value=False)
        self.selected_date = tk.StringVar(value=date.today().strftime('%Y-%m-%d'))

        # Main container
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill='both', expand=True, padx=20, pady=10)

        # Header
        self.setup_header()

        # Status bar
        self.setup_status_bar()

        # Table
        self.setup_table()

        # Pagination
        self.setup_pagination()

        # Load initial data
        self.load_users()

    def setup_header(self):
        # Header frame
        header = ttk.Frame(self.main_container)
        header.pack(fill='x', pady=(0, 10))

        # Title
        title = ttk.Label(header, text="Employee Management Checking", font=('Arial', 24, 'bold'))
        title.pack(side='top', anchor='w')

        subtitle = ttk.Label(header,
                             text="Manage all users in one place. Control access, assign roles, and monitor activity across your platform.",
                             font=('Arial', 12))
        subtitle.pack(side='top', anchor='w', pady=(5, 15))

        # Controls frame
        controls = ttk.Frame(header)
        controls.pack(fill='x', pady=(0, 10))

        # Left side controls
        left_controls = ttk.Frame(controls)
        left_controls.pack(side='left', fill='x', expand=True)

        # Search
        search_frame = ttk.Frame(left_controls)
        search_frame.pack(side='left')
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side='left', padx=5)
        search_btn = ttk.Button(search_frame, text="Search", command=self.search_users_and_logs)
        search_btn.pack(side='left', padx=2)
        self.search_entry.bind('<Return>', lambda event: self.search_users_and_logs())

        # Role filter
        self.role_var = tk.StringVar(value="Role")
        self.role_combobox = ttk.Combobox(left_controls, textvariable=self.role_var, values=["HR", "EMPLOYEE"],
                                          state="readonly")
        self.role_combobox.pack(side='left', padx=5)
        self.role_combobox.bind("<<ComboboxSelected>>", self.on_role_selected)

        # Date filtering controls
        date_frame = ttk.Frame(left_controls)
        date_frame.pack(side='left', padx=5)

        # Date filter checkbox
        self.date_checkbox = ttk.Checkbutton(date_frame, text="Filter by date",
                                             variable=self.date_filter_enabled,
                                             command=self.toggle_date_filter)
        self.date_checkbox.pack(side='left')

        # Date picker
        self.date_picker = DateEntry(date_frame, width=12, background='darkblue',
                                     foreground='white', borderwidth=2,
                                     date_pattern='yyyy-mm-dd',
                                     textvariable=self.selected_date)
        self.date_picker.pack(side='left', padx=5)
        self.date_picker.bind("<<DateEntrySelected>>", self.on_date_selected)

        # Today button
        today_btn = ttk.Button(date_frame, text="Today", command=self.show_today_logs)
        today_btn.pack(side='left', padx=5)

        # Reset filter button
        reset_btn = ttk.Button(left_controls, text="Reset", command=self.reset_filters)
        reset_btn.pack(side='left', padx=5)

        # Right-side buttons
        ttk.Button(controls, text="Export Log", command=self.export_log).pack(side='right', padx=5)
        ttk.Button(controls, text="+ Add User", style='Black.TButton', command=self.add_user).pack(side='right',
                                                                                                    padx=5)
        ttk.Button(controls, text="User List", command=self.show_user_list).pack(side='right', padx=5)
        ttk.Button(controls, text="Delete Old Logs", command=self.delete_old_logs).pack(side='right', padx=5)
        ttk.Button(controls, text="Detailed Statistics", command=self.show_detailed_statistics).pack(side='right',
                                                                                                     padx=5)

    def setup_status_bar(self):
        # Status bar frame
        status_frame = ttk.Frame(self.main_container)
        status_frame.pack(fill='x', pady=(0, 10))

        # Status label
        self.status_label = ttk.Label(status_frame, text="Showing all logs",
                                      font=('Arial', 10), foreground='gray')
        self.status_label.pack(side='left')

    def setup_table(self):
        # Table frame
        table_frame = ttk.Frame(self.main_container)
        table_frame.pack(fill='both', expand=True)

        # Create Treeview with columns matching your database
        columns = ('id', 'user_name', 'status', 'role', 'time_in', 'time_out')
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings')

        # Column headings
        headings = {
            'id': 'ID',
            'user_name': 'User Name',
            'status': 'Status',
            'role': 'Role',
            'time_in': 'Time In',
            'time_out': 'Time Out'
        }

        # Column widths
        widths = {
            'id': 60,
            'user_name': 200,
            'status': 100,
            'role': 100,
            'time_in': 150,
            'time_out': 150
        }

        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col])

        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        # Pack elements
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.bind('<ButtonRelease-1>', self.on_tree_click)

    def load_users(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            offset = (self.current_page - 1) * self.rows_per_page
            limit = self.rows_per_page
            # Build query based on date filter
            if self.date_filter_enabled.get():
                query = """
                        SELECT l.id, u.user_name, l.status, u.role, l.time_in, l.time_out
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        WHERE DATE(l.time_in) = %s
                        ORDER BY l.time_in DESC
                        LIMIT %s OFFSET %s
                    """
                cursor.execute(query, (self.selected_date.get(), limit, offset))
            else:
                query = """
                        SELECT l.id, u.user_name, l.status, u.role, l.time_in, l.time_out
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        ORDER BY l.time_in DESC
                        LIMIT %s OFFSET %s
                    """
                cursor.execute(query, (limit, offset))
            for item in self.tree.get_children():
                self.tree.delete(item)
            late_time = datetime.strptime("00:00:00", "%H:%M:%S").time()
            for row in cursor.fetchall():
                log_id = row[0]
                time_in = row[4]
                time_out = row[5]
                # Xác định status
                if time_in and not time_out:
                    if time_in.time() > late_time:
                        status = "Late"
                    else:
                        status = "Check-in"
                elif time_in and time_out:
                    status = "Check-out"
                else:
                    status = 'unknown'
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ''
                time_out_str = time_out.strftime('%Y-%m-%d %H:%M:%S') if time_out else ''
                actions = "Account"
                values = [log_id, row[1], status, row[3], time_in_str, time_out_str, actions]
                tags = (status.lower(),)
                self.tree.insert('', 'end', values=values, tags=tags)
            # Update status bar
            self.update_status_bar()
            self.update_pagination_buttons()
        except Exception as e:
            print(f"Error loading users: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def update_status_bar(self):
        """Update the status bar with current filter information"""
        status_parts = []

        # Check if date filter is enabled
        if self.date_filter_enabled.get():
            status_parts.append(f"logs for {self.selected_date.get()}")
        else:
            status_parts.append("all logs")

        # Check if role filter is active
        if self.role_var.get() != "Role":
            status_parts.append(f"{self.role_var.get()} logs")

        # Check if search is active
        if self.search_entry.get().strip():
            status_parts.append(f"search results for '{self.search_entry.get().strip()}'")

        # Build status text
        if len(status_parts) == 1:
            status_text = f"Showing {status_parts[0]}"
        else:
            status_text = f"Showing {' '.join(status_parts)}"

        self.status_label.config(text=status_text)

    def on_date_selected(self, event=None):
        """Handle date picker selection"""
        if self.date_filter_enabled.get():
            self.load_users()

    def toggle_date_filter(self):
        """Toggle date filtering on/off"""
        self.load_users()

    def show_today_logs(self):
        """Show logs for today"""
        self.selected_date.set(date.today().strftime('%Y-%m-%d'))
        self.date_filter_enabled.set(True)
        self.load_users()

    def apply_styles(self):
        style = ttk.Style()

        # Button styles
        style.configure('Accent.TButton', background='#2563eb', foreground='white')
        style.configure('Black.TButton', background='#000000', foreground='black')

    def add_user(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add User")
        popup.geometry("400x520")

        # ID
        tk.Label(popup, text="ID:").pack()
        id_var = tk.StringVar()
        tk.Entry(popup, textvariable=id_var).pack()

        # User Name
        tk.Label(popup, text="User Name:").pack()
        user_name_var = tk.StringVar()
        tk.Entry(popup, textvariable=user_name_var).pack()

        # Image URL
        tk.Label(popup, text="Image URL (Cloudinary):").pack()
        image_url_var = tk.StringVar()
        tk.Entry(popup, textvariable=image_url_var).pack()

        # Email
        tk.Label(popup, text="Email:").pack()
        email_var = tk.StringVar()
        tk.Entry(popup, textvariable=email_var).pack()

        # Phone Number
        tk.Label(popup, text="Phone Number:").pack()
        phone_var = tk.StringVar()
        tk.Entry(popup, textvariable=phone_var).pack()

        # Role
        tk.Label(popup, text="Role:").pack()
        role_var = tk.StringVar(value="EMPLOYEE")
        role_combo = ttk.Combobox(popup, textvariable=role_var, values=["HR", "EMPLOYEE"], state="readonly")
        role_combo.pack()

        # Password (only for HR)
        password_label = tk.Label(popup, text="Password:")
        password_var = tk.StringVar()
        password_entry = tk.Entry(popup, textvariable=password_var, show="*")

        def on_role_change(event=None):
            if role_var.get() == "HR":
                password_label.pack()
                password_entry.pack()
            else:
                password_label.pack_forget()
                password_entry.pack_forget()

        role_combo.bind("<<ComboboxSelected>>", on_role_change)
        on_role_change()  # Initial call

        def save():
            id_val = id_var.get().strip()
            user_name = user_name_var.get().strip()
            image_url = image_url_var.get().strip()
            email = email_var.get().strip()
            phone = phone_var.get().strip()
            role = role_var.get()
            password = password_var.get().strip() if role == "HR" else None

            # Validate
            if not id_val or not user_name or not email or not phone or not role:
                messagebox.showerror("Error", "Please fill in all required fields.")
                return
            if not id_val.isdigit():
                messagebox.showerror("Error", "ID must be a number.")
                return
            if role == "HR" and not password:
                messagebox.showerror("Error", "Password is required for HR role.")
                return
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                # Check if id, username hoặc email đã tồn tại
                cursor.execute("SELECT 1 FROM users WHERE id=%s OR user_name=%s OR email=%s",
                               (id_val, user_name, email))
                if cursor.fetchone():
                    messagebox.showerror("Error", "ID, Username hoặc Email đã tồn tại.")
                    return
                # Insert user
                if role == "HR":
                    cursor.execute(
                        "INSERT INTO users (id, user_name, image_url, email, phone_number, password, role) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (id_val, user_name, image_url, email, phone, password, role)
                    )
                else:
                    cursor.execute(
                        "INSERT INTO users (id, user_name, image_url, email, phone_number, role) VALUES (%s, %s, %s, %s, %s, %s)",
                        (id_val, user_name, image_url, email, phone, role)
                    )
                conn.commit()
                messagebox.showinfo("Success", "User added successfully!")
                popup.destroy()
                self.load_users()
            except Exception as e:
                messagebox.showerror("Error", f"Error: {e}")
            finally:
                if conn:
                    cursor.close()
                    conn.close()

        tk.Button(popup, text="Save", command=save).pack(pady=20)

    def export_log(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()

            # Build export query with date filter support
            if self.date_filter_enabled.get():
                cursor.execute("""
                        SELECT u.user_name, l.status, u.role, l.time_in, l.time_out, u.ip_address
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        WHERE DATE(l.time_in) = %s
                        ORDER BY l.time_in DESC
                    """, (self.selected_date.get(),))
            else:
                cursor.execute("""
                        SELECT u.user_name, l.status, u.role, l.time_in, l.time_out, u.ip_address
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        ORDER BY l.time_in DESC
                    """)

            rows = cursor.fetchall()
            columns = ['User Name', 'Status', 'Role', 'Time In', 'Time Out', 'IP Address']
            df = pd.DataFrame(rows, columns=columns)
            # Hiển thị hộp thoại chọn nơi lưu file
            file_path = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx')],
                title='Save Log As...'
            )
            if file_path:
                df.to_excel(file_path, index=False)
                messagebox.showinfo('Export Success', f'Log exported to {file_path}')
        except Exception as e:
            messagebox.showerror('Export Error', f'Error exporting log: {e}')
        finally:
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def setup_pagination(self):
        self.pagination_frame = ttk.Frame(self.main_container)
        self.pagination_frame.pack(fill='x', pady=10)
        self.update_pagination_buttons()

    def update_pagination_buttons(self):
        # Xóa các nút cũ
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()
        # Tính tổng số dòng
        total_rows = self.get_total_rows()
        total_pages = max(1, (total_rows + self.rows_per_page - 1) // self.rows_per_page)

        # Nút chuyển trang
        def goto_page(page):
            self.current_page = page
            self.load_users()

        ttk.Label(self.pagination_frame, text=f"Rows per page: {self.rows_per_page}").pack(side='left')
        ttk.Button(self.pagination_frame, text="«", width=3, command=lambda: goto_page(1)).pack(side='left', padx=2)
        ttk.Button(self.pagination_frame, text="‹", width=3,
                   command=lambda: goto_page(max(1, self.current_page - 1))).pack(side='left', padx=2)
        # Hiển thị số trang (tối đa 5 số, ... nếu nhiều)
        page_range = self.get_page_range(self.current_page, total_pages)
        for p in page_range:
            if p == '...':
                btn = ttk.Label(self.pagination_frame, text="...", width=3)
            else:
                style = {'relief': 'sunken'} if p == self.current_page else {}
                btn = ttk.Button(self.pagination_frame, text=str(p), width=3, command=lambda pg=p: goto_page(pg))
            btn.pack(side='left', padx=2)
        ttk.Button(self.pagination_frame, text="›", width=3,
                   command=lambda: goto_page(min(total_pages, self.current_page + 1))).pack(side='left', padx=2)
        ttk.Button(self.pagination_frame, text="»", width=3, command=lambda: goto_page(total_pages)).pack(side='left',
                                                                                                          padx=2)

    def get_total_rows(self):
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            # Đếm tổng số dòng theo filter hiện tại
            if self.date_filter_enabled.get():
                cursor.execute("""
                        SELECT COUNT(*) FROM users u LEFT JOIN logs l ON u.id = l.user_id WHERE DATE(l.time_in) = %s
                    """, (self.selected_date.get(),))
            else:
                cursor.execute("""
                        SELECT COUNT(*) FROM users u LEFT JOIN logs l ON u.id = l.user_id
                    """)
            total = cursor.fetchone()[0]
            return total
        except Exception as e:
            return 0
        finally:
            if 'conn' in locals() and conn:
                cursor.close()
                conn.close()

    def get_page_range(self, current, total):
        # Hiển thị tối đa 5 số trang, ... nếu nhiều
        if total <= 5:
            return list(range(1, total + 1))
        if current <= 3:
            return [1, 2, 3, 4, '...', total]
        if current >= total - 2:
            return [1, '...', total - 3, total - 2, total - 1, total]
        return [1, '...', current - 1, current, current + 1, '...', total]

    def on_tree_click(self, event):
        item_id = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not item_id or col != '#7':
            return
        values = self.tree.item(item_id, 'values')
        user_name = values[0]
        self.show_user_popup(user_name)

    def show_user_list(self):
        popup = tk.Toplevel(self.root)
        popup.title("User List")
        popup.geometry("1050x400")
        columns = ('id', 'user_name', 'email', 'phone_number', 'role')
        tree = ttk.Treeview(popup, columns=columns, show='headings')
        headings = {
            'id': 'ID',
            'user_name': 'User Name',
            'email': 'Email',
            'phone_number': 'Phone Number',
            'role': 'Role'
        }
        widths = {
            'id': 50,
            'user_name': 150,
            'email': 180,
            'phone_number': 120,
            'role': 100
        }
        for col in columns:
            tree.heading(col, text=headings[col])
            tree.column(col, width=widths[col])
        tree.pack(side='left', fill='both', expand=True)

        # Frame chứa các nút
        button_frame = tk.Frame(popup)
        button_frame.pack(side='right', fill='y')

        # Load data
        user_rows = []
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT id, user_name, email, phone_number, role FROM users ORDER BY id")
            for row in cursor.fetchall():
                tree.insert('', 'end', iid=str(row[0]), values=row)
                user_rows.append(row)
        except Exception as e:
            tk.Label(popup, text=f"Error: {e}").pack()
            return
        finally:
            if conn:
                cursor.close()
                conn.close()

        # Thêm nút Edit và Delete cho từng dòng
        for row in user_rows:
            user_id = row[0]
            row_frame = tk.Frame(button_frame)
            row_frame.pack(fill='x', pady=2)
            tk.Label(row_frame, text=f"ID {user_id}", width=6).pack(side='left')
            tk.Button(row_frame, text="Edit", width=6,
                      command=lambda uid=user_id: self.edit_user_popup(uid, popup, tree)).pack(side='left', padx=2)
            tk.Button(row_frame, text="Delete", width=6,
                      command=lambda uid=user_id: self.delete_user(uid, tree, str(uid))).pack(side='left', padx=2)

    def edit_user_popup(self, user_id, parent_popup, tree):
        popup = tk.Toplevel(parent_popup)
        popup.title("Edit User")
        popup.geometry("350x350")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT user_name, email, phone_number, role, ip_address FROM users WHERE id = %s",
                           (user_id,))
            user = cursor.fetchone()
        except Exception as e:
            tk.Label(popup, text=f"Error: {e}").pack()
            return
        finally:
            if conn:
                cursor.close()
                conn.close()
        tk.Label(popup, text="User Name:").pack()
        name_var = tk.StringVar(value=user[0])
        tk.Entry(popup, textvariable=name_var).pack()
        tk.Label(popup, text="Email:").pack()
        email_var = tk.StringVar(value=user[1])
        tk.Entry(popup, textvariable=email_var).pack()
        tk.Label(popup, text="Phone Number:").pack()
        phone_var = tk.StringVar(value=user[2])
        tk.Entry(popup, textvariable=phone_var).pack()
        tk.Label(popup, text="Role:").pack()
        role_map = {"HR": "HR", "EMPLOYEE": "EMPLOYEE"}
        reverse_role_map = {v: k for k, v in role_map.items()}
        valid_labels = list(role_map.keys())
        current_label = reverse_role_map.get(user[3], "EMPLOYEE")
        role_var = tk.StringVar(value=current_label)
        role_combo = ttk.Combobox(popup, textvariable=role_var, values=valid_labels, state="readonly")
        role_combo.pack()
        tk.Label(popup, text="IP Address:").pack()
        ip_var = tk.StringVar(value=user[4])
        tk.Entry(popup, textvariable=ip_var).pack()

        def save():
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                role_value = role_map.get(role_var.get(), "EMPLOYEE")
                cursor.execute(
                    "UPDATE users SET user_name=%s, email=%s, phone_number=%s, role=%s, ip_address=%s WHERE id=%s",
                    (name_var.get().strip(), email_var.get().strip(), phone_var.get().strip(), role_value,
                     ip_var.get().strip(), user_id)
                )
                conn.commit()
                messagebox.showinfo("Success", "User updated successfully!")
                for item in tree.get_children():
                    tree.delete(item)
                cursor.execute("SELECT id, user_name, email, phone_number, role, ip_address FROM users ORDER BY id")
                for row in cursor.fetchall():
                    actions = "Edit | Delete"
                    role_label = reverse_role_map.get(row[4], row[4])
                    tree.insert('', 'end', values=[row[0], row[1], row[2], row[3], role_label, row[5], actions])
                popup.destroy()
            except Exception as e:
                tk.Label(popup, text=f"Error: {e}", fg="red").pack()
            finally:
                if conn:
                    cursor.close()
                    conn.close()

        tk.Button(popup, text="Save", command=save).pack(pady=10)

    def delete_user(self, user_id, tree, item_id):
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this user?")
        if not confirm:
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM logs WHERE user_id=%s", (user_id,))
            cursor.execute("DELETE FROM leave_requests WHERE user_id=%s", (user_id,))
            cursor.execute("DELETE FROM users WHERE id=%s", (user_id,))
            conn.commit()
            tree.delete(item_id)
        except psycopg2.errors.ForeignKeyViolation:
            messagebox.showerror(
                "Error",
                "Cannot delete this user because it is still referenced in other tables."
            )
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def show_user_popup(self, user_name):
        popup = tk.Toplevel(self.root)
        popup.title(f"User: {user_name}")
        popup.geometry("400x200")
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("SELECT user_name, role FROM users WHERE user_name = %s", (user_name,))
            user = cursor.fetchone()
        except Exception as e:
            tk.Label(popup, text=f"Error: {e}").pack()
            return
        finally:
            if conn:
                cursor.close()
                conn.close()
        tk.Label(popup, text="User Name:").pack()
        name_var = tk.StringVar(value=user[0])
        name_entry = tk.Entry(popup, textvariable=name_var)
        name_entry.pack()
        tk.Label(popup, text="Role:").pack()
        role_var = tk.StringVar(value=user[1])
        role_entry = tk.Entry(popup, textvariable=role_var)
        role_entry.pack()

        def save_changes():
            try:
                conn = psycopg2.connect(**DB_CONFIG)
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE users SET user_name=%s, role=%s WHERE user_name=%s",
                    (name_var.get(), role_var.get(), user_name)
                )
                conn.commit()
                messagebox.showinfo("Success", "User updated successfully!")
                self.load_users()
                popup.destroy()
            except Exception as e:
                tk.Label(popup, text=f"Error: {e}", fg="red").pack()
            finally:
                if conn:
                    cursor.close()
                    conn.close()

        tk.Button(popup, text="Save", command=save_changes).pack(pady=10)

    def delete_old_logs(self):
        from datetime import datetime, timedelta
        # Hộp thoại chọn số ngày
        choice = messagebox.askquestion(
            "Delete Old Logs",
            "Delete logs older than:\n\nYes: 1 day\nNo: 30 days",
            icon='question'
        )
        if choice == 'yes':
            days = 1
        elif choice == 'no':
            days = 30
        else:
            return

        cutoff = datetime.now() - timedelta(days=days)
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete all logs older than {days} day(s)?\n(This cannot be undone!)"
        )
        if not confirm:
            return
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM logs WHERE time_in < %s", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            messagebox.showinfo("Success", f"Deleted {deleted} old log(s).")
            self.load_users()
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def search_users_and_logs(self):
        keyword = self.search_entry.get().strip()
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            offset = (self.current_page - 1) * self.rows_per_page
            limit = self.rows_per_page
            # Build search query with date filter support
            if self.date_filter_enabled.get():
                query = '''
                        SELECT u.user_name, l.status, CAST(u.role AS TEXT), l.time_in, l.time_out, u.ip_address
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        WHERE (
                            u.user_name ILIKE %s OR
                            u.email ILIKE %s OR
                            CAST(u.role AS TEXT) ILIKE %s OR
                            l.status ILIKE %s OR
                            u.ip_address ILIKE %s
                        ) AND DATE(l.time_in) = %s
                        ORDER BY l.time_in DESC
                        LIMIT %s OFFSET %s
                    '''
                like_kw = f"%{keyword}%"
                cursor.execute(query,
                               (like_kw, like_kw, like_kw, like_kw, like_kw, self.selected_date.get(), limit, offset))
            else:
                query = '''
                        SELECT u.user_name, l.status, CAST(u.role AS TEXT), l.time_in, l.time_out, u.ip_address
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        WHERE (
                            u.user_name ILIKE %s OR
                            u.email ILIKE %s OR
                            CAST(u.role AS TEXT) ILIKE %s OR
                            l.status ILIKE %s OR
                            u.ip_address ILIKE %s
                        )
                        ORDER BY l.time_in DESC
                        LIMIT %s OFFSET %s
                    '''
                like_kw = f"%{keyword}%"
                cursor.execute(query, (like_kw, like_kw, like_kw, like_kw, like_kw, limit, offset))
            for item in self.tree.get_children():
                self.tree.delete(item)
            late_time = datetime.strptime("00:00:00", "%H:%M:%S").time()
            for row in cursor.fetchall():
                time_in = row[3]
                time_out = row[4]
                if time_in and not time_out:
                    if time_in.time() > late_time:
                        status = "Late"
                    else:
                        status = "Check-in"
                elif time_in and time_out:
                    status = "Check-out"
                else:
                    status = 'unknown'
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ''
                time_out_str = time_out.strftime('%Y-%m-%d %H:%M:%S') if time_out else ''
                actions = "Account"
                values = [row[0], status, row[2], time_in_str, time_out_str, row[5], actions]
                tags = (status.lower(),)
                self.tree.insert('', 'end', values=values, tags=tags)
            # Update status bar
            self.update_status_bar()
            self.update_pagination_buttons()
        except Exception as e:
            messagebox.showerror("Error", f"Search error: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def on_role_selected(self, event):
        role = self.role_combobox.get()
        self.role_var.set(role)
        self.apply_role_filter(role)

    def apply_role_filter(self, role):
        """Apply role filter with date filter support"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cursor = conn.cursor()
            offset = (self.current_page - 1) * self.rows_per_page
            limit = self.rows_per_page
            # Build query with role and date filters
            if self.date_filter_enabled.get():
                query = """
                        SELECT u.user_name, l.status, u.role, l.time_in, l.time_out, u.ip_address
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        WHERE u.role = %s AND DATE(l.time_in) = %s
                        ORDER BY l.time_in DESC
                        LIMIT %s OFFSET %s
                    """
                cursor.execute(query, (role, self.selected_date.get(), limit, offset))
            else:
                query = """
                        SELECT u.user_name, l.status, u.role, l.time_in, l.time_out, u.ip_address
                        FROM users u
                        LEFT JOIN logs l ON u.id = l.user_id
                        WHERE u.role = %s
                        ORDER BY l.time_in DESC
                        LIMIT %s OFFSET %s
                    """
                cursor.execute(query, (role, limit, offset))
            for item in self.tree.get_children():
                self.tree.delete(item)
            late_time = datetime.strptime("00:00:00", "%H:%M:%S").time()
            for row in cursor.fetchall():
                time_in = row[3]
                time_out = row[4]
                if time_in and not time_out:
                    if time_in.time() > late_time:
                        status = "Late"
                    else:
                        status = "Check-in"
                elif time_in and time_out:
                    status = "Check-out"
                else:
                    status = 'unknown'
                time_in_str = time_in.strftime('%Y-%m-%d %H:%M:%S') if time_in else ''
                time_out_str = time_out.strftime('%Y-%m-%d %H:%M:%S') if time_out else ''
                actions = "Account"
                values = [row[0], status, row[2], time_in_str, time_out_str, row[5], actions]
                tags = (status.lower(),)
                self.tree.insert('', 'end', values=values, tags=tags)
            # Update status bar
            self.update_status_bar()
            self.update_pagination_buttons()
        except Exception as e:
            print(f"Error applying role filter: {e}")
        finally:
            if conn:
                cursor.close()
                conn.close()

    def reset_filters(self):
        self.role_var.set("Role")
        self.role_combobox.set("Role")
        self.date_filter_enabled.set(False)
        self.selected_date.set(date.today().strftime('%Y-%m-%d'))
        self.search_entry.delete(0, tk.END)
        self.load_users()

    def show_detailed_statistics(self):
        """Open detailed statistics window"""
        DetailedStatisticsWindow(self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = AdminInterface(root)
    app.apply_styles()
    root.mainloop()
