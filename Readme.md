#### 一、 整体框架 

本次pj 采用python 的 flask 框架。前端以 web 形式，用 js 进行实现；后端逻辑使用python 实现。前后端之间的交互均利用手动设计的协议，通过socket 进行交互，而没有依赖 http 以及其他的方式来完成。 

在功能方面，我们实现了网页版的聊天室，支持进入、退出、发送消息（包括文本、图片、视频）。当一个用户有这些操作时，其他所有在聊天室内的用户都会收到消息提醒。 

#### 二、 前端实现以及与后端的交互 

​	前端主要包含搜索并进入房间，以及聊天室之中的发送与接受消息两个主要模块。除此之外socket 实现了对于服务器的消息的监听。 
​	前端的socket 主要利用js 的WebSocket 指令来实现。这个指令支持连接、发送消息、以及设置接收消息时的监听事件，这些基本的功能能够完成我们所想要做的事。此外，发送的消息全部都是字符串形式，于是前端发送json格式的字符串，后端将接受并转码为json。

###### 1、 搜索和进入房间 

用户打开网页时，向服务器发送第一次socket握手，此时二者第一次建立socket联系。

当用户输入某一具体的房间号并进入时，用户根据前端的页面输入在聊天室内的昵称。（系统将自动记录上一次的输入）。 输入完了之后，此时用户完成了进聊天室前的所有准备，
客户端向服务端发送 json 形式的信息：

```json
{
    Content: room_id;nickname;
    Type:"Enter"
}
```

服务器将反馈给前端一个 json 形式的信息，收到了消息后，此时用户进入了房间。当然，服务器也会向其他所有在房间里的用户发送广播，具体的消息接受在后文另有提起。

在用户在聊天室里的时候，用户可以选择退出房间。退出房间时，前端向服务器发送 json：

```json
{
    Content: ""
    Type:"Quit"
}
```

之后服务器接受消息并向其他在聊天室里的用户发送广播，客户端方面，界面重新回到选择进入房间的界面。 

###### 2、 发送与接受消息（包括图片）

在聊天室内，一个用户能收到三种类型的消息：” xxx 进入了”， ”xxx 离开”，以及聊天的消息。

发送消息时，客户端向服务器发送一个json：

```json
{
    Content: message input
    Type:"Talk"
}
```

然后服务器会把这个消息广播给所有在聊天室里的用户。 
当用户发送图片时，前端将先获取到图片的 base64 码，然后将 base64 码当作文本

发送给后端，具体如下：

```json
{
    Content: base64
    Type:"Picture"
}
```

###### 3、 对服务器的监听 

除了发送消息之外，有很多功能需要前端接受服务器传来的 socket 通信，比如有另一个人进入了用户所在的聊天室，用户可以在界面上收到”xxx 进入了聊天室”的信息，这些就需要我们完成对后端服务器的监听。 后端的监听事件由 ws.onmessage 函数实现，函数首先接受后端发来的 json 文件，其格式为：

```json
{
	Type： Enter / Talk / Picture / Quit, 
	Sender：表示这个事件的主体（如进入房间的人，发消息的人）, Self_send：事件的主体是不是己, 
	Text：内容, 
}
```

首先根据Type 判断发送消息的种类。当是 Talk 或者 Picture 类型时，前端根据self_send 是否为真来呈现信息，这个部分以直接写入 html 文本实现。如果是 Picture 的话还会经历base64 转码成图片的过程。 
当收到Enter 或者Quit 类型的消息时，如果 self_send 为真，那么表示用户进入或者退出了房间，界面会整个的发生改变：聊天界面的显现与消失；左侧功能区界面的改变…如果 self_send 为假，则会在界面上显示”xxx 进入/退出了房间”。这也是通过写入 html 文本实现的。 

###### 三、 后端 

​		后端采用python 的 websocket 编程，主要接收来自前端 js 的json 文件，根据 json中 type 类型的不同，向前端的各个用户发送不同消息。此外，由于与 js 控制的前端进行通讯，需要对 js 首次握手的加密请求进行密钥配对，保证 TCP 连接的安全性.

###### 1、后端连接与加密性握手

​		后端维护三个列表：__connection__、__nicknames、__rooms__，分别代表：与各个用户的通讯 socket 列表、用户昵称列表、用户所在房间列表。 在初始化三个列表后，建立server 的监听socket，利用bind()函数绑定在本地8888 端口，调用listen()函数开始监听。并调用 accept()函数建立新的 socket 与用户端进行通讯。

js 前端在握手时会发送一个具有随机密钥的 GET 请求，为保证 TCP 连接的安全性，需要 python 后端提取其中的密钥，并向前端发送特殊编码后的信息，格式如下：

```python
HANDSHAKE_STRING="HTTP/1.1 101 Switching Protocols\r\n"  \
      "Upgrade:websocket\r\n"\
      "Connection: Upgrade\r\n"  \
      "Sec-WebSocket-Accept: {1}\r\n"  \
      "WebSocket-Location:ws://{2}/chat\r\n"\
      "WebSocket-Protocol:chat\r\n\r\n"
```

Python 后端首先提取GET 请求中的密钥信息，利用base64 解码，替换在上图（2）的位置，最后将这个字符串进行编码，发送给 js 前端。js 前端在接受到该握手信息后，进行密钥匹配，匹配成功后即可完成安全的 TCP 握手过程，并在命令行中发出“xxx 进入房间 xxx” 的提示。

###### 2、后端通讯 

完成握手后，后端为每个客户端开启新线程，开始进行监听。本次开发中，前后端的协议是以 json 的形式，后端接收来自前端的消息，根据 Type 的不同产生不同的行为，并向前端发送固定格式的协议。 

关于消息接收：后端接收到的消息格式如下 :

```json
{
	Content: xxxxx 
	Type: Enter / Talk / Picture / Quit 
}
```

1）当收到 Type 为Enter 的消息时，Content 中的内容为用户进入的房间号，后端遍历所有的用户，如果处在目标房间中，则调用该用户的通讯 socket 向它发送以下格式的信息：

```json
{
	Type： Enter ， 
	Sender：进房间的人, 
	Self_send：1,（事件主体不是自己） Text：, 
}
```

2）当收到 Type 为Quit 的消息时，Content 中的内容为空，后端遍历所有的用户，如果处在目标房间中，则调用该用户的通讯 socket 向它发送以下格式的信息：

```json
{
	Type： Quit ， 
	Sender：谁退出房间了, 
	Self_send：1,（事件主体不是自己） Text：, 
}
```

之后，将对应的通讯 socket 关闭，结束用户线程

3）当收到Type 为Talk/Picture 的消息时，Content 中的内容为发送的消息，后端遍历所有的用户，如果处在目标房间中，则调用该用户的通讯 socket 向它发送以下格式的信息： 

```json
{
	Type： Talk/Picture ， 
	Sender：发送者, 
	Self_send：1（事件主体不是自己） / 0 （事件主体是自己） Text：数据内容, 
}
```

###### 3、 错误处理

后端可能会遇到两种连接错误：非法协议格式和连接断开。

如果遇到非法的协议格式，后端将在命令行中进行提示：

```python
print('[Server] 无法解析json 数据包:', connection.getsockname(), connection.fileno())
```

 如果遇到连接断开，后端将利用 try catch 语句抓到错误状态，并向房间内用户广播信息 xxx 退出房间的信息，同时在命令行中提醒错误状态:

```python
[Server]连接失败：('127.0.0.1',8888) 116
```

之后，将对应的通讯 socket 关闭，结束用户线程。