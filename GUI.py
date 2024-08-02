# built in modules
# for threading
# for checking all the process outputs
import subprocess
import threading

# for delaying execution
import time

# for handling the GUI
import tkinter as tk

# 3rd party modules
# for handling the GUI
import customtkinter as ctk

# for checking the windows
import pyautogui

# Local modules
# for talking with the arduino
from arduino import Arduino

# for handling the database
from db import DB

# holds all the global vars
from variables import checked, kill, reading

went_through = []

# kill timer flag. when True it kills the timeout threads active
kill_timer = [False]

# set to True to enable logging
logging = False

# set end flag
end = False


# log function. prints the message if logging is enabled. for development purposes
def log(*x):
    global logging
    if logging:
        print(*x)


def clear_checked_if_locked():
    global checked, end
    process_name = "LogonUI.exe"
    callall = "TASKLIST"
    log("watching for lock")
    while True:
        if end:
            print("killing lock watcher")
            break
        outputall = subprocess.check_output(callall)
        outputstringall = str(outputall)
        if process_name in outputstringall:
            log("locked, clearing checked")
            if len(checked) > 0:
                checked.clear()


# timeout function. it waits for a certain amount of time and then calls the callback function
def timeout(sec, callback):
    global kill_timer
    # reset kill timer flag
    kill_timer[0] = False
    # wait for sec seconds
    for i in range(sec)[::-1]:
        # if kill timer flag is True, return
        if kill_timer[0]:
            return
        log(i)
        # wait for 1 second
        time.sleep(1)
    # call the callback function
    callback()


