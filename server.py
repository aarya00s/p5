import socket
import struct
import threading
import time
import sys
#convert py dict to string
import json
#client class
from router import RouterClass
#send the data to diffrent router as the system is decentralized by using multicast
ip_address = ['224.1.1.1','224.1.1.2']
port0 = 33007
#set time to live value as 1 by default to send data in LAN itself
ttl = 1
#diffrent drones and routers to transmit information
port1 = 33008
port2 = 33009
port3 = 33010
ip_primary = '224.1.1.5'
network = True

class drone:
    #initilaize dictionary 
    data_sent = {}
    data_collect = {}
    droneTimestampList = {}
    droneName = ""
    #provide id to each drone
    def setdroneName(self, name):
        self.droneName = name
    #initalize value
    def __init__(self, host, port, hostname, p2p):
        self.host = host
        self.hostname = hostname
        self.port = port
        self.ip_address = ip_address[int(p2p) - 1]
        #unisocket used to create a one to one transmission bw drone and router
        self.unisock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #creating socket with ipv4 protocol
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        
        #to write information in kernel 
        self.sentsock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        #create interface between socket and object server
        self.receivesock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    #error handle
    def error(self):
        #no. of drones
        drone_connected = 10
        #nearest drone
        for i in list(self.data_collect):
            drone_id = i[4:]
            if int(drone_id) < drone_connected:
                drone_connected = int(drone_id)
                
        start_new = "drone" + str(drone_connected)
        #connect to nearest drone
        if self.droneName == start_new:
            self.setdroneName("root")
            print("drone", drone_connected, " is new root")
        
    def recieve (self):
        self.sentsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if network:
            # in this port recive all data
            self.sentsock.bind(('', port2))
        else:
            # in this port recive only data to ip_address
            self.sentsock.bind((self.ip_address, port2))
        #multicast
        req = struct.pack("4sl", socket.inet_aton(self.ip_address), socket.INADDR_ANY)
        self.sentsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)

        while True:
            data, addr = self.sentsock.recvfrom(10240)
            recieve_data = data.decode("utf-8")
            k = json.loads(recieve_data)
            for key in k:   
                curr = self.data_sent[key]
                data_load = k[key]
                data_load[1] = data_load[1]+1  
                
                if key == self.droneName:
                    continue                 # same drone continue 
                if key in self.data_sent:    # If key is present in data_sent
                    
                    if curr[1] > data_load[1]:    
                        self.data_sent[key] = data_load 
                    else:                    
                        self.data_sent[key] = data_load
            
    def recieve_data(self):
        while(True):
            for drone in self.data_collect:
                values = self.data_collect[drone]
                self.data_sent[drone] = values
                print("Recieve New Drone :: ", self.data_sent)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            dict_json = json.dumps(self.data_sent)
            self.sock.sendto(dict_json.encode('utf-8'), (self.ip_address, port2))
            time.sleep(30)

    def sender(self):
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if network:
            self.sock.bind(('', port0))
        else:
            self.sock.bind((self.ip_address, port0))

        req = struct.pack("4sl", socket.inet_aton(self.ip_address), socket.INADDR_ANY)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)

        while True:
            data, addr = self.sock.recvfrom(10240)
            droneName = data.decode("utf-8")
            self.droneTimestampList[droneName] = time.time()
            if addr not in list(self.droneTimestampList):
                self.data_collect[droneName] = list()
                values = [addr, 1]
                self.data_collect[droneName].extend(values)
                
            detail = self.data_collect[droneName]

    def sender_data(self):
        hostname = socket.gethostname()
        host = socket.gethostbyname(hostname)
        sensorobj = RouterClass(host, port1)
        while True:
            sensorobj.getData()

    def process_data(self):
        self.unisock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.unisock.bind((self.hostname, port1))

        while True:
            data, _ = self.unisock.recvfrom(10240)
            if self.droneName == "root":
                self.check_if_fire(data)

    def check_if_fire(self, data):
        check_data = data.decode("utf-8")
        if (check_data[:14] == "Recieved Data"):
            if( check_data.find('FIRE') != -1 ):
                # Alert incase of fire
                alert = "!!!! \n FIRE ALERT!!!!!!!  ----------- \n !!!!!!"
                self.receivesock.sendto(alert.encode("utf-8"), (ip_primary, port3))
        else:
            print(check_data)
    # communication across the network using getway
    def drone_network(self):
        if self.droneName == "root":

            self.receivesock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if network:
                self.receivesock.bind(('', port3))
            else:
                self.receivesock.bind((ip_primary, port3))

            req = struct.pack("4sl", socket.inet_aton(ip_primary), socket.INADDR_ANY)
            self.receivesock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, req)

            while True:
                data, _ = self.receivesock.recvfrom(10240)
                print(data.decode('utf-8'))    

    def start(self, droneName):
        self.setdroneName(str(sys.argv[1]))
        
        network = threading.Thread(target=self.drone_network)
        network.setDaemon(True)
        network.start()
        sendThread = threading.Thread(target=self.sender)
        sendThread.setDaemon(True)
        sendThread.start()
        checkThread = threading.Thread(target=self.process_data)
        checkThread.setDaemon(True)
        checkThread.start()
        send_dataThread = threading.Thread(target=self.drone_to_drone)
        send_dataThread.setDaemon(True)
        send_dataThread.start()
        time.sleep(5)
        recieveThread = threading.Thread(target=self.recieve )
        recieveThread.setDaemon(True)
        recieveThread.start()
        recieve_dataThread = threading.Thread(target=self.recieve_data)
        recieve_dataThread.setDaemon(True)
        recieve_dataThread.start()
        dataThread = threading.Thread(target=self.sender_data)
        dataThread.setDaemon(True)
        dataThread.start()

    def drone_to_drone(self):
        while(True):
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
            self.sock.sendto(self.droneName.encode('utf-8'), (self.ip_address, port0))
            time.sleep(30)

    def drone_to_router(self, message, droneName):
        unisock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        record = self.data_sent[droneName]
        ip_addr = record[0]
        unisock.sendto(message, ip_addr)

def main():
    hostname = socket.gethostname()
    host = socket.gethostbyname(hostname)
    p2p = sys.argv[2].replace('network', '')
    
    if(not p2p.isdigit() or not int(p2p) in (1,2)):
        print("Error")
        exit(1)

    d = drone(host, port0, hostname, p2p)
    
    d.start(str(sys.argv[1]))

    while True:
        pass
    
if __name__ == '__main__':
    main()
    

