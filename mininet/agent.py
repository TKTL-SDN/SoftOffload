import socket, optparse;



if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-p', dest='port', type=int, default=6777)
    parser.add_option('-i', dest='ip', type=str, default='127.0.0.1')
    parser.add_option('-n', dest='name', type=str)

    (options, args) = parser.parse_args();

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((options.ip, options.port))

        while True:
            (data, addr) = s.recvfrom(1024)
            print "*** Message from %s: %s" % (addr, data)
            s.sendto(data, addr)

    except (KeyboardInterrupt, SystemExit):
        print "\n*** Interrupt signal caught, UDP server exited"
        s.close()
        