class GUI:
    def __init__(self):
        #! connect to the database
        self.db = DB("root", "jan04198", log=True)

        #! create the database
        self.db.create_database("program_manager")
        self.db.use("program_manager")

        #! create the tables
        self.db.create_table(
            "programs",
            {
                "id": {"data_type": "INT", "keys": ["PRIMARY KEY", "AUTO_INCREMENT"]},
                "name": {"data_type": "VARCHAR(255)"},
                "description": {"data_type": "TEXT"},
            },
        )

        self.db.create_table(
            "users",
            {
                "id": {"data_type": "INT", "keys": ["PRIMARY KEY", "AUTO_INCREMENT"]},
                "username": {"data_type": "VARCHAR(255)"},
                "fingerprintID": {"data_type": "INT", "keys": ["UNIQUE", "NOT NULL"]},
            },
        )

        self.db.create_table(
            "access",
            {
                "id": {"data_type": "INT", "keys": ["PRIMARY KEY", "AUTO_INCREMENT"]},
                "uid": {
                    "data_type": "INT",
                    "keys": ["NOT NULL"],
                },
                "pid": {
                    "data_type": "INT",
                    "keys": ["NOT NULL"],
                },
            },
            constraints=[
                "FOREIGN KEY (uid) REFERENCES users(id)",
                "FOREIGN KEY (pid) REFERENCES programs(id)",
            ],
        )

        self.db.create_table(
            "fingerprints",
            {
                "Id": {"data_type": "INT", "keys": ["PRIMARY KEY", "AUTO_INCREMENT"]},
                "FingerprintID": {"data_type": "INT", "keys": ["UNIQUE", "NOT NULL"]},
                "uid": {"data_type": "INT", "keys": ["NOT NULL"]},
            },
            constraints=["FOREIGN KEY (uid) REFERENCES users(id)"],
        )

        #! connect to the arduino
        self.arduino = Arduino("COM12", 9600)

        #! create the root window+
        self.root = tk.Tk()
        self.root.title("Custom Tkinter")
        self.root.geometry("1920x1080")
        self.w = 1920
        self.h = 1080
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        #! program list window section
        self.program_list_window = ctk.CTkFrame(self.root, corner_radius=0)
        # top bar
        self.program_list_window_top_bar = ctk.CTkFrame(
            self.program_list_window, corner_radius=0
        )
        # title
        self.program_list_title = ctk.CTkLabel(
            self.program_list_window_top_bar, text="Programs"
        )
        # place the title
        self.program_list_title.place(relx=0, rely=0, relwidth=0.8, relheight=1)

        # add program button
        ctk.CTkButton(
            self.program_list_window_top_bar,
            text="Add Program",
            command=self.add_program,
        ).place(relx=0.8, rely=0.5, relwidth=0.2, anchor=tk.CENTER)
        # place the top bar
        self.program_list_window_top_bar.place(
            relx=0, rely=0, relwidth=1, relheight=0.1
        )

        # add program button. this should only be visible if there are no programs
        self.add_program_button = ctk.CTkButton(
            self.program_list_window,
            text="Add Program",
            command=self.add_program,
        )

        # program list which will show all the programs on the watch list
        self.program_list = ctk.CTkScrollableFrame(
            self.program_list_window, height=self.h, corner_radius=0
        )

        # populate the program list window
        self.populate_programs_window()

        #! program window section
        # selected program
        self.selected = None

        # program window
        self.program_window = ctk.CTkFrame(self.root, height=self.h, corner_radius=0)

        # select program label which will be visible if no program is selected
        self.select_program_label = ctk.CTkLabel(
            self.program_window, text="Select Program"
        )

        # program info window
        self.program_info = ctk.CTkFrame(self.program_window, corner_radius=0)
        # program name label
        self.program_name = ctk.CTkLabel(
            self.program_info,
            text=f"Program Name: {self.selected.name if self.selected else ''}",
        )
        # place the program name
        self.program_name.place(
            relx=0.5, rely=0.5, relwidth=1, relheight=0.1, anchor=tk.CENTER
        )

        # program users window
        self.program_users_frame = ctk.CTkFrame(self.program_window, corner_radius=0)
        # top bar
        top_heading = ctk.CTkFrame(self.program_users_frame, corner_radius=0)
        # place the top bar
        top_heading.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        # title
        ctk.CTkLabel(top_heading, text="Users").place(
            relx=0, rely=0, relwidth=0.8, relheight=1
        )
        # add user button
        self.add_user_top_button = ctk.CTkButton(
            top_heading,
            text="Add User",
        )
        # place the add user button
        self.add_user_top_button.place(
            relx=0.8, rely=0.5, relwidth=0.2, anchor=tk.CENTER
        )
        # users list
        self.program_users = ctk.CTkScrollableFrame(
            self.program_users_frame, corner_radius=0
        )

        # add user button only visible if no users are in the program
        self.add_user_button = ctk.CTkButton(
            self.program_users_frame,
            text="Add User",
        )

        # populate the program window
        self.populate_program_window()

        # pack the frames
        self.program_list_window.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        self.program_window.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)

        # start the lock watcher
        threading.Thread(target=clear_checked_if_locked).start()
        # call the mainloop
        self.run()

    def run(self):
        # run the mainloop
        self.root.mainloop()

    def clear_children(self, parent: ctk.CTkBaseClass):
        """
        clears all the children of the parent widget

        Args:
            parent (ctk.CTkBaseClass): the parent widget

        Returns:
            None
        """
        for child in parent.winfo_children():
            child.destroy()

    def populate_programs_window(self):
        """
        populates the program list window

        Returns:
            None
        """

        # set the kill flag to True to kill the window watcher
        global kill
        kill = True
        # get all the programs
        programs = self.db.query().select().from_table("programs").execute()

        # if no programs, return
        if len(programs) == 0:
            # remove the program list
            self.program_list.place_forget()
            # place the add program button
            self.add_program_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            return

        # remove the add program button
        self.add_program_button.place_forget()

        # place list after top bar
        self.program_list.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        # clear the program list
        self.clear_children(self.program_list)
        # populate the program list
        for program in programs:
            container = ctk.CTkFrame(self.program_list, corner_radius=0)
            # place container with fill x and auto y
            container.pack(fill="x")
            # buttons with the same height as the container
            # select button 80% width
            ctk.CTkButton(
                container,
                text=program.name,
                command=lambda program=program: self.select_program(program),
                fg_color="transparent",
                hover=False,
            ).pack(side="left", fill="x", expand=True)
            # delete button 20% width
            ctk.CTkButton(
                container,
                text="Delete",
                command=lambda program=program: self.delete_program(program),
            ).pack(side="right", fill="x", expand=True)
            # place the buttons

        # create a new window watcher
        self.watcher = window_watcher(
            self.db.query().select().from_table("programs").execute(),
            callbacks={Verify_Access: {"parent": self, "target": None}},
        )

    def select_program(self, program):
        """
        selects the program

        Args:
            program (Record): the program to select

        Returns:
            None
        """
        # set the selected program
        self.selected = program
        # populate the program window
        self.populate_program_window()

    def populate_program_window(self):
        """
        populates the program window

        Returns:
            None
        """
        # if no program is selected
        if self.selected != None:
            # get rid of label
            self.select_program_label.place_forget()

            # change program name
            self.program_name.configure(
                text=f"Program Name: {self.selected.name}",
            )
            # empty list of users
            self.clear_children(self.program_users)

            # place the program info
            self.program_info.place(relx=0, rely=0, relwidth=1, relheight=0.1)
            # place the program users
            self.program_users_frame.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)
            self.program_users.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

            # place the add user button
            self.add_user_top_button.configure(
                command=lambda program=self.selected: self.add_user(program)
            )

            # get all the users in the program
            users = (
                self.db.query()
                .select()
                .from_table("users")
                .in_column(
                    id=self.db.query()
                    .select(["uid"])
                    .from_table("access")
                    .equals(pid=self.selected.id)
                )
                .execute()
            )

            # if no users in the program
            if len(users) == 0:
                # remove the add user button
                self.program_users.place_forget()
                # place the add user button this is necessary to refresh button content
                self.add_user_button.configure(
                    command=lambda program=self.selected: self.add_user(program)
                )
                self.add_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                return

            # if users are there
            # remove the add user button
            self.add_user_button.place_forget()

            # populate the users
            for user in users:
                # create a frame for each user
                userFrame = ctk.CTkFrame(self.program_users, corner_radius=0)
                userFrame.pack(fill="x")

                # create a button with the user name
                ctk.CTkButton(
                    userFrame,
                    text=user.username,
                    command=lambda user=user: self.delete_user_from_program(user),
                    fg_color="transparent",
                    hover=False,
                ).pack(side="left", fill="x", expand=True)

                # create a delete button
                ctk.CTkButton(
                    userFrame,
                    text="Delete",
                    command=lambda user=user: self.delete_user_from_program(user),
                ).pack(side="right", fill="x", expand=True)
        else:
            # if no program is selected
            # remove the program info
            self.program_info.place_forget()
            # remove the program users
            self.program_users_frame.place_forget()
            # place the select program label
            self.select_program_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def delete_user_from_program(self, user):
        """
        deletes the user from the program

        Args:
            user (Record): the user to delete

        Returns:
            None
        """
        # delete the user from the program
        self.db.query().delete("access").equals(
            uid=user.id, pid=self.selected.id
        ).execute()
        # refresh the program window
        self.populate_program_window()

    def delete_program(self, program):
        """
        deletes the program

        Args:
            program (Record): the program to delete

        Returns:
            None
        """
        # get program id
        program_id = program.id
        # remove access for users for this program. necessary due to sql reference
        self.db.query().delete("access").equals(pid=program_id).execute()
        # remove the program
        self.db.query().delete("programs").equals(id=program_id).execute()

        # if the selected program is the one being deleted
        if self.selected:
            if self.selected.id == program_id:
                # set selected to None
                self.selected = None
                # refresh the program window
                self.populate_program_window()

        # refresh the program list
        self.clear_children(self.program_list)
        self.populate_programs_window()

    def add_program(self):
        """
        adds a program

        Returns:
            None
        """

        # create a new add program window
        Add_program(self)

    def add_user(self, program):
        """
        adds a user to the program

        Args:
            program (Record): the program to add the user to

        Returns:
            None
        """
        # create a new add user window
        Add_user_to_program_window(self, program, self.populate_program_window)

    def on_close(self):
        """
        called when the window is closed

        Returns:
            None
        """
        # set the kill flag to True
        global kill, end
        kill = True
        end = True
        # destroy the UI
        self.root.destroy()
        # close arduino serial connection
        self.arduino.close()
        # close the database connection
        self.db.conn.close()
        # exit the program
        exit()


