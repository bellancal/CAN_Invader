import socket
import argparse

'''
General program used for communicating with the active server sockets.
This program will invoke a socket to transfer the required data
All commands invoke this program first to parse and send the data to via socket.
Generic syntax is  python pynetcat.py host port data
'''
parser = argparse.ArgumentParser(description='define and parse the cli for socket server')
parser.add_argument("host")
parser.add_argument("port")
parser.add_argument("data")
args = parser.parse_args()


def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    s.sendall(content)
    s.shutdown(socket.SHUT_WR)
    while 1:
        data = s.recv(1024)
        if data == bytes("", "utf-8"):
            break
        print("Received:", repr(data))
    print("Connection closed.")
    s.close()
    exit()

netcat(args.host, int(args.port), bytes(args.data, "utf-8"))
