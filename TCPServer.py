from socket import *
serverPort = 12000
# AF_INET 指示底层网络使用的IPv4，SOCK_STREAM指示套接字类型
serverSocket = socket(AF_INET, SOCK_STREAM)
# 将服务器的端口号serverPort与该套接字关联起来
serverSocket.bind(('', serverPort))
# serverSocket是我们的欢迎套接字。在创建这扇欢迎之门之后，我们将等待并聆听某个客户敲门
serverSocket.listen(1)
print('The server is ready to receive')
while True:
    # 当客户敲该门时，程序为socketSocket调用accept()方法，这在服务器中创建了一个称为connectionSocket的新套接字，由这个指定的客户专用
    connectionSocket, addr = serverSocket.accept()
    sentence = connectionSocket.recv(1024).decode()
    capitalizedSentence = sentence.upper()
    connectionSocket.send(capitalizedSentence.encode())
    connectionSocket.close()