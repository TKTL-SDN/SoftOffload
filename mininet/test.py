#!/usr/bin/python

import math
import json
import os
import re
import time
from random import randint
from subprocess import Popen, PIPE

from mininet.node import Node, Controller, OVSSwitch, OVSBridge, RemoteController
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import lg, info
from mininet.cli import CLI
from mininet.link import TCLink

import util

def createAgentNet( k, routeIP ):
    net = Mininet( controller=Controller, switch=OVSBridge )

    print "*** Creating agent network"
    sw = net.addSwitch( 's%s' % (k+1) )
    for i in range( 1, k+1 ):
        host = net.addHost( 'agent%s' % i, ip='171.0.0.%s/16' % i )
        intf = net.addLink( sw, host ).intf2
        if routeIP != '127.0.0.1':
            # host.setHostRoute( routeIP, intf ) # this api does not work!!!
            host.cmd( 'ip route add %s dev %s' % ( routeIP, str( intf ) ) )

    # c = net.addController('c1', controller=Controller, ip='127.0.0.1', port=6699)

    root = Node( 'root', inNamespace=False )
    intf = net.addLink( root, sw ).intf1
    root.setIP( '171.0.123.1/16', intf=intf )
    # root.cmd( 'route add -net 171.0.0.0/16 dev ' + str( intf ) )

    net.build()
    # c.start()
    sw.start( [] )
    return net

def createTestNet( k, n, accessBw=10, coreBw=100, gtwBw=1000, coverage=10, 
                    ctlIP='127.0.0.1' ):
    agents = []

    if n == 1:
        genHostName = lambda i, j: 'h%s' % i
    else:
        genHostName = lambda i, j: 'h%ss%s' % ( j, i )

    print "*** Creating test network"
    net = Mininet( controller=Controller, switch=OVSSwitch, link=TCLink )

    print "*** Adding central controller"
    c0 = RemoteController( 'c0', ip=ctlIP, port=6633 )

    print "*** Adding switches and hosts"
    coreSwitch = net.addSwitch( 's0' )
    gtw = net.addHost( 'gtw' )
    net.addLink( gtw, coreSwitch, bw=gtwBw )

    column = int(math.sqrt(k))
    if column < 1:
        return

    switches = []
    for i in range( 1, k+1 ):
        # add access switch
        agent = {}
        switch = net.addSwitch( 's%s' % i, cls=OVSBridge )
        agent['sw_name'] = 's%s' % i
        agent['name'] = 'agent%s' % i
        agent['ip'] = '171.0.0.%s' % i
        agent['ssid'] = 'sdntest%s' % i
        # location, start from (0, 0)
        row = (i - 1) / column
        col = (i - 1) % column
        base = (col * coverage * 1.5, row * coverage * 1.5)
        agent['location'] = base
        net.addLink( coreSwitch, switch, bw=coreBw )
        # add hosts
        clients = []
        for j in range( 1, n+1 ):
            client = {}
            client[ 'name' ] = genHostName( i, j )
            host = net.addHost( client[ 'name' ] )
            x = randint(int(base[0] - coverage), int(base[0] + coverage))
            y = randint(int(base[1] - coverage), int(base[1] + coverage))
            dis = util.distance(base, (x, y))
            tmpBw = accessBw
            if dis > 6:
                v = int(math.pow(6 / dis, 2) * tmpBw)
                tmpBw = v if v > 0 else 0.5

            net.addLink( host, switch, bw=tmpBw )
            client['bw'] = tmpBw
            client['location'] = (x, y)
            client['distantce'] = dis
            clients.append(client)

        agent['clients'] = clients
        agents.append(agent)
        switches.append(switch)

    print ""
    print "*** Starting test network"
    net.build()
    coreSwitch.start( [ c0 ] )
    for sw in switches:
        sw.start( [] )
    print ""

    return (net, agents)

def getOVSPort( k, s='s0' ):
    # run "ovs-dpctl show" to get port number
    res = {}
    p = Popen(["ovs-dpctl", "show"], stdout=PIPE)
    output, err = p.communicate()
    code = p.returncode
    if code == 0:
        for i in range( 1, k+2 ):
            mstr = ".*port\s(\d+):\s%s-eth%d" % ( s, i )
            m = re.search(mstr, output)
            if m:
                if i == 1:
                    res[ 'gtw' ] = m.group(1)
                else:
                    res[ 'agent%d' % (i - 1) ] = m.group(1)

    return res


