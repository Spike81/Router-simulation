# !/usr/local/bin/python3
# @Time : 2021/1/15 17:14
# @Author : Tianlei.Shi
# @Site : Suzhou
# @File : main.py
# @Software : PyCharm

'''Summary of project here.

An application for simulate the routing process using Python Socket network programming
based on the Bellman-Ford distance vector algorithm

Attributes:
    :buffer_size: the size of udp receive buffer
    :recorded_client: this variable will record the IP and port of node that can be received by server
    :all_cwd: this variable will store all files now in current work directory
    :prefix_path: the prefix path of current work directory
    :result_routing_table: this variable is used to store final result
    :server_port: this variable is used to store the IP and port of this node

'''


# import all relevant libraries
import threading
import time
import json
import os
import socket
import getopt
import sys


# initialize all global variables
buffer_size = 1024  # the size of udp receive buffer
recorded_client = []  # this variable will record the IP and port of node that is first pass in
sent_client = {}  # this variable will store IP and port of node that is sent by client
all_cwd = []  # this variable will store all files now in current work directory
prefix_path = ""  # the prefix path of current work directory
result_routing_table = {}  # this variable is used to store final result
server_port = []  # this variable is used to store the IP and port of this node



class call_server(threading.Thread):

    '''Summary of class here.

    Used to start server method with multithreading

    '''

    def __init__(self):

        '''Summary of method here.

        Instantiation this class

        '''

        threading.Thread.__init__(self)

    def run(self):

        '''Summary of method here.

        Run the server of udp, and make it always-on

        '''

        while True:  # make the server is always-on
            udp_server()  # call the server of udp


def udp_server():

    '''Summary of method here.

    This is the server of udp, it accepts messages and files from its neighbor nodes

    '''

    own_node = (server_port[0], server_port[1])  # get IP and port of this node
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # use udp protocol to connection
    server.bind(own_node)  # listen itself

    global recorded_client  # record the IP and port of node that can be received

    while True:  # always-on server

        information, ip_port = server.recvfrom(buffer_size)  # receive information and IP and port of node from other node

        if (recorded_client == []):  # if no node sent before
            node = information.decode()  # get node name of send node
            print('node name of send node:', node)
            server.sendto(b'node_check', ip_port)  # respond to node, let it continue
            recorded_client = [node, ip_port]  # record this node, reject other node

        elif (ip_port == recorded_client[1]):  # if received node is recorded node
            size_file = information  # restore information
            file_size = int(size_file.decode())  # get the size of file that will be sent
            rece_size = 0  # size of file that received

            server.sendto(b'size_check', ip_port)  # respond to node, let it continue

            node = recorded_client[0]  # node that recorded
            file = prefix_path + "/" + node + "_routing_table_rec.json"  # generate a file to store the sending file

            f = open(file, "wb")  # write this file

            while rece_size < file_size:  # if file not received completed
                if file_size - rece_size > 1024:  # if file size is bigger than 1024 kb, split it to block of 1024 kb
                    size = 1024
                else:  # the last packet less than 1024
                    size = file_size - rece_size  # receive it all

                recv_data, ip_port = server.recvfrom(size)  # receive information and IP and port of node from other node

                if (ip_port == recorded_client[1]):  # if received node is recorded node
                    rece_size += len(recv_data)  # summarize file length
                    f.write(recv_data)  # write file
                else:  # if received information no from recorded node
                    while ip_port != recorded_client[1]:  # repeat to receive until receive message from recorded node
                        server.sendto(b'no_suit', ip_port)  # if not recorded node, tell it do not send following
                        recv_data, client_addr = server.recvfrom(size)  # receive again
                    rece_size += len(recv_data)  # summarize file length
                    f.write(recv_data)  # write file
            else:  # if file received completed
                f.close()  # close file writer
                server.sendto(b'file-ack', ip_port)  # tell node end connection

                recorded_client = []  # clear recorded_client to record new first passed in node
        else:
            server.sendto(b'no_suit', ip_port)  # if not recorded node, tell it do not send following


def client(node, key, ip_port):

    '''Summary of method here.

    This is the client of udp, it sends messages and files to its neighbor nodes

    '''

    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # udp connection

    try:  # make sure no error if other node offline
        client.sendto(node.encode('utf-8'), ip_port)  # send node name firstly, encode with utf-8
        data, server_addr = client.recvfrom(buffer_size)  # receive respond
        print('message %s received from neighbor %s' % (data, server_addr))

        if data != b'no_suit':  # if this node is recorded
            pathname = prefix_path + "/" + node + "_routing_table.json"  # find the routing table file

            f = open(pathname, "rb")  # read file
            size = os.stat(pathname).st_size  # get size of file
            client.sendto(str(size).encode(), ip_port)  # send the size of routing table file to neighbor node
            data, server_addr = client.recvfrom(buffer_size)  # receive respond
            print('message %s received from neighbor %s' % (data, server_addr))

            for line in f:
                client.sendto(line, ip_port)  # sends routing table file to neighbor node
            f.close()  # close file processer

            data, server_addr = client.recvfrom(buffer_size)  # receive respond
            print('message %s received from neighbor %s' % (data, server_addr))
            client.close()  # end this connection

            global sent_client  # global variable sent_client
            sent_client[key] = ip_port  # put this send succeed node into sent_client
    except:
        client.close()  # if any problem appear, end this connection


