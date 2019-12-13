import threading, time, os, shutil, argparse, tarfile, gzip, subprocess, paramiko, getpass, yaml, re
from colorama import init, Fore, Style
init(convert=True)

strdata=''
fulldata=''
sftp = ''

def print_message(colour, message):
    print (colour + str(message))
    print(Style.RESET_ALL)

class ssh:
    shell = None
    client = None
    transport = None
    def __init__(self, address, username, password):
        print_message(Fore.BLUE, ("Connecting to server on ip " + (address) + "."))
        self.client = paramiko.client.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
        self.client.connect(address, username=username, password=password, look_for_keys=False)
        self.transport = paramiko.Transport((address, 22))
        self.transport.connect(username=username, password=password)  
        thread = threading.Thread(target=self.process)
        thread.daemon = True
        thread.start()
    def sftp(self):
        return self.client.open_sftp()
    def close_connection(self):
        if(self.client != None):
            self.client.close()
            self.transport.close()
    def open_shell(self):
        self.shell = self.client.invoke_shell()
    def send_shell(self, command):
        if(self.shell):
            self.shell.send(command + "\n")
        else:
            print_message(Fore.RED, "Shell not opened.")
    def process(self):
        global strdata, fulldata
        while True:
            # Print data when available
            if self.shell is not None and self.shell.recv_ready():
                alldata = self.shell.recv(1024)
                while self.shell.recv_ready():
                    alldata += self.shell.recv(1024)
                strdata = strdata + alldata.decode('utf-8')
                fulldata = fulldata + alldata.decode('utf-8')
                strdata = self.print_lines(strdata) # print all received data except last line
    def print_lines(self, data):
        last_line = data
        if '\n' in data:
            lines = data.splitlines()
            for i in range(0, len(lines)-1):
                print(lines[i])
            last_line = lines[len(lines) - 1]
            if data.endswith('\n'):
                print(last_line)
                last_line = ''
        return last_line

def printTotals(transferred, toBeTransferred):
        print("Transferred: {0}\tOut of: {1}".format(transferred, toBeTransferred))

def login_connect(username, password, ipaddress):
    return ssh(ipaddress, username, password)

def gunzip_shutil(source_filepath, dest_filepath, block_size=65536):
    with gzip.open(source_filepath, 'rb') as s_file, \
            open(dest_filepath, 'wb') as d_file:
        shutil.copyfileobj(s_file, d_file, block_size)

def run_server_command(connection, commands, custom_variables):
    connection.send_shell("cd /")
    for command in commands:
        command = command
        to_replace =  re.findall(r"\$\w*",command)
        for item in to_replace:
            print(item)
            command = (command.replace(item, get_from_dict('Key',item,custom_variables)))
        print_message(Fore.BLUE, ("Runnning Command: " + command))
        connection.send_shell(command)
        time.sleep(2)
    time.sleep(10)
    print_message(Fore.BLUE, "Notes: Waiting for 10 Seconds Before Next Set Of Commands")
    connection.send_shell("cd /")

def run_local_command(commands, custom_variables):
    for command in commands:
        command = command
        to_replace =  re.findall(r"\$\w*",command)
        for item in to_replace:
            command = (command.replace(item, get_from_dict('Key',item,custom_variables)))
        print_message(Fore.BLUE, ("Runnning Command: " + command))
        os.system(command+' &')
    time.sleep(10)
    print_message(Fore.BLUE, ("Notes: Waiting for 10 Seconds Before Next Set Of Commands"))

def folder_create(path):
    path = str(path)
    if os.path.isdir(path) != True:
        print_message(Fore.RED, ("Notes: Folder '%s' does not exist. Creating One Now." % path))
        try:
            os.mkdir(path)
        except OSError:
            print_message(Fore.BLUE,("Creation of the directory '%s' failed" % path))
        else:
            print_message(Fore.BLUE,("Successfully created the directory '%s' " % path))
    else:
        print_message(Fore.BLUE,("Notes: Required Folder exists. Yay!"))

# function to return key for any value 
def get_from_dict(val_type, val, array):
    if val.startswith("$"):
        val=val[1:] #To help match true value
    if val_type.lower() == "key":
        for key, value in array: 
            if key == val: 
                return value 
        return val
    elif val_type.lower() == "value":
        for key, value in array: 
            if value == val: 
                return key 
        return val  

def find_index(array, findvar):
    found = False
    i = 0
    while i < len(array):
        if findvar in array[i]:
            found = True
            break
        else:
            i = i +1 
    if found == False:
        return("Not Found")
    else:
        return(i)

