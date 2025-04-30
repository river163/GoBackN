from client import Client
from config import Configuration
from server import Server


def main():
    config = Configuration("config.ini")
    server = Server(config)
    server.start()
    client = Client(config)

    try:
        while True:
            cmd = input("\nEnter command (get <IP> <PORT> <FILENAME> or 'exit'): ").strip()
            if cmd.lower() == 'exit':
                break

            parts = cmd.split()
            if len(parts) == 4 and parts[0].lower() == 'get':
                _, ip, port_str, filename = parts
                try:
                    port = int(port_str)
                    client.request_file(ip, port, filename)
                except ValueError:
                    print("Invalid port number")
            else:
                print("Invalid command. Usage: get <IP> <PORT> <FILENAME>")
    except KeyboardInterrupt:
        print("\nShutting down...")
        exit(0)
    finally:
        server.stop()


if __name__ == "__main__":
    main()