class Bellman_Ford_Graph():  # implementation of Bellman-Ford algorithm

    '''Summary of class here.

    This is the implementation of Bellman-Ford algorithm, call this class can calculate the shortest path

    '''

    def __init__(self):

        '''Summary of method here.

        Instantiation this class

        '''

        self.vertices = {}  # vertices of graph
        self.edges = []  # edges of graph

    def addEdge(self, start, end, dist):

        '''Summary of method here.

        Add edges for graph

        :arg:
            start: the start vertice of edge in graph
            end: the end vertice of edge in graph
            dist: the distance (or weight) of this edge

        '''

        self.edges.extend([[start, end, dist], [end, start, dist]])  # add edge into graph

    def getVertices(self):

        '''Summary of method here.

        return all vertices in graph

        :return:
            all_vertices: all vertices in graph

        '''

        all_vertices = set(sum(([edge[0], edge[1]] for edge in self.edges), []))

        return all_vertices

    def printSolution(self, dist, predecessor):

        '''Summary of method here.

        Get the shortest path of specified node

        :arg:
            dist: all distance of graph
            predecessor: the predecessor vertice of specified node

        '''

        for v in self.vertices:  # whole path
            if v != self.src:  # if not itself
                path = self.getPath(predecessor, v)  # get the shortest path
                result_routing_table[v] = {"distance": dist[v], "next_hop": path[1]}  # get final result

    def getPath(self, predecessor, s_n):

        '''Summary of method here.

        Get the whole shortest path of specified node

        :arg:
            predecessor: the predecessor vertice of specified node
            v: specified node

        :return:
            path: whole path of specified node

        '''

        pred = predecessor[s_n]  # predecessor vertice of specified node
        path = []  # store shortest path
        path.append(s_n)  # append predecessor vertice

        # find the shortest path in reverse order, then reverse
        while (pred!= None):  # find all predecessor vertice
            path.append(pred)  # append predecessor vertice
            pred = predecessor[pred]  # find the predecessor vertice of predecessor vertice
        path.reverse()  # reverse

        return path

    def bellmanFord(self, src):

        '''Summary of method here.

        Implementation of the Bellman-Ford algorithm

        :arg:
            src: the specified node that need to be solved

        '''

        self.src = src  # specified node
        self.vertices = self.getVertices()  # get all vertices
        dist = {v: sys.maxsize for v in self.vertices}  # distance between vertices
        dist[src] = 0  # all distance of specified vertice
        predecessor = {v: None for v in self.vertices}  # predecessor vertices

        # core of algorithm
        for i in range(len(self.vertices)-1):  # Traverse the n-1 times
            for edge in self.edges: # Loosen all edges
                if dist[edge[0]] + edge[2] < dist[edge[1]]:
                    dist[edge[1]] = dist[edge[0]] + edge[2]
                    predecessor[edge[1]] = edge[0]

        self.printSolution(dist, predecessor)  # get result


def Bellman_Ford_calculater(node):

    '''Summary of method here.

    The starter of the Bellman-Ford algorithm

    :arg:
        node: the specified node that need to be solved

    '''

    graph = Bellman_Ford_Graph()  # instantiated object

    final_distance = prefix_path + "/" + node + "_routing_table.json"  # get all routing table info
    f = open(final_distance, "rb")  # read file
    final_distance = json.load(f)  # convert json to dict

    # add all node and distance info into Bellman-Ford graph
    for key in final_distance.keys():
        for i in final_distance[key]:
            graph.addEdge(key, i, final_distance[key][i])  # add edge

    graph.bellmanFord(node)  # find the shortest path of node

    global result_routing_table  # global variable result_routing_table

    result_routing_table = json.dumps(result_routing_table)  # convert dict to json
    pathname = prefix_path + "/" + node + "_output.json"  # generate the ouput.json file

    with open(pathname, 'w', encoding='utf-8') as f:
        f.write(result_routing_table)  # write file

    pathname = prefix_path + "/" + node + "_output.json"  # output.json
    f = open(pathname, "rb")  # read file
    result = json.load(f)  # convert json to dict
    print("the content of %s_output.json: %s" % (node, result))


