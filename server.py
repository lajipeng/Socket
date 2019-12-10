import socket
import threading
import json
import hashlib
import base64
import struct

MAGIC_STRING='258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
HOST='localhost'
PORT = 8888
HANDSHAKE_STRING="HTTP/1.1 101 Switching Protocols\r\n"  \
      "Upgrade:websocket\r\n"\
      "Connection: Upgrade\r\n"  \
      "Sec-WebSocket-Accept: {1}\r\n"  \
      "WebSocket-Location:ws://{2}/chat\r\n"\
      "WebSocket-Protocol:chat\r\n\r\n"

def recv_data(all_data):
    code_len = all_data[1] & 127
    if code_len == 126:
        masks = all_data[4:8]
        data = all_data[8:]
    elif code_len == 127:
        masks = all_data[10:14]
        data = all_data[14:]
    else:
        masks = all_data[2:6]
        data = all_data[6:]
    raw_str = ""
    i = 0
    for d in data:
        raw_str += chr(d ^ masks[i % 4])
        i += 1
    return raw_str


def writedata(msg):
    data = struct.pack('B', 129) # 将129转为16进制 data = b'\x81'

    length = len(msg)
    if length < 126:
        data += struct.pack("B", length)
    elif length <= 0xFFFF:
        data += struct.pack("!BH", 126, length)
    else:
        data += struct.pack("!BQ", 127, length)

    data += bytes(msg, encoding="utf-8")
    return data


def parse_headers(msg):
    headers = {}
    header, data = msg.split('\r\n\r\n', 1)
    for line in header.split('\r\n')[1:]:
        key, value = line.split(': ', 1)
        headers[key] = value
    headers['data'] = data
    return headers

def generate_token(msg):
    key = msg + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
    key = key.encode()
    ser_key = hashlib.sha1(key).digest()
    return base64.b64encode(ser_key)


