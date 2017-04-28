import os
import time
import base64
import socks
import paramiko


class Sftp (object):
    __curr_path = os.path.abspath(os.curdir)
    __servers = {}
    __socks = {}
    
    def __init__(self, server, port, user, password, sock_address=None, sock_port=None):
        self.set_servers('server', server)
        self.set_servers('port', port)
        self.set_servers('user', user)
        self.set_servers('password', password)
        self.set_socks(sock_address, sock_port)
        
    def sftp_open(self):
        self.ok_print('Connection open')
        sock=socks.socksocket()
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, self.socks('address'), self.socks('port'), True)
        sock.connect((self.servers('server'), self.servers('port')))
### Transport
        self.t=paramiko.Transport(sock)
        self.t.connect(username=self.servers('user'), password=base64.b64decode(self.servers('password')))
        self.ok_print('Connection complete')
### SFTPClient
        self.sftp=paramiko.SFTPClient.from_transport(self.t)

    def sftp_close (self):
        self.t.close()
        self.sftp.close()
        self.ok_print('Connection close')
    
    def exec_cmd(self, cmd):
        sock=socks.socksocket()
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, self.socks('address'), self.socks('port'), True)
        sock.connect((self.servers('server'), self.servers('port')))

        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.servers('server'),
                       username=self.servers('user'),
                       password=self.servers('password'),
                       sock=sock)

        stdin, stdout, stderr=client.exec_command(cmd)
        res=stdout.read() + stderr.read()
        client.close()
        return res

    def sudo_exec_invoke_shell(self, cmd, count):
        sock=socks.socksocket()
        sock.setproxy(socks.PROXY_TYPE_SOCKS5, self.socks('address'), self.socks('port'), True)
        sock.connect((self.servers('server'), self.servers('port')))

        client=paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.servers('server'),
                       username=self.servers('user'),
                       password=self.servers('password'),
                       sock=sock)

        response_list=[]
        shell=client.invoke_shell()
        shell.send('sudo -s\n')
        data=shell.recv(1024)
        print(data)
        data=''
        shell.send(cmd + '\n')
        time.sleep(4)
        data=shell.recv(1024)
        data=''
        count += 1

        while count:
            data=shell.recv(1024)
            print (data)

            if data.find('free'):
                tmp=data.split(' ')
                response_list.append(tmp[0])
                count -= 1
            
            if count == 0:
                break

        client.close()
        return response_list

    def sftp_get (self, remotepath, localpath):
        print ('Download %s >> %s' % (remotepath, localpath))
        try:
            self.sftp.get(remotepath, localpath)
            return True
        except:
            self.err_print('Download error. No such file or other. Remote - %s, Local - %s' % (remotepath, localpath))
            return False
        
    def sftp_put (self, localpath, remotepath):
        print ('Upload %s >> %s' % (localpath, remotepath))

        path=remotepath.split('/')
        path.pop() # dir path only
        full_p=''
        for p in path:
            if p:
                full_p +=  '/' + p
                if self.sftp_stat(path=full_p) == False:
                    print ("PATH EXISTS " + full_p)
                    self.sftp_mkdir(full_p)
        self.sftp.put(localpath=localpath, remotepath=remotepath)
    
    def sftp_stat(self, path):
        try:
            return self.sftp.stat(path)
        except:
            return False
    
    def sftp_listdir(self, path):
        info=self.sftp.listdir(path=path)
        return info
    
    def sftp_mkdir(self, path, mode=0o755):
        try:
            self.sftp.mkdir(path, mode)
        except:
            print('Unable to create directory:  ' + path)
            if self.sftp_stat(path):
                print('DIR EXISTS ')
            else:
                print ('ACCESS DENIED OR OTHER')

    def set_servers (self, key, value):
        if key:
            self.__servers [key]=value
    
    def servers (self, key=None):
        if key:
            return self.__servers [key]
        else:
            return self.__servers

    def set_socks (self, sock_address=False, sock_port=False):
        if sock_address and sock_port:
            self.__socks['address']=sock_address
            self.__socks['port']=int(sock_port)

    def socks(self, key=None):
        if key:
            return self.__socks[key]
        else:
            return self.__socks
    
    @staticmethod
    def isfile (file_path):
        if os.path.exists(file_path):
            return True
        else :
            return False

    @staticmethod
    def isdir (dir_path) :
        if os.path.isdir(dir_path):
            return True
        else :    
            return False

    @staticmethod
    def ok_print(sString):
        """
        green text
        """
        print ('\033[2;32m' + sString + '\033[2;m')

    @staticmethod
    def err_print(sString):
        """
        red text
        """
        print ('\033[2;31m' + sString + '\033[2;m')