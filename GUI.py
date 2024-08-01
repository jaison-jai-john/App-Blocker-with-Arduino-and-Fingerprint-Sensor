# 3rd part modules
import threading

# built in modules
import time
import tkinter as tk

import customtkinter as ctk
import pyautogui

from arduino import Arduino

# Local modules
from db import DB
from variables import checked, kill, reading

went_through = []
kill_timer = False


def timeout(sec, callback):
    global kill_timer
    kill_timer = False
    for i in range(sec)[::-1]:
        if kill_timer:
            return
        print(i)
        time.sleep(1)
    callback()


class GUI:
    def __init__(self):
        # connect to the database
        self.db = DB("root", "jan04198", log=True)

        # create the database
        self.db.create_database("program_manager")
        self.db.use("program_manager")

        # create the tables
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

        self.arduino = Arduino("COM12", 9600)

        # create the root window+
        self.root = tk.Tk()
        self.root.title("Custom Tkinter")
        self.root.geometry("1920x1080")
        self.w = 1920
        self.h = 1080
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        # program list window
        self.program_list_window = ctk.CTkFrame(self.root, corner_radius=0)
        self.program_list_window_top_bar = ctk.CTkFrame(
            self.program_list_window, corner_radius=0
        )
        self.program_list_title = ctk.CTkLabel(
            self.program_list_window_top_bar, text="Programs"
        )
        self.program_list_title.place(relx=0, rely=0, relwidth=0.8, relheight=1)
        ctk.CTkButton(
            self.program_list_window_top_bar,
            text="Add Program",
            command=self.add_program,
        ).place(relx=0.8, rely=0.5, relwidth=0.2, anchor=tk.CENTER)
        self.program_list_window_top_bar.place(
            relx=0, rely=0, relwidth=1, relheight=0.1
        )

        # add program button
        self.add_program_button = ctk.CTkButton(
            self.program_list_window,
            text="Add Program",
            command=self.add_program,
        )

        # program list
        self.program_list = ctk.CTkScrollableFrame(
            self.program_list_window, height=self.h, corner_radius=0
        )

        self.populate_programs_window()

        # program window
        self.selected = None
        self.program_window = ctk.CTkFrame(self.root, height=self.h, corner_radius=0)

        self.select_program_label = ctk.CTkLabel(
            self.program_window, text="Select Program"
        )

        # program info window
        self.program_info = ctk.CTkFrame(self.program_window, corner_radius=0)
        self.program_name = ctk.CTkLabel(
            self.program_info,
            text=f"Program Name: {self.selected.name if self.selected else ''}",
        )
        self.program_name.place(
            relx=0.5, rely=0.5, relwidth=1, relheight=0.1, anchor=tk.CENTER
        )

        # program users window
        self.program_users_frame = ctk.CTkFrame(self.program_window, corner_radius=0)
        top_heading = ctk.CTkFrame(self.program_users_frame, corner_radius=0)
        top_heading.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        ctk.CTkLabel(top_heading, text="Users").place(
            relx=0, rely=0, relwidth=0.8, relheight=1
        )
        self.add_user_top_button = ctk.CTkButton(
            top_heading,
            text="Add User",
        )
        self.add_user_top_button.place(
            relx=0.8, rely=0.5, relwidth=0.2, anchor=tk.CENTER
        )
        self.program_users = ctk.CTkScrollableFrame(
            self.program_users_frame, corner_radius=0
        )

        # add user button
        self.add_user_button = ctk.CTkButton(
            self.program_users_frame,
            text="Add User",
        )

        # populate the program window
        self.populate_program_window()

        # pack the frames
        self.program_list_window.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        self.program_window.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)

        self.run()

    def run(self):
        self.root.mainloop()

    def clear_children(self, parent: ctk.CTkBaseClass):
        for child in parent.winfo_children():
            child.destroy()

    def populate_programs_window(self):
        global kill
        kill = True
        # get all the programs
        programs = self.db.query().select().from_table("programs").execute()

        # if no programs, return
        if len(programs) == 0:
            self.program_list.place_forget()
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

        self.watcher = window_watcher(
            self.db.query().select().from_table("programs").execute(),
            callbacks={Verify_Access: {"parent": self, "target": None}},
        )

    def select_program(self, program):
        self.selected = program
        self.populate_program_window()

    def populate_program_window(self):
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

            self.add_user_top_button.configure(
                command=lambda program=self.selected: self.add_user(program)
            )

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

            if len(users) == 0:
                self.program_users.place_forget()
                self.add_user_button.configure(
                    command=lambda program=self.selected: self.add_user(program)
                )
                self.add_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
                return

            self.add_user_button.place_forget()

            for user in users:
                userFrame = ctk.CTkFrame(self.program_users, corner_radius=0)
                userFrame.pack(fill="x")
                ctk.CTkButton(
                    userFrame,
                    text=user.username,
                    command=lambda user=user: self.delete_user_from_program(user),
                    fg_color="transparent",
                    hover=False,
                ).pack(side="left", fill="x", expand=True)
                ctk.CTkButton(
                    userFrame,
                    text="Delete",
                    command=lambda user=user: self.delete_user_from_program(user),
                ).pack(side="right", fill="x", expand=True)
        else:
            self.program_info.place_forget()
            self.program_users_frame.place_forget()
            self.select_program_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def delete_user_from_program(self, user):
        self.db.query().delete("access").equals(
            uid=user.id, pid=self.selected.id
        ).execute()
        self.populate_program_window()

    def delete_program(self, program):
        program_id = program.id
        self.db.query().delete("access").equals(pid=program_id).execute()
        self.db.query().delete("programs").equals(id=program_id).execute()

        if self.selected:
            if self.selected.id == program_id:
                self.selected = None
                self.populate_program_window()

        self.clear_children(self.program_list)
        self.populate_programs_window()

    def add_program(self):
        Add_program(self)

    def add_user(self, program):
        Add_user_to_program_window(self, program, self.populate_program_window)

    def on_close(self):
        global kill
        kill = True
        self.root.destroy()
        exit()


