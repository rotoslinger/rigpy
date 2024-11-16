import socket
import sys

def send_code_to_maya(code: str):
    host = '127.0.0.1'  # Maya is listening on localhost
    port = 1234         # Same port that Maya is listening on

    try:
        # Debugging: Print the code that is being sent
        print(f"Sending the following code to Maya (raw code):\n{code}")
        
        # Create a socket connection to Maya
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            # Send the raw code to Maya without any wrapping
            s.sendall(code.encode('utf-8'))
    except Exception as e:
        print(f"Error sending code to Maya: {e}")

def get_active_code():
    # Get the code currently being executed in VS Code
    # This might be customized based on your workflow.
    with open(sys.argv[1], 'r') as file:
        print(f'Script executed in VSCode: {sys.argv[1]}')
        return file.read()

# Example: Run the active code and send it to Maya
if __name__ == "__main__":
    active_code = get_active_code()
    print(f"Active code read from file:\n{active_code}")
    send_code_to_maya(active_code)
active_code = get_active_code()
print(f"Active code to send to Maya:\n{active_code}")
send_code_to_maya(active_code)


'''
# You have to run this in maya to establish a connection.  You can add it to your userSetup.py

import maya.cmds as cmds
import socket
import threading

# Maya command to run in a separate thread
def maya_socket_server(host='localhost', port=1234):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)  # Max 5 queued connections

    print(f"Maya server listening on {host}:{port}")

    def handle_client(client_socket):
        while True:
            try:
                # Receive command from the client
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                print(f"Received command: {data}")

                # Run the command inside Maya
                try:
                    exec(data)
                except Exception as e:
                    print(f"Error executing command: {e}")
                    client_socket.send(f"Error: {e}".encode('utf-8'))
                else:
                    client_socket.send("Command executed successfully".encode('utf-8'))
            except Exception as e:
                print(f"Error handling client: {e}")
                break

        client_socket.close()

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection established with {addr}")
        threading.Thread(target=handle_client, args=(client_socket,)).start()

# Run the server in a new thread
threading.Thread(target=maya_socket_server, daemon=True).start()



'''