class Add_User_Window:
    def __init__(self, parent: GUI, callback=None):
        """
        Add user window

        Args:
            parent (GUI): the parent GUI
            callback (function): the function to call after the user is added

        Returns:
            None
        """
        # set the parent
        self.parent = parent

        # create a new window
        self.window = ctk.CTkToplevel(self.parent.root)
        # set the window to the top
        self.window.attributes("-topmost", True)
        # set the title
        self.window.title("Add User")
        # set the geometry
        self.window.geometry(f"{self.parent.w//2}x{self.parent.h//2}")

        # set the callback
        self.callback = callback

        # user name label
        self.user_name_label = ctk.CTkLabel(self.window, text="User Name")
        # user name entry
        self.user_name_entry = ctk.CTkEntry(self.window)

        # fingerprint label
        self.fingerprint_label = ctk.CTkLabel(self.window, text="Fingerprint ID")
        # fingerprint entry
        self.fingerprint_entry = ctk.CTkEntry(self.window)

        # add user button
        self.add_user_button = ctk.CTkButton(
            self.window, text="Add User", command=self.add_user
        )

        # message label
        self.user_name_label.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        self.user_name_entry.place(relx=0, rely=0.1, relwidth=1, relheight=0.1)

        # place the fingerprint label and entry
        self.fingerprint_label.place(relx=0, rely=0.2, relwidth=1, relheight=0.1)
        self.fingerprint_entry.place(relx=0, rely=0.3, relwidth=1, relheight=0.1)

        # place the add user button
        self.add_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # message label
        self.message_label = ctk.CTkLabel(self.window, text="")
        self.message_label.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

        # run the window
        self.run()

    def add_user(self):
        # check if the user name is empty
        if self.user_name_entry.get() == "" or self.user_name_entry.get() == None:
            # set the message label
            self.message_label.configure(text="User name is required")
            return
        # check if the fingerprint id is empty
        if self.fingerprint_entry.get() == "" or self.fingerprint_entry.get() == None:
            # set the message label
            self.message_label.configure(text="Fingerprint ID is required")
            return
        # check if the fingerprint id is a number
        if not self.fingerprint_entry.get().isdigit():
            # set the message label
            self.message_label.configure(text="Fingerprint ID must be a number")
            return
        # check if the fingerprint id is between 1 and 127
        if (
            int(self.fingerprint_entry.get()) < 1
            or int(self.fingerprint_entry.get()) > 127
        ):
            # set the message label
            self.message_label.configure(
                text="Fingerprint ID must be between 1 and 127"
            )
            return
        # check if the user name already exists
        if (
            self.parent.db.query()
            .select()
            .from_table("users")
            .equals(username=self.user_name_entry.get())
            .execute()
        ):
            # set the message label
            self.message_label.configure(text="User name already exists")
            return
        # check if the fingerprint id already exists
        if (
            self.parent.db.query()
            .select()
            .from_table("users")
            .equals(fingerprintID=self.fingerprint_entry.get())
            .execute()
        ):
            # set the message label
            self.message_label.configure(text="Fingerprint ID already exists")
            return

        # start reading from the arduino
        self.parent.arduino.start_reading()
        # wait for the arduino to ask for the choice
        self.parent.arduino.wait_for(["Enter choice: "])
        # write the choice
        self.parent.arduino.write("1")
        # wait for the arduino to ask for the fingerprint id
        self.parent.arduino.wait_for(["Enter finger print id from 1 to 127"])
        # write the fingerprint id
        self.parent.arduino.write(self.fingerprint_entry.get())

        # take fingerprint
        while True:
            # wait for the arduino to ask for the fingerprint or processes it
            read = self.parent.arduino.wait_for(
                ["place finger", "remove finger", "stored!"]
            )
            # if the fingerprint is stored, break
            if "stored!" in read:
                self.message_label.configure(text="Fingerprint stored!")
                break
            # if the arduino asks to place the finger, set the message label
            if "place finger" in read:
                self.message_label.configure(text="Place finger")
            # if the arduino asks to remove the finger, set the message label
            if "remove finger" in read:
                self.message_label.configure(text="Remove finger")

        # create the user
        self.parent.db.query().insert(
            "users",
            username=self.user_name_entry.get(),
            fingerprintID=self.fingerprint_entry.get(),
        ).values(
            [(self.user_name_entry.get(), int(self.fingerprint_entry.get()))]
        ).execute()

        # if any callback is set, call it
        if self.callback != None:
            self.callback()

        # close the window
        self.window.destroy()

    def run(self):
        """
        runs the window

        Returns:
            None
        """
        # run the window
        self.window.mainloop()


