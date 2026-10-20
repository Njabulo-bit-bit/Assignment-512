import tkinter as tk

from database import Database
from gui import LoginWindow, SetupWindow

def main():
    database = Database()
    database.setup_database()

    root = tk.Tk()

    if database.user_count() == 0:
        SetupWindow(root, database)
    else:
        LoginWindow(root, database)

    root.mainloop()

if __name__ == '__main__':
    main()