class Add_User_Window:
    def __init__(self, parent: GUI, callback=None):
        self.parent = parent
        self.window = ctk.CTkToplevel(self.parent.root)
        self.window.attributes("-topmost", True)
        self.window.title("Add User")
        self.window.geometry(f"{self.parent.w//2}x{self.parent.h//2}")

        self.callback = callback

        self.user_name_label = ctk.CTkLabel(self.window, text="User Name")
        self.user_name_entry = ctk.CTkEntry(self.window)

        self.fingerprint_label = ctk.CTkLabel(self.window, text="Fingerprint ID")
        self.fingerprint_entry = ctk.CTkEntry(self.window)

        self.add_user_button = ctk.CTkButton(
            self.window, text="Add User", command=self.add_user
        )

        self.user_name_label.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        self.user_name_entry.place(relx=0, rely=0.1, relwidth=1, relheight=0.1)

        self.fingerprint_label.place(relx=0, rely=0.2, relwidth=1, relheight=0.1)
        self.fingerprint_entry.place(relx=0, rely=0.3, relwidth=1, relheight=0.1)

        self.add_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.message_label = ctk.CTkLabel(self.window, text="")
        self.message_label.place(relx=0.5, rely=0.6, anchor=tk.CENTER)

        self.run()

    def add_user(self):
        if self.user_name_entry.get() == "" or self.user_name_entry.get() == None:
            self.message_label.configure(text="User name is required")
            return
        if self.fingerprint_entry.get() == "" or self.fingerprint_entry.get() == None:
            self.message_label.configure(text="Fingerprint ID is required")
            return
        if not self.fingerprint_entry.get().isdigit():
            self.message_label.configure(text="Fingerprint ID must be a number")
            return
        if (
            int(self.fingerprint_entry.get()) < 1
            or int(self.fingerprint_entry.get()) > 127
        ):
            self.message_label.configure(
                text="Fingerprint ID must be between 1 and 127"
            )
            return
        if (
            self.parent.db.query()
            .select()
            .from_table("users")
            .equals(username=self.user_name_entry.get())
            .execute()
        ):
            self.message_label.configure(text="User name already exists")
            return
        if (
            self.parent.db.query()
            .select()
            .from_table("users")
            .equals(fingerprintID=self.fingerprint_entry.get())
            .execute()
        ):
            self.message_label.configure(text="Fingerprint ID already exists")
            return

        self.parent.arduino.start_reading()
        self.parent.arduino.wait_for(["Enter choice: "])
        self.parent.arduino.write("1")
        self.parent.arduino.wait_for(["Enter finger print id from 1 to 127"])
        self.parent.arduino.write(self.fingerprint_entry.get())
        while True:
            read = self.parent.arduino.wait_for(
                ["place finger", "remove finger", "stored!"]
            )
            if "stored!" in read:
                break
            if "place finger" in read:
                self.message_label.configure(text="Place finger")
            if "remove finger" in read:
                self.message_label.configure(text="Remove finger")

        self.parent.db.query().insert(
            "users",
            username=self.user_name_entry.get(),
            fingerprintID=self.fingerprint_entry.get(),
        ).values(
            [(self.user_name_entry.get(), int(self.fingerprint_entry.get()))]
        ).execute()
        if self.callback != None:
            self.callback()
        self.window.destroy()

    def run(self):
        self.window.mainloop()