class Add_user_to_program_window:
    def __init__(self, parent: GUI, program, callback=None):
        """
        Add user to program window

        Args:
            parent (GUI): the parent GUI
            program (Record): the program to add the user to
            callback (function): the function to call after the user is added

        Returns:
            None
        """

        # set the callback
        self.callback = callback
        # set the parent
        self.parent = parent
        # create a new window
        self.window = ctk.CTkToplevel(self.parent.root)
        # set the window to the top
        self.window.attributes("-topmost", True)
        # set the title
        self.window.title("Add User")
        # set the geometry
        self.window.geometry(f"{self.parent.w//2}x{self.parent.h//2}")

        # set the program
        self.program = program

        # user list window
        self.selected = None
        # user list window
        self.user_list_window = ctk.CTkFrame(self.window, corner_radius=0)
        # top bar
        user_list_window_top_bar = ctk.CTkFrame(self.user_list_window, corner_radius=0)
        # title
        user_list_title = ctk.CTkLabel(user_list_window_top_bar, text="Users")
        # add user button
        add_user_button = ctk.CTkButton(
            user_list_window_top_bar, text="Add User", command=self.add_new_user
        )
        # user list
        self.user_list = ctk.CTkScrollableFrame(self.user_list_window, corner_radius=0)

        # user window
        self.add_new_user_button = ctk.CTkButton(
            self.user_list_window, text="Add new user", command=self.add_new_user
        )

        # user window
        user_list_window_top_bar.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        # user list title
        user_list_title.place(relx=0, rely=0, relwidth=0.8, relheight=1)
        # add user button
        add_user_button.place(relx=0.8, rely=0.5, relwidth=0.2, anchor=tk.CENTER)
        # user list
        self.user_list.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        # user window
        self.user_window = ctk.CTkFrame(self.window, corner_radius=0)
        # user name
        self.user_name = ctk.CTkLabel(
            self.user_window,
            text=f"User Name: {self.selected.username if self.selected else ''}",
        )
        # select user button
        self.select_user_button = ctk.CTkButton(
            self.user_window,
            text="Select User",
        )
        # delete user button
        self.delete_user_button = ctk.CTkButton(
            self.user_window,
            text="Delete User",
        )

        # if not selected
        self.user_window_select_label = ctk.CTkLabel(
            self.user_window, text="Select User"
        )
        # user name
        self.user_window_select_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # place the user list window
        self.populate_user_list()

        # place the user list window
        self.user_list_window.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        # place the user window
        self.user_window.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)

        # run the window
        self.run()

    def add_new_user(self):
        """
        adds a new user

        Returns:
            None
        """
        # create a new add user window
        self.window.attributes("-topmost", False)
        # create a new add user window
        Add_User_Window(self.parent, self.populate_user_list)

    def populate_user_list(self):
        """
        populates the user list

        Returns:
            None
        """
        # get all the users
        self.clear_children(self.user_list)

        # get all the users
        users = self.parent.db.query().select().from_table("users").execute()

        # if no users, return
        if len(users) == 0:
            # remove the add user button
            self.add_new_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            return

        # remove the add user button
        self.add_new_user_button.place_forget()

        # populate the users
        for user in users:
            # create a button with the user name
            ctk.CTkButton(
                self.user_list,
                text=user.username,
                command=lambda user=user: self.select_user(user),
                fg_color="transparent",
                hover=False,
            ).pack(side="top", fill="x")

    def clear_children(self, parent: ctk.CTkBaseClass):
        """
        clears all the children of the parent widget

        Args:
            parent (ctk.CTkBaseClass): the parent widget

        Returns:
            None
        """
        # clear all the children
        for child in parent.winfo_children():
            child.destroy()

    def select_user(self, user):
        """
        selects the user

        Args:
            user (Record): the user to select

        Returns:
            None
        """
        # set the selected user
        self.selected = user
        # populate the user window
        self.populate_user_window()

    def populate_user_window(self):
        """
        populates the user window

        Returns:
            None
        """
        # if user is selected
        if self.selected != None:
            # remove the select user label
            self.user_window_select_label.place_forget()
            # change the user name
            self.user_name.configure(
                text=f"User Name: {self.selected.username}",
            )
            # place the user name
            self.select_user_button.configure(
                command=lambda user=self.selected: self.add_user_to_program(user)
            )
            # place the delete user button
            self.delete_user_button.configure(
                command=lambda user=self.selected: self.delete_user(user)
            )
            # place the user name
            self.user_name.place(relx=0, rely=0, relwidth=1, relheight=0.1)
            # place the select user button
            self.select_user_button.place(relx=0, rely=0.1, relwidth=0.5, relheight=0.1)
            # place the delete user button
            self.delete_user_button.place(
                relx=0.5, rely=0.1, relwidth=0.5, relheight=0.1
            )
        # if no user is selected
        else:
            # remove the user name
            self.user_name.place_forget()
            # remove the select user button
            self.select_user_button.place_forget()
            # remove the delete user button
            self.delete_user_button.place_forget()
            # place the select user label
            self.user_window_select_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def delete_user(self, user):
        """
        deletes the user

        Args:
            user (Record): the user to delete

        Returns:
            None
        """
        # delete the user
        self.parent.arduino.wait_for(["Enter choice: "])
        # write the choice
        self.parent.arduino.write("2")
        # wait for the arduino to ask for the fingerprint id
        self.parent.arduino.wait_for(
            ["Enter Id of the fingerprint that is to be deleted: "]
        )
        # write the fingerprint id
        self.parent.arduino.write(str(user.fingerprintID))
        # wait for the arduino to delete the fingerprint
        self.parent.arduino.wait_for(["Deleted!"])
        # delete the user from the program
        self.parent.db.query().delete("access").equals(
            uid=user.id, pid=self.program.id
        ).execute()
        # delete the user
        self.parent.db.query().delete("users").equals(id=user.id).execute()
        # refresh the user list
        self.populate_user_list()
        # refresh the user window
        self.parent.populate_program_window()
        # refresh the program window
        self.select_user(None)

    def add_user_to_program(self, user):
        """
        adds the user to the program

        Args:
            user (Record): the user to add

        Returns:
            None
        """
        # check if the user already has access
        user_exists = (
            self.parent.db.query()
            .select()
            .from_table("access")
            .equals(uid=user.id, pid=self.program.id)
            .execute()
        )

        # if user already has access, return
        if len(user_exists) > 0:
            log("user already has access")
            return

        # add the user to the program
        self.parent.db.query().insert(
            "access", uid=user.id, pid=self.program.id
        ).values([(user.id, self.program.id)]).execute()

        # call the callback if set
        if self.callback != None:
            self.callback()
        # refresh the user list
        self.window.destroy()

    def run(self):
        # run the window
        self.window.mainloop()


