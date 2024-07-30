# 3rd part modules
import tkinter as tk

import customtkinter as ctk

from arduino import Arduino

# Local modules
from db import DB


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

        # program list window
        self.program_list_window = ctk.CTkFrame(self.root, corner_radius=0)
        self.program_list_window_top_bar = ctk.CTkFrame(self.program_list_window)
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
            self.program_list_window, height=self.h
        )

        self.populate_programs_window()

        # program window
        self.selected = None
        self.program_window = ctk.CTkFrame(self.root, height=self.h, corner_radius=0)

        self.select_program_label = ctk.CTkLabel(
            self.program_window, text="Select Program"
        )

        # program info window
        self.program_info = ctk.CTkFrame(self.program_window)
        self.program_name = ctk.CTkLabel(
            self.program_info,
            text=f"Program Name: {self.selected.name if self.selected else ''}",
        )
        self.program_name.pack()

        # program users window
        self.program_users_frame = ctk.CTkFrame(self.program_window)
        top_heading = ctk.CTkFrame(self.program_users_frame)
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
        self.program_users = ctk.CTkScrollableFrame(self.program_users_frame)

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

    def run(self):
        self.root.mainloop()

    def clear_children(self, parent: ctk.CTkBaseClass):
        for child in parent.winfo_children():
            child.destroy()

    def populate_programs_window(self):
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
            container = ctk.CTkFrame(self.program_list)
            # place container with fill x and auto y
            container.pack(fill="x")
            # buttons with the same height as the container
            # select button 80% width
            ctk.CTkButton(
                container,
                text=program.name,
                command=lambda program=program: self.select_program(program),
            ).pack(side="left", fill="x", expand=True)
            # delete button 20% width
            ctk.CTkButton(
                container,
                text="Delete",
                command=lambda program=program: self.delete_program(program),
            ).pack(side="right", fill="x", expand=True)
            # place the buttons

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
                .equals(
                    id=f'({self.db.query().select(["uid"]).from_table("access").equals(pid=self.selected.id).__str__()})'
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
                userFrame = ctk.CTkFrame(self.program_users)
                ctk.CTkLabel(userFrame, text=user.username).place(
                    relx=0, rely=0, relwidth=0.8
                )
                ctk.CTkButton(
                    userFrame,
                    text="Delete",
                    command=lambda user=user: self.delete_user_from_program(user),
                ).place(relx=0.8, rely=0.075, relwidth=0.2, anchor=tk.CENTER)
                userFrame.pack(fill="x")
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
        self.db.query().insert("programs", name="", description="").values(
            [["test", "this is a test program"]]
        ).execute()
        if len(self.program_list.winfo_children()) > 0:
            self.clear_children(self.program_list)
        self.populate_programs_window()

    def add_user(self, program):
        Add_user_to_program_window(self, program, self.populate_program_window)


class Add_User_Window:
    def __init__(self, parent, callback=None):
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

        self.run()

    def add_user(self):
        self.parent.db.query().insert(
            "users",
            username=self.user_name_entry.get(),
            fingerprintID=self.fingerprint_entry.get(),
        ).values([(self.user_name_entry.get(), self.fingerprint_entry.get())]).execute()
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

        self.selected = None
        self.user_list_window = ctk.CTkFrame(self.window)
        self.user_list_title = ctk.CTkLabel(self.user_list_window, text="Users")
        self.user_list = ctk.CTkScrollableFrame(self.user_list_window)

        self.add_new_user_button = ctk.CTkButton(
            self.user_list_window, text="Add new user", command=self.add_new_user
        )

        self.user_list_title.place(relx=0, rely=0, relwidth=1, relheight=0.1)
        self.user_list.place(relx=0, rely=0.1, relwidth=1, relheight=0.9)

        self.user_window = ctk.CTkFrame(self.window)
        self.user_name = ctk.CTkLabel(
            self.user_window,
            text=f"User Name: {self.selected.username if self.selected else ''}",
        )
        self.select_user_button = ctk.CTkButton(
            self.user_window,
            text="Select User",
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
                command=lambda user=user: self.add_user_to_program(user),
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
                command=lambda: self.add_user_to_program(self.selected)
            )

            self.select_user_button.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

            self.user_name.pack()
        else:
            self.user_name.place_forget()
            self.user_window_select_label.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

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


if __name__ == "__main__":
    gui = GUI()
    gui.run()
