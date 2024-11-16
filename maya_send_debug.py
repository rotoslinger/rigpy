import socket

# this will only work

def send_code_to_maya(code, host='localhost', port=1234):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        client_socket.sendall(code.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        print(f"Response from Maya: {response}")

# Example: Send a Python command to Maya
send_code_to_maya("print(cmds.polySphere())")