class Add_program:
    def __init__(self, parent: GUI):
        """
        Add program window

        Args:
            parent (GUI): the parent GUI

        Returns:
            None
        """
        # set the parent
        self.parent = parent
        # create a new window
        self.window = ctk.CTkToplevel(self.parent.root)
        # set the window to the top
        self.window.attributes("-topmost", True)
        # set the title
        self.window.title("Add Program")
        # set the geometry
        self.window.geometry(f"{self.parent.w//2}x{self.parent.h//2}")

        # program list window
        self.program_list_window = ctk.CTkFrame(self.window, corner_radius=0)
        # title
        self.program_list_title = ctk.CTkLabel(
            self.program_list_window, text="programs"
        )
        # program list
        self.program_list = ctk.CTkScrollableFrame(
            self.program_list_window, corner_radius=0
        )

        # place the program list window
        self.program_list_title.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        # place the program list
        self.program_list.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)
        # populate the program list
        self.program_list_window.place(relx=0, rely=0, relwidth=0.5, relheight=1)
        # populate the program list
        self.populate_program_list()

        # run the window
        self.run()

    def populate_program_list(self):
        """
        populates the program list

        Returns:
            None
        """
        # get all the programs
        active_windows = pyautogui.getAllWindows()
        # add the programs to the list
        for window in active_windows:
            # if the window has no title, skip
            if window.title:
                ctk.CTkButton(
                    self.program_list,
                    text=window.title,
                    command=lambda program=window: self.add_program(program),
                ).pack(side="top", fill="x")

    def add_program(self, program):
        """
        adds the program

        Args:
            program (Window): the program to add

        Returns:
            None
        """
        # check if the program already exists
        program_exist = (
            self.parent.db.query()
            .select()
            .from_table("programs")
            .equals(name=program.title)
            .execute()
        )
        # if program already exists, return
        if program_exist:
            log("already on list")
            return

        # add the program
        self.parent.db.query().insert("programs", name="", description="").values(
            [(program.title, "")]
        ).execute()

        # refresh the program list
        self.parent.populate_programs_window()
        # close the window
        self.window.destroy()

    def run(self):
        """
        runs the window

        Returns:
            None
        """
        # run the window
        self.window.mainloop()


