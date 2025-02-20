import math
import tkinter as tk
from tkinter import messagebox
import threading


class ChatUI:
    """
    Handles the user interface for the chat application.
    """

    def __init__(self, root, client):
        """
        Initialize the user interface.

        :param root: The Tkinter root window
        :param client: The ChatClient instance
        """
        self.root = root
        self.client = client

        # Keep track of current pages for list accounts and messages
        self.current_user_page = 0
        self.current_msg_page = 0

        self.all_users = []
        self.all_messages = []

        self.unread_count = 0

        self.prev_search = ""  # Store previous search text for user list

        # Set callback
        self.client.set_message_update_callback(self.message_callback)

        # Start on the login screen
        self.root.title("Login")
        self.create_login_screen()

    ### LOGIN + ACCOUNT CREATION WORKFLOW ###
    def create_login_screen(self):
        """
        Create the login screen.
        """
        self.clear_window()

        # Add padding around the frame
        frame = tk.Frame(self.root, padx=10, pady=20)
        frame.pack(expand=True)

        tk.Label(frame, text="Enter Username:").pack(pady=5)
        self.username_entry = tk.Entry(frame)
        self.username_entry.pack(padx=10, pady=5, fill=tk.X)

        # Explicitly set focus to the username entry field
        self.username_entry.focus_set()

        self.check_button = tk.Button(
            frame, text="Continue", command=self.check_username)
        self.check_button.pack(pady=10)

        # Bind the Enter key to trigger the Continue button
        self.username_entry.bind(
            "<Return>", lambda event: self.check_button.invoke())

    def check_username(self):
        """
        Checks if the username exists and prompts for the next step.
        """
        username = self.username_entry.get().strip()

        if not username:
            messagebox.showerror("Error", "Username cannot be empty.")
            return

        # Run lookup in a background thread
        threading.Thread(target=self.lookup_username_async,
                         args=(username,), daemon=True).start()

    def lookup_username_async(self, username):
        """
        Look up the username in a background thread to see if it exists.

        :param username: The username to look up
        """
        exists = self.client.account_lookup(username)
        self.root.after(0, lambda: self.handle_lookup_result(exists))

    def handle_lookup_result(self, lookup_result):
        """
        Handle the result of the username lookup.

        :param lookup_result: Whether the username exists
        """
        username = self.username_entry.get().strip()
        self.prompt_password(username, login=lookup_result)

    def prompt_password(self, username, login=True):
        """
        Prompts for a password after username check.

        :param username: The username to log in or create an account for
        :param login: Whether to log in (True) or create an account (False)
        """
        self.clear_window()

        frame = tk.Frame(self.root, padx=10, pady=20)
        frame.pack(expand=True)

        action_text = "Login" if login else "Create Account"
        tk.Label(frame, text=f"Enter Password to {action_text}:").pack(pady=5)

        self.password_entry = tk.Entry(frame, show="*")
        self.password_entry.pack(padx=10, pady=5, fill=tk.X)

        # Explicitly set focus to the password entry field
        self.password_entry.focus_set()

        confirm_button = tk.Button(
            frame,
            text=action_text,
            command=lambda: self.process_credentials(username, login)
        )
        confirm_button.pack(pady=10)

        # Bind the Enter key to trigger the Login/Create button
        self.password_entry.bind(
            "<Return>", lambda event: confirm_button.invoke())

    def process_credentials(self, username, login):
        """
        Processes login or account creation based on user input.

        :param username: The username to log in or create an account for
        :param login: Whether to log in (True) or create an account (False)
        """
        password = self.password_entry.get().strip()

        if not password:
            messagebox.showerror("Error", "Password cannot be empty.")
            return

        # Run login or account creation in a background thread
        threading.Thread(target=self.handle_credentials, args=(
            username, password, login), daemon=True).start()

    def handle_credentials(self, username, password, login):
        """
        Handles login or account creation in a background thread.

        :param username: The username to log in or create an account for
        :param password: The password to use
        :param login: Whether to log in (True) or create an account (False)
        """
        if login:
            # Log in to the existing account
            print("[DEBUG] Logging in")
            # see if response is tuple
            response = self.client.login(username, password)
            if isinstance(response, tuple):
                success, unread_count = response
            else:
                success = response
                unread_count = 0
            self.root.after(0, lambda: self.handle_login_result(
                success, unread_count))
        else:
            # Create a new account
            print("[DEBUG] Creating account")
            success = self.client.create_account(username, password)
            self.root.after(
                0, lambda: self.handle_account_creation_result(success))

    def handle_login_result(self, success, unread_count):
        """
        Handle UI update after login.

        :param success: Whether the login was successful
        :param unread_count: The number of unread messages
        """
        if success:
            self.unread_count = unread_count
            messagebox.showinfo("Login Successful",
                                f"You have {unread_count} unread messages.")
            print("[DEBUG] Calling create_chat")
            self.create_chat_screen()
        else:
            messagebox.showerror(
                "Login Failed", "Invalid username or password. Please try again.")

    def handle_account_creation_result(self, success):
        """
        Handle UI update after account creation.

        :param success: Whether the account creation was successful
        """
        if success:
            messagebox.showinfo("Account Created",
                                "Account successfully created! Logging in...")
            print("[DEBUG] Calling create_chat")
            self.create_chat_screen()
        else:
            messagebox.showerror(
                "Error", "Failed to create an account. Please try again.")

    ### CHAT SCREEN WORKFLOW ###
    def create_chat_screen(self):
        """
        Create the main chat screen.
        """
        print("[DEBUG] In create_chat")
        self.clear_window()
        self.root.title("Chat")
        self.root.geometry("900x500")  # Larger window

        # Ensure grid layout is configured to allow resizing
        self.root.rowconfigure(1, weight=1)  # Expandable row for main chat UI
        self.root.columnconfigure(0, weight=1)  # Sidebar
        self.root.columnconfigure(1, weight=3)  # Chat window takes more space

        # Settings Toolbar (At the Top)
        settings_frame = tk.Frame(
            self.root, relief=tk.RAISED, bd=2, padx=5, pady=5)
        settings_frame.grid(row=0, column=0, columnspan=2, sticky="we")

        tk.Button(settings_frame, text="Log out", fg="red",
                  command=self.disconnect).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(settings_frame, text="Delete Account", fg="red",
                  command=self.confirm_delete_account).pack(side=tk.RIGHT, padx=5, pady=5)

        # Container to hold both sidebar and chat frame
        container = tk.Frame(self.root)
        container.grid(row=1, column=0, columnspan=2, sticky="nswe")

        container.columnconfigure(0, weight=1)  # Sidebar takes space
        container.columnconfigure(1, weight=3)  # Chat window expands more
        container.rowconfigure(0, weight=1)  # Make sure it expands

        # Sidebar for user list
        self.sidebar = tk.Frame(container, width=250, relief=tk.SUNKEN, bd=2)
        self.sidebar.grid(row=0, column=0, sticky="nswe")

        tk.Label(self.sidebar, text="Users:").pack(pady=5)
        self.user_listbox = tk.Listbox(
            self.sidebar, height=self.client.max_users)
        self.user_listbox.pack(fill=tk.BOTH, expand=True)
        self.user_listbox.bind("<Double-1>", self.fill_recipient)

        # Create a frame to hold the input and button side by side
        search_frame = tk.Frame(self.sidebar)
        search_frame.pack(fill=tk.X, padx=5, pady=5)

        # Search input field
        self.user_search = tk.Entry(search_frame)
        self.user_search.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Search button
        tk.Button(search_frame, text="Search",
                  command=self.load_user_list).pack(side=tk.LEFT, padx=5)

        # User pagination controls
        self.user_pagination_frame = tk.Frame(self.sidebar)
        self.user_pagination_frame.pack()
        self.prev_user_button = tk.Button(
            self.user_pagination_frame, text="Prev Page", command=lambda: self.change_user_page(-1))
        self.prev_user_button.pack(side=tk.LEFT, pady=5)
        self.next_user_button = tk.Button(
            self.user_pagination_frame, text="Next Page", command=lambda: self.change_user_page(1))
        self.next_user_button.pack(side=tk.RIGHT, pady=5)

        # Chat frame
        self.chat_frame = tk.Frame(container)
        self.chat_frame.grid(row=0, column=1, sticky="nswe")

        tk.Label(self.chat_frame, text="Messages:").pack(pady=0)
        self.chat_display = tk.Listbox(
            self.chat_frame, height=self.client.max_msg, selectmode=tk.MULTIPLE)
        self.chat_display.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Ensure chat_display gets focus so buttons are immediately clickable
        self.chat_display.focus_set()

        # Frame to align pagination buttons (left) and delete button (right)
        self.button_container = tk.Frame(self.chat_frame)
        # Full width to align buttons
        self.button_container.pack(fill=tk.X, pady=5, padx=10)

        # Message pagination controls (LEFT side)
        self.pagination_frame = tk.Frame(self.button_container)
        self.pagination_frame.pack(side=tk.LEFT)

        self.prev_msg_button = tk.Button(self.pagination_frame, text="Older Messages",
                                         command=lambda: self.change_msg_page(
                                             -1),
                                         state=tk.DISABLED)
        self.prev_msg_button.pack(side=tk.LEFT, padx=5)

        self.next_msg_button = tk.Button(self.pagination_frame, text="Newer Messages",
                                         command=lambda: self.change_msg_page(
                                             1),
                                         state=tk.NORMAL if len(self.all_messages) > self.unread_count else tk.DISABLED)
        self.next_msg_button.pack(side=tk.LEFT, padx=5)

        # "Delete Selected" button (RIGHT side)
        self.delete_msg_button = tk.Button(self.button_container, fg="red", text="Delete Selected",
                                           command=self.delete_selected_messages,
                                           state=tk.DISABLED)
        self.delete_msg_button.pack(side=tk.RIGHT)

        # "New Message" button
        tk.Button(self.chat_frame, text="New Message",
                  command=self.open_new_message_window).pack(pady=10)

        self.root.bind("<Configure>", self.on_resize)  # Bind resize event

        self.load_user_list()
        self.root.after(0, lambda: self.update_messages([]))  # Load messages

    def on_resize(self, event=None):
        """
        Adjust message width based on window size.
        """
        if hasattr(self, "chat_display"):
            # Adjust based on padding/margins
            new_width = self.chat_display.winfo_width() - 60
            self.message_wrap_length = max(
                new_width, 200)  # Ensure a minimum width
            print(
                f"[DEBUG] Resizing message wrap length to {self.message_wrap_length}")

            # Throttle frequent updates using `after()`
            if hasattr(self, "resize_after_id"):
                self.root.after_cancel(self.resize_after_id)

            self.resize_after_id = self.root.after(
                0, self.update_message_widths)

    def update_message_widths(self):
        """
        Update the wrap length of existing message labels without reloading messages.
        """
        for frame in self.chat_display.winfo_children():
            for widget in frame.winfo_children():
                if isinstance(widget, tk.Label):
                    widget.config(wraplength=self.message_wrap_length)

    ### LIST ACCOUNTS WORKFLOW ###
    def load_user_list(self, reset_pages=True):
        """
        Start a thread to fetch and display users.

        :param reset_pages: Whether to reset the current page to 0
        """
        if reset_pages:
            self.current_user_page = 0  # Reset to first page when loading users
        threading.Thread(target=self.fetch_users, daemon=True).start()

    def fetch_users(self):
        """
        Fetch user list in a background thread.
        """
        search_text = self.user_search.get().strip()

        if search_text != self.prev_search:
            self.prev_search = search_text
            self.client.last_offset_account_id = 0  # Reset offset when search text changes
            self.all_users = []  # Clear existing users
        else:  # If search text is the same, increment offset to last user ID
            self.client.last_offset_account_id = self.all_users[-1][0] if self.all_users else 0

        print(f"[DEBUG] Fetching users with search text: {search_text}")
        users = self.client.list_accounts(search_text)
        self.root.after(0, lambda: self.handle_user_results(users))

    def handle_user_results(self, users):
        """
        Handle the results of a list accounts request.

        :param users: The list of users to display
        """
        if len(users) == 0:
            # show message that no users found
            messagebox.showinfo("No Users Found", "No more users to load.")
            return
        # Else increment current page if needed
        if len(self.all_users) > 0:
            self.current_user_page += 1
        # Then update the user list UI
        self.update_user_list(users)

    def update_user_list(self, users):
        """
        Update the user list UI.

        :param users: The list of users to display
        """
        self.all_users += users  # Append to existing list
        current_user = self.client.username

        print("[DEBUG] Current user:", current_user)

        self.user_listbox.delete(0, tk.END)

        if not self.all_users:
            self.user_listbox.insert(tk.END, "No users found.")
            return

        visible_users = self.all_users[self.current_user_page * self.client.max_users:(
            self.current_user_page + 1) * self.client.max_users]

        for i, (_, username) in enumerate(visible_users):
            self.user_listbox.insert(
                tk.END, username + (" (you)" if current_user == username else ""))
            if username == current_user:
                self.user_listbox.itemconfig(
                    i, {'bg': 'lightgray'})  # Highlight current user

        # Update pagination buttons
        self.prev_user_button.config(
            state=tk.NORMAL if self.current_user_page > 0 else tk.DISABLED)

        # Next button is always enabled to allow users to load more accounts

        # Force focus back to user list
        self.user_listbox.focus_set()

    def change_user_page(self, direction):
        """
        Paginate through user list.

        :param direction: The direction to move in the user list
        """
        new_page = self.current_user_page + direction
        if new_page < 0:
            return

        # Calculate total pages
        total_pages = math.ceil(len(self.all_users) / self.client.max_users)
        if new_page >= total_pages:
            # request more users
            self.load_user_list(reset_pages=False)
            return

        self.current_user_page = new_page  # Update current page
        print(f"Changing user page to {self.current_user_page}")
        self.update_user_list([])

    ### MESSAGES WORKFLOW ###
    def message_callback(self, messages):
        """
        Callback to update messages when new messages are received.

        :param messages: The list of messages to display
        """
        print("[DEBUG] Got new messages")
        self.root.after(0, lambda: self.update_messages(messages))

    def update_messages(self, messages):
        """
        Update the chat display with messages.

        :param messages: The list of messages to display
        """
        print("[DEBUG] Updating messages")
        # Make sure only messages with new IDs are added
        new_messages = [msg for msg in messages if msg[0]
                        not in self.all_messages]
        self.all_messages += new_messages  # Append to existing messages

        print(f"[DEBUG] All messages: {self.all_messages}")

        visible_messages = self.all_messages[self.current_msg_page * self.client.max_msg:(
            self.current_msg_page + 1) * self.client.max_msg]

        print(f"[DEBUG] Visible messages: {visible_messages}")

        if self.chat_display == None:
            return

        # Clear only messages, not buttons or pagination controls
        for widget in self.chat_display.winfo_children():
            widget.destroy()

        self.message_selection = {}  # Dictionary to store selected messages

        # Add message checkboxes for selection
        for idx, (msg_id, sender, message) in enumerate(visible_messages):
            frame = tk.Frame(self.chat_display)
            frame.pack(fill=tk.X, padx=5, pady=2)

            var = tk.BooleanVar()
            self.message_selection[msg_id] = var

            # Bind a trace to update delete button state when selection changes
            var.trace_add(
                "write", lambda *args: self.update_delete_button_state())

            cb = tk.Checkbutton(frame, variable=var)
            cb.pack(side=tk.LEFT)

            lbl = tk.Label(frame, text=f"{sender}: {message}", anchor="w",
                           justify="left", wraplength=self.message_wrap_length)
            lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Bind double click to fill recipient
            lbl.bind("<Double-1>", lambda event,
                     sender=sender: self.open_new_message_window(sender))

        # Update delete button state
        self.update_delete_button_state()

        # Update pagination buttons
        self.prev_msg_button.config(
            state=tk.NORMAL if self.current_msg_page > 0 else tk.DISABLED)

        # Calculate total pages
        total_pages = math.ceil(len(self.all_messages) / self.client.max_msg)
        self.next_msg_button.config(state=tk.NORMAL if self.current_msg_page < total_pages -
                                    1 or len(self.all_messages) < self.unread_count else tk.DISABLED)

        # Force focus back to chat display
        self.chat_display.focus_set()

    def update_delete_button_state(self):
        """
        Enable or disable the delete button based on message selection.
        """
        selected = any(var.get() for var in self.message_selection.values())
        self.delete_msg_button.config(
            state=tk.NORMAL if selected else tk.DISABLED)

    def change_msg_page(self, direction):
        """
        Paginate through messages.

        :param direction: The direction to move in the message list
        """
        print("[DEBUG] Changing message page:", direction)
        new_page = self.current_msg_page + direction
        if new_page < 0:
            return

        num_messages = max(len(self.all_messages), self.unread_count)
        # Calculate total pages
        total_pages = math.ceil(num_messages / self.client.max_msg)
        if new_page >= total_pages:
            return

        self.current_msg_page = new_page
        print(f"Changing message page to {self.current_msg_page}")

        self.update_messages([])

    ### SEND MESSAGE WORKFLOW ###
    def fill_recipient(self, event):
        """
        Fills the recipient entry when a user is clicked in the list.
        """
        print("[DEBUG] Filling recipient")
        selection = self.user_listbox.curselection()
        current_user = self.client.username
        if selection:
            index = selection[0]
            username = self.user_listbox.get(index).replace(
                " (you)", "")  # Remove "(you)" tag
            if username.strip():  # Ensure it's not empty
                if username == current_user:
                    return
                self.open_new_message_window(username)

    def open_new_message_window(self, recipient=""):
        """
        Opens a window to compose and send a new message.

        :param recipient: The recipient to pre-fill in the entry field
        """
        if hasattr(self, 'new_msg_window') and self.new_msg_window is not None:
            self.new_msg_window.destroy()

        new_msg_window = tk.Toplevel(self.root)
        new_msg_window.title("New Message")
        new_msg_window.geometry("400x250")

        # Add padding around the frame
        frame = tk.Frame(new_msg_window, padx=10, pady=20)
        frame.pack(expand=True)

        tk.Label(new_msg_window, text="Recipient Username:").pack(pady=5)
        recipient_entry = tk.Entry(new_msg_window)
        recipient_entry.pack(fill=tk.X, padx=10, pady=5)

        # Pre-fill recipient if provided
        if recipient:
            recipient_entry.insert(tk.END, recipient)

        tk.Label(new_msg_window, text="Message:").pack(pady=5)
        message_entry = tk.Text(new_msg_window, height=5)
        message_entry.pack(fill=tk.BOTH, padx=10, pady=5)

        tk.Button(new_msg_window, text="Send", command=lambda: self.send_message(
            recipient_entry, message_entry)).pack(pady=10)

        self.new_msg_window = new_msg_window

        # Set focus to recipient entry
        recipient_entry.focus_set()

    def send_message(self, recipient_entry, message_entry):
        """
        Handles sending the message.

        :param recipient_entry: The entry field for the recipient
        :param message_entry: The text field for the message
        """
        recipient = recipient_entry.get().strip()
        message = message_entry.get("1.0", tk.END).strip()

        if not recipient or not message:
            messagebox.showerror(
                "Error", "Recipient and message cannot be empty.")
            return

        current_user = self.client.username
        if recipient == current_user:
            messagebox.showerror("Error", "Cannot send message to self.")
            return

        valid_users = [user for _, user in self.all_users]
        if recipient not in valid_users:
            messagebox.showerror("Error", "Recipient not found.")
            return

        # Start thread to send message
        threading.Thread(target=self.process_send_message, args=(
            recipient, message), daemon=True).start()

    def process_send_message(self, recipient, message):
        """
        Send the message in a background thread.

        :param recipient: The recipient of the message
        :param message: The message to send
        """
        success = self.client.send_message(recipient, message)
        self.root.after(0, lambda: self.handle_send_message_result(success))

    def handle_send_message_result(self, success):
        """
        Handle UI update after sending a message.

        :param success: Whether the message was sent successfully
        """
        if success:
            messagebox.showinfo("Message Sent", f"Message sent successfully!")
            self.new_msg_window.destroy()
        else:
            messagebox.showerror("Error", "Failed to send message.")

    ### DELETE MESSAGE WORKFLOW ###
    def delete_selected_messages(self):
        """
        Deletes selected messages.
        """
        selected_msg_ids = [msg_id for msg_id,
                            var in self.message_selection.items() if var.get()]

        if not selected_msg_ids:
            messagebox.showwarning(
                "No Selection", "No messages selected for deletion.")
            return

        # Start thread to delete messages
        threading.Thread(target=self.process_delete_messages,
                         args=(selected_msg_ids,), daemon=True).start()

    def process_delete_messages(self, selected_msg_ids):
        """
        Process message deletion in a background thread.

        :param selected_msg_ids: The list of message IDs to delete
        """
        success = self.client.delete_message(selected_msg_ids)
        self.root.after(0, lambda: self.handle_delete_messages_result(success))

    def handle_delete_messages_result(self, success):
        """
        Handle UI update after deleting messages.

        :param success: Whether the messages were deleted successfully
        """
        if success:
            messagebox.showinfo("Success", "Messages deleted successfully")

            # Remove deleted messages from current list
            deleted_ids = [msg_id for msg_id,
                           var in self.message_selection.items() if var.get()]
            self.all_messages = [
                msg for msg in self.all_messages if msg[0] not in deleted_ids]

            # Update unread count if necessary
            if len(self.all_messages) < self.unread_count:
                self.unread_count = len(self.all_messages)

            # Update UI with remaining messages
            self.current_msg_page = 0  # Reset to first page
            self.update_messages([])

            # Disable delete button
            self.delete_msg_button.config(state=tk.DISABLED)
        else:
            messagebox.showerror("Error", "Failed to delete messages")

    ### DELETE ACCOUNT WORKFLOW ###
    def confirm_delete_account(self):
        """
        Confirm account deletion.
        """
        confirm = messagebox.askokcancel(
            "Confirm", "Are you sure you want to delete your account?")
        if confirm:
            # Start thread to delete account
            threading.Thread(target=self.delete_account, daemon=True).start()

    def delete_account(self):
        """
        Delete the account in a background thread.
        """
        print("[DEBUG] Deleting account")
        success = self.client.delete_account()
        self.root.after(0, self.handle_delete_account_result(success))

    def handle_delete_account_result(self, success):
        """
        Handle UI update after deleting the account.

        :param success: Whether the account was deleted successfully
        """
        if success:
            messagebox.showinfo("Account Deleted",
                                "Account deleted successfully")
            self.root.after(0, self.disconnect)
        else:
            messagebox.showerror("Error", "Failed to delete account")

    ### HELPER METHODS ###
    def disconnect(self):
        """
        Disconnect from the server.
        """
        self.client.stop_polling_messages()
        self.root.destroy()

    def clear_window(self):
        """
        Clear the window of all widgets.
        """
        for widget in self.root.winfo_children():
            widget.destroy()
