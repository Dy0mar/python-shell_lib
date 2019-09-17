# -*- coding: utf-8 -*-

import time
import socks
import paramiko


class Sftp (object):

    def __init__(self, server, port, user, password,
                 sock_address=None, sock_port=None):
        self.server = server
        self.port = port
        self.user = user
        self.password = password
        self.sock_address = sock_address
        self.sock_port = sock_port
        self.t = None
        self.sftp = None
        self.sock = None
        if all([sock_address, sock_port]):
            self.set_socks()

    def sftp_open(self):
        self.ok_print('Connection open')

        # Transport
        self.t = paramiko.Transport(sock=self.sock)
        self.t.connect(username=self.user, password=self.password)
        self.ok_print('Connection complete')

        # SFTPClient
        self.sftp = paramiko.SFTPClient.from_transport(self.t)

    def sftp_close(self):
        if self.t:
            self.t.close()
        if self.sftp:
            self.sftp.close()
        self.ok_print('Connection close')

    def exec_cmd(self, cmd):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.server,
                       username=self.user,
                       password=self.password,
                       sock=self.sock)

        stdin, stdout, stderr = client.exec_command(cmd)
        res = stdout.read() + stderr.read()
        client.close()
        return res

    def sudo_exec_invoke_shell(self, cmd, count):
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=self.server,
                       username=self.user,
                       password=self.password,
                       sock=self.sock)

        response_list = []
        shell = client.invoke_shell()
        shell.send('sudo -s\n')
        data = shell.recv(1024)
        print(data)
        shell.send(cmd + '\n')
        time.sleep(4)
        _ = shell.recv(1024)
        count += 1

        while count:
            data = shell.recv(1024)
            print(data)

            if data.find('free'):
                tmp = data.split(' ')
                response_list.append(tmp[0])
                count -= 1

            if count == 0:
                break

        client.close()
        return response_list

    def sftp_get(self, remote_path, local_path):
        print('Download %s >> %s' % (remote_path, local_path))
        try:
            self.sftp.get(remote_path, local_path)
            return True
        except Exception as e:
            print e.message
            err = 'Remote - %s, Local - %s' % (remote_path, local_path)
            self.err_print(err)
            return False

    def sftp_put(self, local_path, remote_path):
        print('Upload %s >> %s' % (local_path, remote_path))

        path = remote_path.split('/')
        path.pop()  # dir path only
        full_p = ''
        for p in path:
            if p:
                full_p += '/' + p
                if not self.sftp_stat(path=full_p):
                    print("PATH EXISTS " + full_p)
                    self.sftp_mkdir(full_p)
        self.sftp.put(localpath=local_path, remotepath=remote_path)

    def sftp_stat(self, path):
        try:
            return self.sftp.stat(path)
        except Exception as e:
            print e.message
            return False

    def sftp_listdir(self, path):
        return self.sftp.listdir(path=path)

    def sftp_mkdir(self, path, mode=0o755):
        try:
            self.sftp.mkdir(path, mode)
        except IOError:
            print('Unable to create directory: ' + path)
            if self.sftp_stat(path):
                print('dir exists')
            else:
                print('some went wrong')

    def set_socks(self):
        self.sock = socks.socksocket()
        self.sock.setproxy(
            socks.PROXY_TYPE_SOCKS5,
            self.sock_address, self.sock_port
        )
        self.sock.connect((self.server, self.port))

    @staticmethod
    def ok_print(text):
        """
        green text
        """
        print('\033[2;32m' + text + '\033[2;m')

    @staticmethod
    def err_print(text):
        """
        red text
        """
        print('\033[2;31m' + text + '\033[2;m')
