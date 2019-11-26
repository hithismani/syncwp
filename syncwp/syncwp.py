import threading, time, os, shutil, argparse, tarfile, gzip, subprocess, paramiko, getpass
from colorama import Fore, Style

strdata=''
fulldata=''
sftp = ''

def print_message(colour, message):
    print (colour + message)
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

def run_server_command(connection, commands):
    connection.send_shell("cd /")
    for command in commands:
        print_message(Fore.BLUE, ("Runnning Command: " + command))
        connection.send_shell(command)
        time.sleep(2)
    time.sleep(10)
    print_message(Fore.BLUE, "Notes: Waiting for 10 Seconds Before Next Set Of Commands")
    connection.send_shell("cd /")

def run_local_command(commands):
    for command in commands:
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

def run(args):
    current_path = os.getcwd()
    domain = args.domain
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
                folder_create(current_path + "/local-backups")
                os.chdir('%s/local-backups/' % current_path)   
                if "d" in args.localtasks:
                    #Export Database
                    export_commands = [
                        ('lando wp search-replace ' +args.localdomain + ' ' + domain),
                        'lando db-export database.sql',
                        ('lando wp search-replace ' +domain + ' ' + args.localdomain)
                        ]
                    run_local_command(export_commands)
                if "w" in args.localtasks:
                    os.chdir('%s/wp-content/' % current_path)  
                    #Export Database
                    export_commands = [('tar -vczf wordpress-backup.tar.gz *')]                  
                    run_local_command(export_commands)
                    shutil.move('%s/wp-content/wordpress-backup.tar.gz' % current_path, '%s/local-backups/wordpress-backup.tar.gz' % current_path)
                    os.chdir('%s' % current_path)                
        if "U" in args.localtasks:
            connection = login_connect(args.user,password,args.host)
            connection.open_shell()
            ftp_client= connection.sftp()         
            sql_file_name = "database.sql.gz"
            wp_content_file_name = "wordpress-backup.tar.gz"                
            if os.path.exists(current_path+'/local-backups/'+ wp_content_file_name):               
                #unpack sql gzip in local machine, and prepare for upload
                ftp_client.put("%s/local-backups/wordpress-backup.tar.gz" % current_path,"/opt/easyengine/sites/%s/app/htdocs/wp-content/wordpress-backup.tar.gz" % domain, callback=printTotals)
                commands = []
                if "R" in args.localtasks:
                    commands = [
                        'cd '+ ('/opt/easyengine/sites/%s/app/htdocs/wp-content/' %domain ),
                        'tar -xvzf wordpress-backup.tar.gz','rm wordpress-backup.tar.gz'
                        ]
                else:
                    commands = [
                        'cd '+ ('/opt/easyengine/sites/%s/app/htdocs/wp-content/' %domain ),
                        'tar -xvzf wordpress-backup.tar.gz'
                        ]
                run_server_command(connection, commands)              
            else:
                print_message(Fore.RED, "Notes: WP-Content Not In Directory")
            if os.path.exists(current_path+'/local-backups/'+ sql_file_name):               
                #unpack sql gzip in local machine, and prepare for upload
                print_message(Fore.BLUE, "Notes: Unpacking .tar.gz Files into Wp-Content")
                os.chdir('%s/local-backups/' % current_path)
                gunzip_shutil((current_path+'/local-backups/'+ sql_file_name),(current_path+'/local-backups/database.sql'))
                print_message(Fore.BLUE, "Notes: Unpacked!Now Uploading")
                ftp_client.put("%s/local-backups/database.sql" % current_path,"/opt/easyengine/sites/%s/app/htdocs/database.sql" % domain, callback=printTotals)
                if "R" in args.localtasks:
                    commands = [
                        'ee shell %s' % domain,
                        'wp db import ./database.sql',
                        'exit',
                        'cd /',
                        ('rm /opt/easyengine/sites/%s/app/htdocs/database.sql' % domain)
                        ]
                else:
                    commands = [
                        'ee shell %s' % domain,
                        'wp db import ./database.sql',
                        'exit'
                        ]
                run_server_command(connection, commands)
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
                folder_create(current_path + "/server-backups")
                connection = login_connect(args.user,password,args.host)
                connection.open_shell()
                if "d" in args.servertasks:
                #Export Database
                    export_commands = [
                        'ee shell %s' % domain,
                        'wp db export ./database.sql',
                        'exit'
                        ]
                    run_server_command(connection,export_commands)
                #Export wp-content
                if "w" in args.servertasks:
                    wp_commands = [
                        'cd /opt/easyengine/sites/%s/app/htdocs/wp-content' % domain,
                        'tar -vczf wordpress-backup.tar.gz *'
                        ]
                    run_server_command(connection,wp_commands)
                    time.sleep(10)
                if "D" in args.servertasks:   
                #download database / wp-content
                    ftp_client= connection.sftp()
                    if "d" in args.servertasks:
                        ftp_client.get("/opt/easyengine/sites/%s/app/htdocs/database.sql" % domain,"%s/server-backups/database.sql" % current_path, callback=printTotals)
                    if "w" in args.servertasks:
                        ftp_client.get("/opt/easyengine/sites/%s/app/htdocs/wp-content/wordpress-backup.tar.gz" % domain,"%s/server-backups/wordpress-backup.tar.gz" % current_path, callback=printTotals)
                if "R" in args.servertasks:     
                    delete_commands = []
                    if "w" in args.servertasks:
                    #delete server files
                        delete_commands.append('rm /opt/easyengine/sites/%s/app/htdocs/wp-content/wordpress-backup.tar.gz' % domain)
                    if "d" in args.servertasks:    
                        delete_commands.append('rm /opt/easyengine/sites/%s/app/htdocs/database.sql' % domain)
                    run_server_command(connection, delete_commands)
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
            file_name = "wordpress-backup.tar.gz"
            if os.path.exists(current_path+'/server-backups/'+ file_name):
                if os.path.exists(current_path+'/wp-content/'):
                        #unpack zip files
                        print_message(Fore.BLUE, "Notes: Unpacking .tar.gz Files into Wp-Content")
                        os.chdir('%s/wp-content/' % current_path)
                        tar = tarfile.open(current_path+'/server-backups/'+ file_name)
                        tar.extractall()
                        tar.close()
                        print_message(Fore.BLUE, "Notes: .tar.gz Is Now Unpacked!")
                        os.chdir('%s' % current_path)
            else:
                print_message(Fore.RED,"Notes: WP-CONTENT Folder Not Found")
        else:
            print_message(Fore.BLUE,"Notes: You've skipped Export Function")
        if "M" in args.servertasks:
            if args.localdomain:
                run_local_command(['lando db-import /server-backups/database.sql','lando wp search-replace ' +domain + ' ' + args.localdomain])
            else:
                print_message(Fore.BLUE,"Notes: No local domain set")

def main():
    parser=argparse.ArgumentParser(description="SyncWP")
    parser.add_argument("-domain",help="Enter Domain Name" ,dest="domain", type=str, required=True)
    parser.add_argument("-local",help="Local Domain Name / Host URL" ,dest="localdomain", type=str, required=False)
    parser.add_argument("-host",help="Enter Domain Dhost" ,dest="host", type=str, required=True)
    parser.add_argument("-user",help="Enter Domain Username" ,dest="user", type=str, required=True)
    parser.add_argument("-password",help="Enter Domain Password" ,dest="password", type=str, required=False)
    parser.add_argument("-server",help="(B)ackup (d)atabase, (w)p_content | (D)ownload | (R)emove | (E)xtract Files | (M)igrate Into Local | (S)kip All" ,dest="servertasks", type=str, default="BdwDREM" ,required=True)
    parser.add_argument("-dev",help="(B)ackup (d)atabase, (w)p_content | (U)pload | (R)emove (S)kip All" ,dest="localtasks", type=str, default="BdwUR" ,required=True)
    parser.set_defaults(func=run)
    args=parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()