def find_replace(source_array, replacement_array): #To replace single element array, with values from a custom array
    source_array = source_array
    to_replace =  re.findall(r"\$\w*",source_array)
    for element in to_replace:
        print_message(Fore.YELLOW, ("Item To Replace: " + element))
        source_array = source_array.replace(element, get_from_dict("Key",element,replacement_array))
    return(source_array)

def run(args):
    with open('syncwp.yaml', 'r') as f:
        yml = yaml.load(f)
        f.close()
    current_path = os.getcwd()

    #Assign Temporary Variables
    temp_variables=[['current_path',current_path]]

    for item, value in yml['customVars'].items():
        temp = [item,value]
        temp_variables.append(temp)
    #Assign Custom Variables (Temporary Variables With All Input Values Set)
    custom_variables = []
    
    for item, value in temp_variables:
        temp = [item,value]
        to_replace =  re.findall(r"\$\w*",value)
        if len(to_replace) > 0:
            for element in to_replace:
                print(element)
                custom_variables.append([item, value.replace(element, get_from_dict('Key',element,custom_variables))])
        else:
            custom_variables.append(temp)
    domain = str(custom_variables[find_index(custom_variables,"deploy_domain")][1])
    local_domain = str(custom_variables[find_index(custom_variables,"local_domain")][1])
    local_backup_dir = custom_variables[find_index(custom_variables,"localServerBackupDirectory")][1]
    server_local_dir = custom_variables[find_index(custom_variables,"serverLocalBackupDirectory")][1]

    password = ""
    if not args.password:
        password = getpass.getpass("Enter Server Password: ")
    else:
        password = args.password
    if "S" in args.localtasks:
        print_message(Fore.BLUE,("Notes: Skipping Local Server Tasks."))
    else:
        if "B" in args.localtasks: 
            if "d" in args.localtasks or "w" in args.localtasks:
                folder_create(os.path.join(current_path,local_backup_dir))
                os.chdir(current_path)   
                if "d" in args.localtasks:
                    #Export Database
                    export_commands = yml["local"]["database"]["export"]
                    run_local_command(export_commands, custom_variables)
                if "w" in args.localtasks:
                    os.chdir(os.path.join(current_path,custom_variables[find_index(custom_variables,"localWPContentPath")][1]))  
                    
                    #Export WpContent
                    export_commands = yml["local"]["wp_content"]["export"]                  
                    run_local_command(export_commands, custom_variables)
                    os.chdir('%s' % current_path)                
        if "U" in args.localtasks:
            connection = login_connect(args.user,password,args.host)
            connection.open_shell()
            ftp_client= connection.sftp()
            sql_file_name = str(custom_variables[find_index(custom_variables,"sql_file_name")][1])
            wp_content_file_name = str(custom_variables[find_index(custom_variables,"wp_content_file_name")][1])
            file_path_local = os.path.join(current_path,local_backup_dir,wp_content_file_name)
            print_message(Fore.RED, file_path_local)  
            file_path_deploy = find_replace(yml["local"]["wp_content"]["upload"]["directory"],custom_variables)
            print_message(Fore.RED, file_path_deploy)  
            if os.path.exists(file_path_local):            
                #unpack sql gzip in local machine, and prepare for upload
                ftp_client.put(file_path_local,file_path_deploy, callback=printTotals)
                commands = yml["local"]["wp_content"]["extract"]
                run_server_command(connection, commands,custom_variables)              
            else:
                print_message(Fore.RED, "Notes: WP-Content Not In Directory")
            local_sql_file_path = os.path.join(current_path,local_backup_dir,sql_file_name) 
            if os.path.exists(local_sql_file_path):               
                #unpack sql gzip in local machine, and prepare for upload
                print_message(Fore.BLUE, "Notes: Unpacking .tar.gz Files into Wp-Content")
                os.chdir(os.path.join(current_path,local_backup_dir))
                gunzip_shutil(local_sql_file_path,local_sql_file_path)
                print_message(Fore.BLUE, "Notes: Unpacked!Now Uploading")
                ftp_client.put(local_sql_file_path,file_path_deploy, callback=printTotals)
                commands=yml["local"]["database"]["import"]
                run_server_command(connection, commands,custom_variables)
                os.chdir('%s' % current_path)                
            else:
                print_message(Fore.RED,"Notes: MySQL Database Not Found On Local Machine")
            print(bytearray(strdata, 'utf-8').decode())   # print the last line of received data
            print('|== \t Server Logs \t ==|')
            print(bytearray(fulldata, 'utf-8').decode())  # This contains the complete data received.
            print('===========================')
            connection.close_connection() #Log Out
            print('==== LOGOUT SUCCESSFUL ====')
        else:
            print("You've skipped Upload Function")
                    
    if "S" in args.servertasks:
        print("Notes: Skipping Server Side Tasks.")
    else:
        if "B" in args.servertasks:
            if "d" in args.servertasks or "w" in args.servertasks:
                folder_create(os.path.join(current_path,server_local_dir))
                connection = login_connect(args.user,password,args.host)
                connection.open_shell()
                if "d" in args.servertasks:
                #Export Database
                    export_commands = yml["server"]["database"]["export"]
                    run_server_command(connection,export_commands,custom_variables)
                #Export wp-content
                if "w" in args.servertasks:
                    wp_commands = yml["server"]["wp_content"]["export"]
                    run_server_command(connection,wp_commands,custom_variables)
                    time.sleep(10)
                if "D" in args.servertasks:   
                #download database / wp-content
                    ftp_client= connection.sftp()
                    if "d" in args.servertasks:
                        server_path = find_replace(yml["server"]["database"]["download"]["serverPath"],custom_variables)
                        local_path = find_replace(yml["server"]["database"]["download"]["localPath"],custom_variables)  
                        ftp_client.get(server_path,local_path, callback=printTotals)
                    if "w" in args.servertasks:
                        server_path = find_replace(yml["server"]["wp_content"]["download"]["serverPath"],custom_variables)
                        local_path = find_replace(yml["server"]["wp_content"]["download"]["localPath"],custom_variables)  
                        ftp_client.get(server_path,local_path, callback=printTotals)
                if "R" in args.servertasks:     
                    if "w" in args.servertasks:
                    #delete server files
                        delete_commands = yml["server"]["wp_content"]["remove"]
                        run_server_command(connection, delete_commands,custom_variables)
                    if "d" in args.servertasks:
                        delete_commands = yml["server"]["database"]["remove"]
                        run_server_command(connection, delete_commands,custom_variables)
                else:
                    print_message(Fore.RED, "Notes: Removal of Backup Files From Server Skipped")
                print(bytearray(strdata, 'utf-8').decode())   # print the last line of received data
                print('|== \t Server Logs \t ==|')
                print(bytearray(fulldata, 'utf-8').decode())  # This contains the complete data received.
                print('===========================')
                connection.close_connection() #Log Out
                print('==== LOGOUT SUCCESSFUL ====')
            else:
                print_message(Fore.BLUE,'Notes: Neither (d)atabase nor (w)ordpress folders requested for backup. Stopping.')
                raise SystemExit
        if "E" in args.servertasks:
            wp_content_file_name = str(custom_variables[find_index(custom_variables,"wp_content_file_name")][1])
            print_message(Fore.RED, str(os.path.join(current_path,server_local_dir,wp_content_file_name)))
            if os.path.exists(os.path.join(current_path,server_local_dir,wp_content_file_name)):
                if os.path.exists(os.path.join(current_path,custom_variables[find_index(custom_variables,"localWPContentPath")][1])):
                        #unpack zip files
                        print_message(Fore.BLUE, "Notes: Unpacking .tar.gz Files into Wp-Content")
                        os.chdir(os.path.join(custom_variables[find_index(custom_variables,"localWPContentPath")][1]))
                        tar = tarfile.open(os.path.join(current_path,server_local_dir,wp_content_file_name))
                        tar.extractall()
                        tar.close()
                        print_message(Fore.BLUE, "Notes: .tar.gz Is Now Unpacked!")
                        os.chdir('%s' % current_path)
                else:
                    print_message(Fore.RED,"Notes: Local WP-CONTENT Folder Not Found")
            else:
                print_message(Fore.RED,"Notes: WP-CONTENT Backup File Not Found")
        else:
            print_message(Fore.BLUE,"Notes: You've skipped Export Function")
        if "M" in args.servertasks:
            if local_domain:
                run_local_command(yml["local"]["database"]["migrate"], custom_variables)
            else:
                print_message(Fore.BLUE,"Notes: No local domain set")

def main():
    parser=argparse.ArgumentParser(description="SyncWP")
    parser.add_argument("-host",help="Enter Domain Host" ,dest="host", type=str, required=True)
    parser.add_argument("-user",help="Enter Domain Username" ,dest="user", type=str, required=True)
    parser.add_argument("-password",help="Enter Domain Password" ,dest="password", type=str, required=False)
    parser.add_argument("-server",help="(B)ackup (d)atabase, (w)p_content | (D)ownload | (R)emove | (E)xtract Files | (M)igrate Into Local | (S)kip All" ,dest="servertasks", type=str, default="BdwDREM" ,required=True)
    parser.add_argument("-dev",help="(B)ackup (d)atabase, (w)p_content | (U)pload | (R)emove (S)kip All" ,dest="localtasks", type=str, default="BdwUR" ,required=True)
    parser.set_defaults(func=run)
    args=parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()