def controller(node):

    '''Summary of method here.

    Control all process of this application

    :arg:
        node: node name of this program

    '''

    cwd_files = [f for f in os.listdir(prefix_path)]  # find all files in current work directory
    for i in cwd_files:
        if ".json" in i:  # only need json file
            all_cwd.append(i)  # put file into list
    print("files in current work directory:", all_cwd)  # print all files in current work directory

    filename = prefix_path + "/" + node + "_ip.json"  # read ip file of node
    f = open(filename)
    ip_file = json.load(f)  # read ip and port of itself and neighbors

    global server_port  # global variable server_port
    server_port = ip_file[node]  # get ip and port of itself
    print("ip and port of this node:", server_port)

    # start the server of udp by multithreading
    s = call_server()
    s.start()

    # generate routing table according distance file
    pathname = prefix_path + "/" + node + "_distance.json"
    f = open(pathname, "rb")  # read distance file
    distance = json.load(f)

    routing_table = {}  # store all routing table info
    routing_table[node] = distance  # put info from distance file into dict
    routing_table = json.dumps(routing_table)
    pathname = prefix_path + "/" + node + "_routing_table.json"  # routing table file

    with open(pathname, 'w', encoding='utf-8') as f:
        f.write(routing_table)  # write file

    send_flag = 1  # to judge if client need to send again

    while send_flag == 1:

        filename = prefix_path + "/" + node + "_ip.json"  # ip file
        f = open(filename)
        ip_file = json.load(f)  # read content of ip file

        global send_dict, sent_client  # global variable send_dict and sent_client

        send_dict = ip_file  # let send_dict has all neighbors' ip and port
        del send_dict[node]  # delete itself
        print("neighbors of this node is:", send_dict)

        time.sleep(10)  # wait for other node start

        while len(send_dict) != 0:  # if still some neighbor not receive the routing table

            # send routing table to neighbors according to send_dict
            for key, value in send_dict.items():
                value = (value[0], value[1])  # gei neighbor's ip and port
                client(node, key, value)  # start client to send

            # if some neighbor is received, remove it from send_dict
            if len(sent_client) != 0:
                for key in sent_client.keys():
                    del send_dict[key]  # remove from send_dict
                sent_client.clear()  # clear sent_client, avoid to delete again

        time.sleep(20)  # wait other nodes receive routing table completed

        cwd_file_update = []  # file list of current work directory after update
        all_files = [f for f in os.listdir(prefix_path)]  # find all files in current work directory
        for i in all_files:
            if "_routing_table_rec.json" in i:  # find all received routing table
                if not (node + "_routing_table_rec.json" in i):  # except own routing table
                    cwd_file_update.append(i)  # put file into cwd_file_update

        pathname = prefix_path + "/" + node + "_routing_table.json"  # get own routing table
        f = open(pathname, "rb")  # read file
        own_routing_table = json.load(f)  # convert json to dict

        local_flag = 0  # represent if the own routing table be changed

        for i in cwd_file_update:  # compare all received routing table with own routing table
            pathname = prefix_path + "/" + i  # received routing table
            f = open(pathname, "rb")  # read file
            distance = json.load(f)
            print("content of received routing table:", distance)

            # compare received routing table with own routing table
            for key in distance.keys():  # only compare key is enough
                if key in own_routing_table:  # if own routing table have
                    pass
                else:  # if own routing table do not have
                    own_routing_table[key] = distance[key]  # add new distance into own routing table
                    local_flag = 1  # own routing table have changed

        # if no changed to own routing table, no need to send routing table again
        if local_flag == 0:
            send_flag = 0

        # if have changed to own routing table, client must to send new own routing table
        if local_flag == 1:

            own_routing_table = json.dumps(own_routing_table)  # generate new own routing table
            pathname = prefix_path + "/" + node + "_routing_table.json"  # new own routing table

            with open(pathname, 'w', encoding='utf-8') as f:
                f.write(own_routing_table)  # write new own routing table

        pathname = prefix_path + "/" + node + "_routing_table.json"  # new own routing table
        f = open(pathname, "rb")  # read file
        distance = json.load(f)  # convert json to dict
        print("routing table after update:", distance)

    Bellman_Ford_calculater(node)  # calculate the shortest path of this node

    print("please wait for program over...\n")
    time.sleep(100)  # wait all file is transmit completed
    delete_list = []  # store files that need to be deleted
    all_file = [f for f in os.listdir(prefix_path)]  # find all files in current work directory
    for i in all_file:
        if "_routing_table" in i:  # only routing table file need to be deleted
            delete_list.append(i)  # put superfluous file in list

    # delete all superfluous file
    for i in delete_list:
        pathname = prefix_path + "/" + i
        os.remove(pathname)  # delete file

    print("program is over")



# get parameter from user
opts, args = getopt.getopt(sys.argv[1:], "hp:i:", ["node="])

# global variables: the name of node of this program
node = opts[0][1]
print("the name of this node is", node)

# find the prefix path of current work directory
realpath = os.path.realpath(sys.argv[0]).split("/")
for i in range(1, len(realpath) - 1):
    prefix_path += "/" + realpath[i]

controller(node)  # start this application