class Server:
    def __init__(self):
        """
        构造
        """
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__connections = list()
        self.__nicknames = list()
        self.__rooms = list()


    def start(self):
        """
        启动服务器
        """
        # 绑定端口
        self.__socket.bind(('localhost', 8888))
        # 启用监听
        self.__socket.listen(5)
        print('[Server] 服务器正在运行......')

        # 清空连接
        self.__connections.clear()
        self.__nicknames.clear()
        self.__rooms.clear()
        self.__connections.append(None)
        self.__nicknames.append('System')
        self.__rooms.append(None)

        # 开始侦听：用于接收每一个客户端线程，和它们进行三次握手
        while True:
            connection, address = self.__socket.accept()
            # getsockname() ('127.0.0.1', 8888) fileno() 440 address ('127.0.0.1', 56943)
            print('[Server] 收到一个新连接', connection.getsockname(), connection.fileno(), address)
            self.__connections.append(connection)
            # self.__nicknames.append(obj['nickname'])
            # self.__rooms.append(obj['id'])

            # 握手流程
            shake = connection.recv(1024).decode()
            headers = {} # 协议头
            print(shake)
            header, data = shake.split('\r\n\r\n', 1)

            for line in header.split('\r\n')[1:]:
                key, val = line.split(': ', 1)
                headers[key] = val

            sec_key = headers['Sec-WebSocket-Key'] # 获取协议头里的socket-key
            res_key = base64.b64encode(hashlib.sha1((sec_key + MAGIC_STRING).encode()).digest()).decode() # 使用bs64解码，注意HANDSHAKE_STRING是解密socket-key时需要的辅助字符串，是固定的
            str_handshake = HANDSHAKE_STRING.replace('{1}', res_key).replace('{2}', HOST + ':' + str(PORT)).encode() # 生成握手回复信息
            connection.send(str_handshake) # 把握手回复信息发送给客户端 完成握手
            # connection.send('\
            # HTTP/1.1 101 Switching Protocols\r\n\
            # Upgrade: webSocket\r\n\
            # Connection: Upgrade\r\n\
            # Sec-WebSocket-Accept: %s\r\n\r\n' % token)

            # 开辟一个新的线程，用于监听客户端
            thread = threading.Thread(target=self.__user_thread, args=(len(self.__connections) - 1,))
            thread.setDaemon(True)
            thread.start()
    def __sendfile(self, user_id, content, type):
        mes = b''
        try:
            file = open(str(content),'rb')
            mes = file.read()
        except:
            print('error{}'.format(str(content)))
        else:
            file.close()
        return mes

    def __broadcast(self, user_id, content, type):
        """
        广播函数，用于向所有线程的客户端发送消息
        比如，有一个新人进入了房间，需要告诉所有的客户端，从而刷新前端
        用于你的文件管理系统的话，比如有一个客户端上传了新文件，则调用这个广播函数让所有客户端刷新界面，才能看到新文件
        """

        nickname = self.__nicknames[user_id]
        room_id = self.__rooms[user_id]
        room_num = 0
        for i in range(1, len(self.__rooms)):
            if self.__rooms[i] == room_id:
                room_num += 1

        if type == 'Enter':  # 新用户登入房间
            for i in range(1, len(self.__rooms)):
                if self.__rooms[i] == room_id and self.__rooms is not None:
                    if i != user_id:
                        # self.__connections[i].send(writedata(json.dumps({
                        #     'type': 'Enter',
                        #     'roomid': room_id,
                        #     'number': room_num,
                        #     'text': '',
                        #     'sender': nickname,
                        #     'self_send': 1
                        # })))
                        # json.dumps将python对象格式化成json字符.
                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Enter',
                            'roomid': room_id,
                            'number': room_num,
                            'text': '',
                            'sender': nickname,
                            'self_send': 0
                        })))

        elif type == 'Talk':  # 用户发消息
            for i in range(1, len(self.__rooms)):
                if self.__rooms[i] == room_id and self.__rooms is not None:
                    if i == user_id:
                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Talk',
                            'roomid': room_id,
                            'number': room_num,
                            'text': content,
                            'sender': nickname,
                            'self_send': 1
                        })))
                    else:
                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Talk',
                            'roomid': room_id,
                            'number': room_num,
                            'text': content,
                            'sender': nickname,
                            'self_send': 0
                        })))

        elif type == 'Picture':  # 用户发图片消息
            for i in range(1, len(self.__rooms)):
                if self.__rooms[i] == room_id and self.__rooms is not None:
                    if i == user_id:
                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Picture',
                            'roomid': room_id,
                            'number': room_num,
                            'text': content,
                            'sender': nickname,
                            'self_send': 1
                        })))
                    else:
                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Picture',
                            'roomid': room_id,
                            'number': room_num,
                            'text': content,
                            'sender': nickname,
                            'self_send': 0
                        })))

        elif type == 'Quit':  # 用户退出
            print("Quit Success")
            for i in range(1, len(self.__rooms)):
                if self.__rooms[i] == room_id and self.__rooms is not None:
                    if i == user_id:

                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Quit',
                            'roomid': room_id,
                            'number': room_num,
                            'text': '',
                            'sender': nickname,
                            'self_send': 1
                        })))
                        # self.__connections[user_id].close()
                        # self.__connections[user_id] = None
                        # self.__nicknames[user_id] = None

                    else:
                        self.__connections[i].send(writedata(json.dumps({
                            'type': 'Quit',
                            'roomid': room_id,
                            'number': room_num,
                            'text': '',
                            'sender': nickname,
                            'self_send': 0
                        })))


    def __user_thread(self, user_id):
        """
        客户端线程，即每当用户登入聊天室后，都会执行这个函数
        """
        connection = self.__connections[user_id]
        self.__nicknames.append(user_id)
        self.__rooms.append(None)
        # nickname = self.__nicknames[user_id]
        # room_id = self.__rooms[user_id]
        # print('[Server] 用户', user_id, nickname, '加入聊天室', room_id)

        while True:
            # noinspection PyBroadException
            try:
                buffer = connection.recv(1024 * 1024)
                raw_str = recv_data(buffer)
                print(raw_str)
                if buffer[:3] != 'GET': # 如果是GET请求
                    # 解析成json数据
                    obj = json.loads(raw_str)
                    print("JSON String %s" % obj)

                    # 如果是广播指令
                    if obj['type'] == 'Enter':
                        content_string = obj['content']
                        obj['content'] = ''
                        nickname = ''
                        for i in range(len(content_string)):
                            if content_string[i] == ';':
                                for j in range(i+1, len(content_string)):
                                    nickname += content_string[j]
                                break
                            else:
                                obj['content'] += content_string[i]

                        self.__rooms[user_id] = obj['content']
                        self.__nicknames[user_id] = nickname
                        room_id = self.__rooms[user_id]
                        print('[Server] 用户', user_id, nickname, '加入聊天室', room_id)

                        room_num = 0
                        for i in range(1, len(self.__rooms)):
                            if self.__rooms[i] == obj['content']:
                                room_num += 1

                        connection.send(writedata(json.dumps({
                            "type": "Enter",
                            "roomid": obj["content"],
                            "number": room_num,
                            "text": len(self.__connections) - 1,
                            "sender": nickname,
                            "self_send": 1
                        })))
                        self.__broadcast(user_id, obj['content'], obj['type'])

                    elif obj['type'] == 'Talk':
                        self.__broadcast(user_id, obj['content'], obj['type'])
                        self.__sendfile(user_id, obj['content'], obj['type'])
                    elif obj['type'] == 'Picture':
                        self.__broadcast(user_id, obj['content'], obj['type'])
                    elif obj['type'] == 'Quit':
                        room_id = self.__rooms[user_id]
                        room_num = 0
                        nickname = self.__nicknames[user_id]
                        for i in range(1, len(self.__rooms)):
                            if self.__rooms[i] == room_id:
                                room_num += 1
                        for i in range(1, len(self.__rooms)):
                            if self.__rooms[i] == room_id and self.__rooms is not None:
                                if i == user_id:
                                    self.__connections[i].send(writedata(json.dumps({
                                        'type': 'Quit',
                                        'roomid': room_id,
                                        'number': room_num,
                                        'text': '',
                                        'sender': nickname,
                                        'self_send': 1
                                    })))
                                    # self.__connections[user_id].close()
                                    # self.__connections[user_id] = None
                                    # self.__nicknames[user_id] = None
                                else:
                                    self.__connections[i].send(writedata(json.dumps({
                                        'type': 'Quit',
                                        'roomid': room_id,
                                        'number': room_num - 1,
                                        'text': '',
                                        'sender': nickname,
                                        'self_send': 0
                                    })))
                        self.__rooms[user_id] = None
                        # self.__broadcast(user_id, obj['content'], obj['type'])
                        # self.__connections[user_id].close()
                        # self.__connections[user_id] = None
                        # self.__nicknames[user_id] = None
                    else:
                        print('[Server] 无法解析json数据包:', connection.getsockname(), connection.fileno())
            except Exception:
                print('[Server] 连接失效:', connection.getsockname(), connection.fileno())
                room_id = self.__rooms[user_id]
                room_num = 0
                nickname = self.__nicknames[user_id]
                for i in range(1, len(self.__rooms)):
                    if self.__rooms[i] == room_id:
                        room_num += 1
                for i in range(1, len(self.__rooms)):
                    if self.__rooms[i] == room_id and self.__rooms is not None:
                        if i != user_id:
                            self.__connections[i].send(writedata(json.dumps({
                                'type': 'Quit',
                                'roomid': room_id,
                                'number': room_num - 1,
                                'text': '',
                                'sender': nickname,
                                'self_send': 0
                            })))
                self.__rooms[user_id] = None
                self.__connections[user_id].close()
                self.__connections[user_id] = None
                self.__nicknames[user_id] = None

if __name__ == "__main__":
    tt = Server()
    tt.start()


