from network import ChatClient
import config
from ui import ChatUI
import tkinter as tk


def main():
    print("Starting client...")
    client_config = config.get_config()
    host = client_config["host"]
    port = client_config["port"]
    max_msg = client_config["max_msg"]
    max_users = client_config["max_users"]

    # Set up a ChatClient instance and connect to the server
    print(
        f"Configuration: \nhost={host}, \nport={port}, \nmax_msg={max_msg}, \nmax_users={max_users}")

    # Create a client
    client = ChatClient(host, port, max_msg, max_users)

    # Start the user interface, passing in existing client
    root = tk.Tk()
    ChatUI(root, client)
    root.mainloop()


if __name__ == "__main__":
    main()
