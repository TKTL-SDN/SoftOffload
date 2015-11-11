#!/usr/bin/python

import math
import json, os
from random import randint

from mininet.node import Node, Controller, OVSSwitch
from mininet.net import Mininet
from mininet.topo import Topo
from mininet.log import lg, info
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.topolib import TreeTopo

class CampusTopo( Topo ):
    """two-level network topo for campus/middle-size orgnization
    multiple access switches -- core switch -- gateway -- internet
    """

    def __init__( self, *args, **params ):
        self.agents = []
        super(CampusTopo, self).__init__( *args, **params )

    def build( self, k=5, n=5, accessBw=5, coreBw=100, gtwBw=1000, coverage=10, 
        **_opts):
        """k: number of access switches
           n: number of hosts per switch
           accessBw: bandwidth between each host and access switch
           coreBw: bandwidth between access switch and core switch
           gtwBw: bandwidth between core switch to gateway/router
        """

        self.k = k
        self.n = n
        self.accessBw = accessBw
        self.coreBw = coreBw
        self.gtwBw = gtwBw

        if n == 1:
            genHostName = lambda i, j: 'h%s' % i
        else:
            genHostName = lambda i, j: 'h%ss%s' % ( j, i )

        coreSwitch = self.addSwitch( 's0' )
        gtw = self.addHost( 'gtw' )
        self.addLink( gtw, coreSwitch, bw=self.gtwBw )

        column = int(math.sqrt(k))
        if column < 1:
            return

        for i in range( 1, k+1 ):
            # add access switch
            agent = {}
            switch = self.addSwitch( 's%s' % i )
            agent['name'] = 'agent%s' % i
            agent['ip'] = '171.0.0.%s' % i
            agent['ssid'] = 'sdntest%s' % i
            # location, start from (0, 0)
            row = (i - 1) / column
            col = (i - 1) % column
            base = (col * coverage * 1.5, row * coverage * 1.5)
            agent['location'] = base
            self.addLink( coreSwitch, switch, bw=self.coreBw )
            # add hosts
            clients = []
            for j in range( 1, n+1 ):
                client = {}
                host = self.addHost( genHostName( i, j ) )
                client['name'] = host
                x = randint(int(base[0] - coverage), int(base[0] + coverage))
                y = randint(int(base[1] - coverage), int(base[1] + coverage))
                dis = distance(base, (x, y))
                tmpBw = self.accessBw
                if dis > 6:
                    tmpBw = int(math.pow(8 / dis, 2) * tmpBw)

                self.addLink( host, switch, bw=tmpBw )
                client['bw'] = tmpBw
                client['location'] = (x, y)
                client['distantce'] = dis
                clients.append(client)

            agent['clients'] = clients
            self.agents.append(agent)

    def getInfo(self):
        return self.agents



def TreeNet( depth=1, fanout=2, **kwargs):
    topo = TreeTopo( depth, fanout )
    return Mininet( topo, **kwargs )

def distance( x, y ):
    return math.sqrt(math.pow(x[0] - y[0], 2) + math.pow(x[1] - y[1], 2))

def createAgentNet( k=5 ):
    net = Mininet( controller=Controller, switch=OVSSwitch )

    print "*** Creating agents and an internal switch"
    sw = net.addSwitch( 's%s' % (k+1) )
    for i in range( 1, k+1 ):
        host = net.addHost( 'agent%s' % i, ip='171.0.0.%s/16' % i )
        net.addLink( sw, host )

    c = net.addController('c1', controller=Controller, ip='127.0.0.1', port=6699)

    root = Node( 'root', inNamespace=False )
    intf = net.addLink( root, sw ).intf1
    root.setIP( '171.0.123.1/16', intf=intf )
    # root.cmd( 'route add -net 171.0.0.0/16 dev ' + str( intf ) )

    net.build()
    c.start()
    sw.start( [ c ] )
    return net

def main( path='info.json', num=5 ):
    lg.setLogLevel( 'info' )

    topo = CampusTopo( k=num )
    info = topo.getInfo()
    
    net = Mininet(topo, link=TCLink)
    for sw in info:
        for clt in sw['clients']:
            host = net[clt['name']]
            clt['ip'] = host.IP()
            clt['mac'] = host.MAC()

    with open(path, 'w') as outfile:
        json.dump(info, outfile)

    net.start()

    
    agentNet = createAgentNet( num )
    # agentNet.start()

    cmd = 'python /home/yfliu/Dev/sdn/mininet/custom/softoffload/udpserver.py'
    for agent in agentNet.hosts:
        agent.cmd( cmd + ' -i ' + agent.IP() + ' &')
        # agent.startService( agent.IP() )

    CLI( agentNet )

    net.stop()
    
    for agent in agentNet.hosts:
        agent.cmd( 'kill %' + cmd )
        # pass
    agentNet.stop()
    
    try:
        print "*** Removing tmp json topo file"
        os.remove(path)
    except OSError:
        print "*** No json topo file found"


if __name__ == '__main__':
    main()