def genFloodlightConfig( agents, k, ofIP, bw=1000, apBw=100 ):
    port = getOVSPort( k )
    #print port

    # networks.properties
    netCfg = open( 'networks.properties', 'w' )
    netCfg.write( "OFSwitchIP %s\n" % ofIP )
    netCfg.write( "OutPort %s\n" % port[ 'gtw' ] )  # fixed port to host 'gtw'
    netCfg.write( "BandWidth %s\n" % bw )
    apStr = "AP"
    for agent in agents:
        apStr += " " + agent[ 'ip' ]
    netCfg.write( "%s\n" % apStr )
    netCfg.close()

    # ap.properties
    apCfg = open( 'ap.properties', 'w' )
    count = 0
    for agent in agents:
        count += 1
        apCfg.write( "# AP%s\n" % count )
        apCfg.write( "ManagedIP %s\n" % agent[ 'ip' ] )
        apCfg.write( "SSID %s\n" % agent[ 'ssid' ] )
        apCfg.write( "BSSID %s\n" % agent[ 'bssid' ] )
        apCfg.write( "AUTH wpa|test\n" )
        apCfg.write( "OFPort %s\n" % port[ "%s" % agent[ 'name' ] ])
        apCfg.write("DownlinkBW %s\n\n" % apBw)
    apCfg.close()


def main( path='tmp.json', k=5, n=5, controllerIP='127.0.0.1', 
        ofIP='127.0.0.1' ):
    """main func for simulating agents, clients and tcp traffic
       k:   agent/ap number
       n:   client number on each agent. 
            Now each agent must have the same number of clients
       controllerIP: floodlight controller ip. 127.0.0.1 means it runs locally 
            on the same machine
       ofIP: ovs control ip exposed to the floodlight controller. The ovs switch
            runs on this machine with mininet, so 127.0.0.1 means the floodlight
            controller runs on the same machine
    """

    lg.setLogLevel( 'info' )

    ( net, agents ) = createTestNet( k, n, ctlIP=controllerIP )

    # add missing info to topo, and write it to a json file
    for agent in agents: 
        sw = net[ agent[ 'sw_name' ] ]
        if len(sw.intfNames()) > 1:
            intf = sw.nameToIntf[ agent[ 'sw_name' ] + '-eth1' ]
            agent[ 'bssid' ] = intf.MAC()

        for clt in agent[ 'clients' ]:
            host = net[ clt[ 'name' ] ]
            clt[ 'ip' ] = host.IP()
            clt[ 'mac' ] = host.MAC()
    with open( path, 'w' ) as outfile:
        json.dump( agents, outfile )

    print "*** Starting UDP servers"
    agentNet = createAgentNet( k, routeIP=controllerIP )
    cmd = 'python %s/agent.py' % os.path.dirname(os.path.abspath(__file__))
    pids = []
    for agent in agentNet.hosts:
        pid = agent.popen( cmd + ' -n %s -i %s -o log &' % ( 
                            agent.name, agent.IP() ) )
        pids.append( pid )
        #print cmd + ' -n ' + agent.name + ' -i ' + agent.IP() + ' &'

    # generate config for floodlight
    print "*** Generating config files for floodlight"
    genFloodlightConfig( agents, k, ofIP )
    
    # pause until user's input
    raw_input("*** Pausing, Press Enter to continue...")

    print "*** Generating test traffic"
    filenode = net[ 'gtw' ]
    iperfArgs = 'iperf -p 5001 '
    for host in net.hosts:
        if host.name != 'gtw':
            host.cmd( iperfArgs + '-s &' )
            filenode.cmd( iperfArgs + '-t 15 -c ' + host.IP() + ' &' )
    # repeat
    while True:
        time.sleep(15)
        choice = raw_input("*** Do you want to repeat test ([y]/n)? ")
        if choice.lower() != 'y':
            break

        for host in net.hosts:
            if host.name != 'gtw':
                filenode.cmd( iperfArgs + '-t 15 -c ' + host.IP() + ' &' )


    CLI( agentNet )

    for host in net.hosts:
        if host.name != 'gtw':
            host.cmd( 'killall -9 iperf' )
    net.stop()
    
    for pid in pids:
        pid.terminate()
        # pass
    agentNet.stop()
    
    try:
        print "*** Removing tmp json topo file"
        os.remove(path)
    except OSError:
        print "*** No json topo file found"
    


if __name__ == '__main__':

    main( k=10, n=10, controllerIP='192.168.0.10', ofIP='192.168.0.30' )