class Add_user_to_program_window:
    def __init__(self, parent: GUI, program, callback=None):
        self.callback = callback
        self.parent = parent
        self.window = ctk.CTkToplevel(self.parent.root)
        self.window.attributes("-topmost", True)
        self.window.title("Add User")
        self.window.geometry(f"{self.parent.w//2}x{self.parent.h//2}")

        self.program = program

        # user list window
        self.selected = None
        self.user_list_window = ctk.CTkFrame(self.window, corner_radius=0)
        user_list_window_top_bar = ctk.CTkFrame(self.user_list_window, corner_radius=0)
        user_list_title = ctk.CTkLabel(user_list_window_top_bar, text="Users")
        add_user_button = ctk.CTkButton(
            user_list_window_top_bar, text="Add User", command=self.add_new_user
        )
        self.user_list = ctk.CTkScrollableFrame(self.user_list_window, corner_radius=0)

        self.add_new_user_button = ctk.CTkButton(
            self.user_list_window, text="Add new user", command=self.add_new_user
        )
        user_list_window_top_bar.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        user_list_title.place(relx=0, rely=0, relwidth=0.8, relheight=1)
        add_user_button.place(relx=0.8, rely=0.5, relwidth=0.2, anchor=tk.CENTER)
        self.user_list.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        # user window
        self.user_window = ctk.CTkFrame(self.window, corner_radius=0)
        self.user_name = ctk.CTkLabel(
            self.user_window,
            text=f"User Name: {self.selected.username if self.selected else ''}",
        )
        self.select_user_button = ctk.CTkButton(
            self.user_window,
            text="Select User",
        )
        self.delete_user_button = ctk.CTkButton(
            self.user_window,
            text="Delete User",
        )

        # if not selected
        self.user_window_select_label = ctk.CTkLabel(
            self.user_window, text="Select User"
        )
        self.user_window_select_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        self.populate_user_list()

        self.user_list_window.place(relx=0, rely=0, relwidth=0.4, relheight=1)
        self.user_window.place(relx=0.4, rely=0, relwidth=0.6, relheight=1)

        self.run()

    def add_new_user(self):
        self.window.attributes("-topmost", False)
        Add_User_Window(self.parent, self.populate_user_list)

    def populate_user_list(self):
        self.clear_children(self.user_list)

        users = self.parent.db.query().select().from_table("users").execute()

        if len(users) == 0:
            self.add_new_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
            return

        self.add_new_user_button.place_forget()

        for user in users:
            ctk.CTkButton(
                self.user_list,
                text=user.username,
                command=lambda user=user: self.select_user(user),
                fg_color="transparent",
                hover=False,
            ).pack(side="top", fill="x")

    def clear_children(self, parent: ctk.CTkBaseClass):
        for child in parent.winfo_children():
            child.destroy()

    def select_user(self, user):
        self.selected = user
        self.populate_user_window()

    def populate_user_window(self):
        if self.selected != None:
            self.user_window_select_label.place_forget()
            self.user_name.configure(
                text=f"User Name: {self.selected.username}",
            )
            self.select_user_button.configure(
                command=lambda user=self.selected: self.add_user_to_program(user)
            )
            self.delete_user_button.configure(
                command=lambda user=self.selected: self.delete_user(user)
            )
            self.user_name.place(relx=0, rely=0, relwidth=1, relheight=0.1)
            self.select_user_button.place(relx=0, rely=0.1, relwidth=0.5, relheight=0.1)
            self.delete_user_button.place(
                relx=0.5, rely=0.1, relwidth=0.5, relheight=0.1
            )
        else:
            self.user_name.place_forget()
            self.select_user_button.place_forget()
            self.delete_user_button.place_forget()
            self.user_window_select_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    def delete_user(self, user):
        self.parent.arduino.wait_for(["Enter choice: "])
        self.parent.arduino.write("2")
        self.parent.arduino.wait_for(
            ["Enter Id of the fingerprint that is to be deleted: "]
        )
        self.parent.arduino.write(str(user.fingerprintID))
        self.parent.arduino.wait_for(["Deleted!"])
        self.parent.db.query().delete("access").equals(
            uid=user.id, pid=self.program.id
        ).execute()
        self.parent.db.query().delete("users").equals(id=user.id).execute()
        self.populate_user_list()
        self.parent.populate_program_window()
        self.select_user(None)

    def add_user_to_program(self, user):
        user_exists = (
            self.parent.db.query()
            .select()
            .from_table("access")
            .equals(uid=user.id, pid=self.program.id)
            .execute()
        )
        if len(user_exists) > 0:
            print("user already has access")
            return
        self.parent.db.query().insert(
            "access", uid=user.id, pid=self.program.id
        ).values([(user.id, self.program.id)]).execute()
        if self.callback != None:
            self.callback()
        self.window.destroy()

    def run(self):
        self.window.mainloop()


