In this file we illustrate how to use mininet and our test.py to simulate softoffload agents and clients

## Requirements

* latesd mininet installed, source code on [github](https://github.com/mininet/mininet)

## Test Instruction

* config ip addresses for both of the simulating machine and remote controller (if your are using a remote controller)

* run test.py with appropriate arguments in main()

* when test.py pauses for the first time, copy/move files "ap.properties" and "networks.properties" to the resource folder of your floodlight controller ([your-floodlight]/src/main/resources), and re-compile your floodlight with "ant"

* enable ip_forwarding and proxy_arp on the simulating machine

* start floodlight

* continue test.py by press "enter"

## Example Config

Here we show setting-up steps we are using for a remote controller, the topo looks like this:

    192.168.0.30/24    192.168.0.10/24
              eth0     eth2
      mininet <-----------> floodlight
  

* now we are using 171.0.0.0/16 for simulating agents (you could edit it anyway), so we need to first edit routing tables on the floodlight controller

  ```
  # eth2 is the interface we are using on the floodlight controller
  ip route add 171.0.123.1 dev eth2
  ip route add default via 171.0.123.1
  ```



* enable ip_forwarding and proxy_arp on the mininet machine

    ```
    # root-eth0 is the virtual interface we use by default
    echo 1 > /proc/sys/net/ipv4/ip_forwarding
    echo 1 > /proc/sys/net/ipv4/conf/root-eth0/proxy_arp
    ```