class Verify_Access:
    def __init__(self, parent: GUI, target):
        """
        Verify access window

        Args:
            parent (GUI): the parent GUI
            target (Window): the target window

        Returns:
            None
        """
        log("new verification")
        # set the parent
        if target != None:
            # set the targets
            self.targets = target
            # set the target
            self.target = target[0]
            # set the parent
            self.parent = parent
            # create a new window
            self.window = ctk.CTkToplevel(self.parent.root)  # set focus to self.window
            self.window.attributes("-topmost", True)

            # on window close call self.failed
            self.window.protocol("WM_DELETE_WINDOW", self.failed)
            self.window.bind("<FocusOut>", self.failed)

            # set the title
            self.window.title("Access Verification")
            # set the geometry
            self.window.geometry(f"{parent.w//2}x{parent.h//2}")

            # set the status label
            self.status_label = ctk.CTkLabel(
                self.window,
                text="verifying! please place your finger on the sensor. you are given 10 seconds to verify identity",
            )
            # place the status label
            self.status_label.place(
                relx=0.5, rely=0.5, relheight=0.1, relwidth=1, anchor=tk.CENTER
            )
            # set the status label
            self.closed = False

            # start the verification
            self.parent.arduino.start_reading()
            # start the verification

            pyautogui.getWindowsWithTitle("Access Verification")[0].activate()
            if self.target_still_active():

                t = threading.Thread(target=timeout, args=(10, self.failed))
                t.start()
                print("thread started")
                self.verify()

    def failed(self, *x):
        """
        called when the verification fails

        Returns:
            None
        """
        # check if the window is closed
        if hasattr(self, "closed"):
            # if closed, return
            if self.closed:
                return
        # if closed is missing then there is an error so return
        else:
            return

        log("FAILED")
        log(hasattr(self, "closed"), self.closed)

        # set the status label
        self.closed = True
        # set the kill timer flag
        global kill_timer
        kill_timer[0] = True

        # stop reading from the arduino
        self.parent.arduino.stop_reading()
        # if the window is still active
        if self.target_still_active():
            # close the window
            for target in self.targets:
                target.close()
        # forget the status label
        self.status_label.place_forget()
        # destroy the label
        self.status_label.destroy()
        # destroy the window
        self.window.destroy()

    def target_still_active(self):
        """
        checks if the target window is still active

        Returns:
            bool: True if the window is still active, False otherwise
        """
        # get all the windows
        for window in pyautogui.getAllWindows():
            # if the window has no title, skip
            if window.title == "":
                continue
            # if the window title is the same as the target title
            if window.title == self.target.title:
                log(window.title, self.target.title, "still active")
                return True
        return False

    def verify(self):
        """
        verifies the access

        Returns:
            None
        """
        log("VERIFY")

        # get the checked list
        global checked, kill_timer
        # fetch program
        program = (
            self.parent.db.query()
            .select()
            .from_table("programs")
            .equals(name=self.target.title)
            .execute()[0]
        )
        # fetch users list
        users = (
            self.parent.db.query()
            .select()
            .from_table("users")
            .in_column(
                id=self.parent.db.query()
                .select(["uid"])
                .from_table("access")
                .equals(pid=program.id)
            )
            .execute()
        )

        # if no users, return
        if len(users) <= 0:
            checked.append(self.target.title)
            return

        self.parent.arduino.start_reading()
        # start the verification
        while True:
            # check if the window is closed
            if hasattr(self, "closed"):
                if self.closed:
                    return
            else:
                return
            # verify fingerprint
            self.parent.arduino.wait_for(["Enter choice: "])
            log("entering choice")
            self.parent.arduino.write("3")
            log("scan fingerprint")
            # scan fingerprint
            while True:
                read = self.parent.arduino.wait_for(["print match", "error", "a match"])
                # if a match is found, break
                if "print match" in read:
                    break
                # if the arduino stops reading, execute failure and break
                elif "stopped reading" == read:
                    log("exiting with fail")
                    self.failed()
                    break
                else:
                    log(read)
            # if the arduino stops reading, return
            if read == "stopped reading":
                return

            # get the fingerprint id
            fingerprintId = int(
                self.parent.arduino.wait_for(["found id"]).split()[-1][1::]
            )
            log("id found", fingerprintId)
            # get the confidence, how accurate the fingerprint is
            confidence = self.parent.arduino.wait_for(["confidence"]).split()[-1]
            log("confidence found")

            # check if any of the users have the fingerprint
            if any([user.fingerprintID == fingerprintId for user in users]):
                log("found user")
                break
            else:
                self.failed()
                return

        log("access granted")
        # permission is granted so add the program to checked list
        checked.append(self.target.title)
        # close the window
        kill_timer[0] = True
        self.window.destroy()