class Add_program:
    def __init__(self, parent: GUI):
        self.parent = parent
        self.window = ctk.CTkToplevel(self.parent.root)
        self.window.attributes("-topmost", True)
        self.window.title("Add Program")
        self.window.geometry(f"{self.parent.w//2}x{self.parent.h//2}")

        # program list window
        self.program_list_window = ctk.CTkFrame(self.window, corner_radius=0)
        self.program_list_title = ctk.CTkLabel(
            self.program_list_window, text="programs"
        )
        self.program_list = ctk.CTkScrollableFrame(
            self.program_list_window, corner_radius=0
        )

        self.program_list_title.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        self.program_list.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        self.program_list_window.place(relx=0, rely=0, relwidth=0.5, relheight=1)

        self.populate_program_list()
        # program window

        self.run()

    def populate_program_list(self):
        active_windows = pyautogui.getAllWindows()
        for window in active_windows:
            if window.title:
                ctk.CTkButton(
                    self.program_list,
                    text=window.title,
                    command=lambda program=window: self.add_program(program),
                ).pack(side="top", fill="x")

    def add_program(self, program):
        program_exist = (
            self.parent.db.query()
            .select()
            .from_table("programs")
            .equals(name=program.title)
            .execute()
        )
        if program_exist:
            print("already on list")
            return

        self.parent.db.query().insert("programs", name="", description="").values(
            [(program.title, "")]
        ).execute()

        self.parent.populate_programs_window()
        self.window.destroy()

    def run(self):
        self.window.mainloop()


