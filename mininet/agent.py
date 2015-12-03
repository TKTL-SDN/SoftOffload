#!/usr/bin/python

import os, sys
import socket
import optparse
import json
import datetime

import util


class Agent:
    """class representation for agent info"""

    def __init__(self, data, *args, **kwargs):
        self.ip = data['ip']
        self.location = data['location']
        self.name = data['name']
        self.clients = data['clients']
        self.ssid = data['ssid']
        self.bssid = data['bssid']

    def has_client(self, mac):
        return mac.lower() in self.get_all_clt_mac()

    def get_all_clt_mac(self):
        """return all clients' mac addresses as a list"""
        res = []
        for each in self.clients:
            res.append(each['mac'])
        return res

    def gen_clt_info(self, mac):
        """return a string for this mac address"""
        res = ""
        mac = mac.lower()
        for clt in self.clients:
            if clt['mac'].lower == mac:
                res = "client|" + mac + "|" + clt['ip'] + "/n"
                break

        return res

    def gen_all_clt_info(self):
        """return a string list containing all client info, 
        one str for one client"""
        res = []

        for clt in self.clients:
            res.append("client|" + clt['mac'] + "|" + clt['ip'])

        return res

    def get_client_location(self, mac):
        for clt in self.clients:
            if clt['mac'].lower() == mac.lower():
                return clt['location']

    def gen_signal_levels(self, mac, data):
        if not self.has_client(mac):
            return ""

        clt_pos = self.get_client_location(mac)
        res = "scan|%s|static" % mac
        for each in data:
            if each.has_key('bssid'):
                ssid = each['ssid']
                bssid = each['bssid']
                pos = each['location']
                dis = util.distance(clt_pos, pos)
                if dis <= 5:
                    level = -int(dis * 10)
                elif dis > 5 and dis <= 10:
                    level = -int(50 + dis * 2)
                elif dis > 10 and dis <= 13:
                    level = -int(40 + dis * 3)
                else:
                    level = -int(dis * 6 + 2)
                    if level < -95:
                        continue

                res += '|%s&%s&%s' % (ssid, bssid, level)

        return res


def convert_byte_str_to_mac(byte_str):
    res = ""
    mac = [element.encode('hex') for element in byte_str]
    for each in mac:
        res += each if res == "" else ":" + each

    return res

def get_current_time():
    return str(datetime.datetime.now())


if __name__ == '__main__':
    path = os.path.dirname(os.path.abspath(__file__))

    parser = optparse.OptionParser()
    parser.add_option('-p', dest='port', type=int, default=6777)
    parser.add_option('-i', dest='ip', type=str, default='127.0.0.1')
    parser.add_option('-n', dest='name', type=str)
    parser.add_option('--path', dest='path', type=str, default=path)
    parser.add_option('-f', dest='file', type=str, default='tmp.json')

    (options, args) = parser.parse_args();

    log_tag = "[%s]" % options.name

    print "*** [%s]%s Reading topo info..." % (get_current_time(), log_tag)
    with open(options.path + '/' + options.file) as data_file:
        topo = json.load(data_file)

    info = []
    for each in topo:
        if each['name'] == options.name:
            info = each
            break
    else:
        print "*** [%s]%s No topo info found, exiting" % (get_current_time(), log_tag)
        sys.exit(-1)

    agent = Agent(data=info)

    try:
        print "*** [%s]%s Starting UDP server..." % (get_current_time(), log_tag)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((options.ip, options.port))

        while True:
            (data, addr) = s.recvfrom(1024)
            res_addr = (addr[0], 26284)
            if data[0] == 'a':
                print ("*** [%s]%s Message from %s: %s" % (get_current_time(),
                        log_tag, addr, data.rstrip()))
                cmd = data[1:3]
                if cmd == 'ck':
                    mac = convert_byte_str_to_mac(data[4:11])
                    s.sendto(agent.gen_clt_info(mac), res_addr)
                elif cmd == 'rp':
                    print ("*** [%s]%s Report all client info" % 
                            (get_current_time(), log_tag))
                    msgs = agent.gen_all_clt_info()
                    for each in msgs:
                        s.sendto(each, res_addr)
            elif data[0] == 'c':
                mac = convert_byte_str_to_mac(data[1:7])
                if agent.has_client(mac):
                    fields = data[7:].split('|')
                    cmd = fields[0].lower()
                    print ("*** [%s]%s Message from %s: c%s%s" 
                        % (get_current_time(), log_tag, addr, mac, cmd))
                    if cmd == 'app':
                        print ("*** [%s]%s Report app info" 
                            % (get_current_time(), log_tag))
                        s.sendto('app|' + mac + '|download', res_addr)
                    elif cmd == 'scan':
                        print ("*** [%s]%s Report signal info" 
                            % (get_current_time(), log_tag))
                        scan_res = agent.gen_signal_levels(mac, topo)
                        if scan_res != "":
                            print ("*** [%s]%s Sent signal info to master" 
                                % (get_current_time(), log_tag))
                            s.sendto(scan_res, res_addr)


    except (KeyboardInterrupt, SystemExit):
        print "\n*** Interrupt signal caught, UDP server exited"
        s.close()
        
