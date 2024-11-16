import socket











# Settings for the connection to Maya
HOST = '127.0.0.1'  # Maya server IP
PORT = 1234         # Port Maya is listening on

def send_code_to_maya(file_path):
    """Reads and sends the code in the given file to Maya."""
    try:
        # Establish connection
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))

            # Read file content
            with open(file_path, 'r') as file:
                code = file.read()

            # Send the code to Maya and print response
            client_socket.sendall(code.encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            print(f"Response from Maya: {response}")
    except Exception as e:
        print(f"Failed to send code to Maya: {e}")
print('sending to maya')