class Verify_Access:
    def __init__(self, parent: GUI, target):
        print("new verification")
        if target != None:
            self.targets = target
            self.target = target[0]
            self.parent = parent
            self.window = ctk.CTkToplevel(self.parent.root)  # set focus to self.window
            # self.window.attributes("-topmost", True)

            # on window close call self.failed
            self.window.protocol("WM_DELETE_WINDOW", self.failed)
            # self.window.bind("<FocusOut>", self.failed)
            self.window.title("Access Verification")
            self.window.geometry(f"{parent.w//2}x{parent.h//2}")

            self.status_label = ctk.CTkLabel(
                self.window,
                text="verifying! please place your finger on the sensor. you are given 10 seconds to verify identity",
            )
            self.status_label.place(
                relx=0.5, rely=0.5, relheight=0.1, relwidth=0.3, anchor=tk.CENTER
            )
            self.closed = False

            self.parent.arduino.start_reading()
            if self.target_still_active():
                threading.Thread(target=timeout(10, self.failed)).start()
                self.verify()

    def failed(self, *x):
        if hasattr(self, "closed"):
            if self.closed:
                return
        else:
            return
        print("FAILED")
        print(hasattr(self, "closed"), self.closed)
        self.closed = True
        global kill_timer
        kill_timer = True
        self.parent.arduino.stop_reading()
        if self.target_still_active():
            for target in self.targets:
                target.close()
        self.status_label.place_forget()
        self.status_label.destroy()
        self.window.destroy()

    def target_still_active(self):
        for window in pyautogui.getAllWindows():
            if window.title == "":
                continue
            if window.title == self.target.title:
                print(window.title, self.target.title, "still active")
                return True
        return False

    def verify(self):
        print("VERIFY")
        global checked
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

        if len(users) <= 0:
            checked.append(self.target.title)
            return

        while True:
            if hasattr(self, "closed"):
                if self.closed:
                    return
            else:
                return
            # verify fingerprint
            self.parent.arduino.wait_for(["Enter choice: "])
            print("entering choice")
            self.parent.arduino.write("3")
            print("scan fingerprint")
            while True:
                read = self.parent.arduino.wait_for(["print match", "error", "a match"])
                if "print match" in read:
                    break
                elif "stopped reading" == read:
                    print("exiting with fail")
                    self.failed()
                    break
                else:
                    print(read)
            if read == "stopped reading":
                return

            fingerprintId = int(
                self.parent.arduino.wait_for(["found id"]).split()[-1][1::]
            )
            print("id found", fingerprintId)
            confidence = self.parent.arduino.wait_for(["confidence"]).split()[-1]
            print("confidence found")

            # check if any of the users have the fingerprint
            if any([user.fingerprintID == fingerprintId for user in users]):
                print("found user")
                break
            else:
                self.failed()
                return

        print("access granted")
        checked.append(self.target.title)
        self.window.destroy()


class window_watcher:
    def __init__(self, windows, callbacks=None, update=None):
        global kill
        kill = False
        self.targets = windows
        self.thread = threading.Thread()
        self.callbacks = callbacks
        self.windows = []
        self.update = update

        self.thread = threading.Thread(target=self.listen_for_update)
        self.thread.start()

    def listen_for_update(self):
        print("listening for updates")
        global kill
        while True:
            if kill:
                print("KILLING THREAD")
                break
            active_windows = pyautogui.getAllWindows()
            if self.windows != active_windows:
                print("windows updated")
                if self.update:
                    for callback, args in self.update.items():
                        callback(**args)
                self.check_for_window()
                self.windows = active_windows
            global went_through
            went_through.clear()

    def check_for_window(self):
        print("checking for window")
        global checked
        windows = set(pyautogui.getAllTitles())
        print(windows)

        global went_through
        for title in windows:
            if title == "":
                continue
            print("running", title)
            targets = pyautogui.getWindowsWithTitle(title)
            if len(targets) < 0:
                print(targets)
                continue
            print(targets[0], len(targets))
            window = targets[0]
            for target in self.targets:
                if window.title == target.name and window.title not in checked:
                    try:
                        window.activate()
                        if not window.isActive:
                            print("failed to activate", window.title)
                            break
                    except:
                        print("failed to activate", window.title)
                        break
                    last_title = window.title
                    if self.callbacks:
                        for callback, args in self.callbacks.items():
                            if isinstance(callback(**args), Verify_Access):
                                callback(args["parent"], targets)
                else:
                    print(window.title, "not target")


if __name__ == "__main__":
    gui = GUI()
    gui.run()
