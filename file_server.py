#!/usr/bin/python
#coding:utf-8
import socketserver
import subprocess
import string
import time
class FileTcpServer(socketserver.BaseRequestHandler):
    def recvfile(self, filename):
        print("start recv")
        f = open(filename, 'wb')
        print(1)
        self.request.send('ready'.encode())
        print(1)
        while True:
            data = self.request.recv(1024).decode()
            print(data)
            if data == 'EOF':
                print("recv success")
                break
            f.write(data.encode())
        f.close()
                                       
    def sendfile(self, filename):
        print("start send")
        # self.request.send('ready'.encode())
        try:
            f = open(filename, 'rb')
            while True:
                data = f.read(1024)
                if not data:
                    print(111)
                    break
                print(data)
                self.request.send(data)
                print(333)
            print(222)
            f.close()
            time.sleep(0.5)
            self.request.send('EOF'.encode())
            print("send success")
        except:
            self.request.send('EOF'.encode())

    def recvImage(self, filename):
        print("start recv")
        f = open(filename, 'wb')
        self.request.send('ready'.encode())
        while True:
            data = self.request.recv(1024)
            print(data)
            if data == b'EOF':
                print("recv success")
                break
            f.write(data)
        f.close()
    def sendImage(self, filename):
        print("start send")
        # self.request.send('ready'.encode())
        try:
            f = open(filename, 'rb')
            while True:
                data = f.read(1024)
                if not data:
                    print(111)
                    break
                print(data)
                self.request.send(data)
                print(333)
            print(222)
            f.close()
            time.sleep(0.5)
            self.request.send('EOF'.encode())
            print("send success")
        except:
            self.request.send('EOF'.encode())
    def recvVideo(self, filename):
        print("start recv")
        f = open(filename, 'wb')
        print(1)
        self.request.send('ready'.encode())
        print(1)
        while True:
            data = self.request.recv(1024)
            print(data)
            if len(data) == 0:
                print("recv success")
                break
            f.write(data)
            print(2)
        f.close()
    def sendVideo(self, filename):
        print("start send")
        # self.request.send('ready'.encode())
        try:
            f = open(filename, 'rb')
            while True:
                data = f.read(1024)
                if not data:
                    print(111)
                    break
                print(data)
                self.request.send(data)
                print(333)
            print(222)
            f.close()
            time.sleep(0.5)
            self.request.send('EOF'.encode())
            print("send success")
        except:
            self.request.send('EOF'.encode())

    def handle(self):
        print("get connection from :",self.client_address)
        while True:
            try:
                data = self.request.recv(1024).decode()
                print("get data:", data)   
                # action, filename = data.split()
                # print(action,filename)
                if not data:
                    print("break the connection")
                    break                
                else:
                    action, filename, filetype = data.split()
                    if action == "put":
                        if filetype == 'txt':
                            self.recvfile(filename)
                        elif filetype == 'jpg':
                            self.recvImage(filename)
                        elif filetype == 'video':
                            self.recvVideo(filename)
                        else:
                            pass
                    elif action == 'get':
                        if filetype == 'txt':
                            self.sendfile(filename)
                        elif filetype == 'jpg':
                            self.sendImage(filename)
                        elif filetype == 'video':
                            self.sendVideo(filename)
                        else:
                            pass 
                    else:
                        print("get error!")
                        continue
            except Exception:
                print("get error at:")
                                           
                                       
if __name__ == "__main__":
    host = '192.168.1.103'
    port = 1010
    s = socketserver.ThreadingTCPServer((host,port), FileTcpServer)
    s.serve_forever()