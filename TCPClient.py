from socket import *
serverName = '101.94.129.106'
serverPort = 12001
# AF_INET 指示底层网络使用的IPv4，SOCK_STREAM指示套接字类型
clientSocket = socket(AF_INET, SOCK_STREAM)
# 将服务器的端口号serverPort与该套接字关联起来
clientSocket.connect((serverName, serverPort))
sentence = raw_input('Input lowercase sentence:')
clientSocket.send(sentence.encode())
modifiedSentence = clientSocket.recv(1024)
print('From Server:', modifiedSentence.decode())
clientSocket.close()