class window_watcher:
    def __init__(self, windows, callbacks=None, update=None):
        """
        window watcher

        Args:
            windows (list): the list of windows to watch
            callbacks (dict): the callbacks to call
            update (dict): the update functions to call

        Returns:
            None
        """
        # set the kill flag
        global kill
        kill = False
        # set the checked list
        self.targets = windows
        # set the thread
        self.thread = threading.Thread()
        # set the callbacks
        self.callbacks = callbacks
        # set the update
        self.windows = []
        # set the update
        self.update = update

        # start the thread
        self.thread = threading.Thread(target=self.listen_for_update)
        # start the thread
        self.thread.start()

    def listen_for_update(self):
        log("listening for updates")
        # set the kill flag
        global kill
        # lsiten for window updates
        while True:
            # if the kill flag is set, break
            if kill:
                log("KILLING THREAD")
                break
            # get all the active windows
            active_windows = pyautogui.getAllWindows()
            # check if any new windows have been opened
            if len(self.windows) < len(active_windows):
                log("windows updated")
                # if any callbacks that have to be ran on update
                if self.update:
                    # run the callbacks
                    for callback, args in self.update.items():
                        callback(**args)
                # check if any of the new windows are on the watch list
                self.check_for_window()
            # set the windows
            if active_windows != self.windows:
                self.windows = active_windows
            # set the went through list
            global went_through
            went_through.clear()

    def check_for_window(self):
        """
        checks for the window

        Returns:
            None
        """
        log("checking for window")
        global checked
        # get all the titles of the active windows
        windows = set(pyautogui.getAllTitles())
        log(windows)

        global went_through
        for title in windows:
            # if the title is empty, skip
            if title == "":
                continue
            log("running", title)
            # get the windows with the title. this is because sometimes background windows have the same title as their active process
            targets = pyautogui.getWindowsWithTitle(title)
            # if there is not such window, skip
            if len(targets) < 0:
                log(targets)
                continue
            log(targets[0], len(targets))
            # get the first window from the list of windows with the title
            window = targets[0]
            # go through the targets
            for target in self.targets:
                # if the window title does not match with the target title or is in the checked list, skip
                if window.title == target.name and window.title not in checked:
                    # try to bring window to the top. this is a test to see if it is a background process
                    try:
                        window.activate()
                        if not window.isActive:
                            log("failed to activate", window.title)
                            break
                    except:
                        log("failed to activate", window.title)
                        break
                    # if the callback is set
                    if self.callbacks:
                        # run the callback
                        for callback, args in self.callbacks.items():
                            if isinstance(callback(**args), Verify_Access):
                                callback(args["parent"], targets)
                else:
                    log(window.title, "not target")


if __name__ == "__main__":
    gui = GUI()
    gui.run()
