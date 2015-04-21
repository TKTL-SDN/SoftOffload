# SoftOffload

SoftOffload is an SDN-based mobile traffic offloading framework. It runs on a custom [Floodlight controller](https://github.com/TKTL-SDN/SoftOffload-Master) with our extensions on [Click modular routers](https://github.com/TKTL-SDN/SoftOffload-Agent) and [mobile devices](https://github.com/TKTL-SDN/SoftOffload-Client). It not only explores the feasibility of context-based traffic offloading, but also provides a platform for designing and implementing a centralized traffic management in wireless networks.

## Requirements

* For the **agent/AP**: a monitor device/interface on the wireless channel is required.

* For the **end-device**: currently only Android platform is supported.

* For the **system**: OpenFlow-supported switches.

## Usage

Building SoftOffload implies building the SoftOffload master, agents, and clients respectively.

If you clone SoftOffload from this repository, please pull every submodules recersively:

    $ git clone --recursive https://github.com/TKTL-SDN/SoftOffload

### SoftOffload Master

You can find a separated [instruction](https://github.com/TKTL-SDN/SoftOffload-Master) on how to build and run the master.

The master shall be run on a central server that has IP reachability to all APs and OF switches in the system. Before running your master, please first check the configuration files in the "[resources](https://github.com/TKTL-SDN/SoftOffload-Master/blob/eit-sdn/src/main/resources)" folder, and make sure the settings are matched with your network.

Our offloading module is called `net.floodlightcontroller.mobilesdn`, and it has been already included in `floodlight.modules` in the example Floodlight system configuration [floodlightdefault.properties](https://github.com/TKTL-SDN/SoftOffload-Master/blob/eit-sdn/src/main/resources/floodlightdefault.properties). We explain our key parameters in this configuration file as follows:

* `mobilesdn.Master.masterPort`: this is the UDP communication port to SoftOffload agent. It shall be the same as the one used in the [agent configuration file](https://github.com/TKTL-SDN/SoftOffload-Agent/tree/eit-sdn/conf/local-agent).

* `mobilesdn.Master.ofMonitorInterval`: this parameter is used to adjust the traffic monitoring interval on OpenFlow switches. 2 means the interval is 2 seconds.

* `mobilesdn.Master.ofMonitorMaxNum`: how many monitoring turns are required for triggering offloading.

* `mobilesdn.Master.apConfig`: this shall point to a apConfig file, which is required for traffic offloading. An example apConfig file is given in the `src/main/resources/ap.properties`. `ManagedIP` is the reachable IP address of the local agent running on the AP, `AUTH` is the authentication method and corresponding password (like "open", "wpa|your_password"). OFPort is port which this AP connects to the OF switch. `DownlinkBW` is the downstream bandwidth in Mbps.

    ```
    # AP1
    ManagedIP 192.168.3.30
    SSID sdntest
    BSSID 9c:d3:6d:10:a9:b8
    AUTH wpa|testeitsdn
    OFPort 2
    DownlinkBW 16

    # AP2 only for test
    ManagedIP 192.168.1.21
    SSID sdntest1
    BSSID 90:94:e4:07:ad:0f
    AUTH wpa|testeitsdn
    OFPort 3
    DownlinkBW 80
    ```

* `mobilesdn.Master.networkFile`: this shall point to a network topology file. An example file is given in the `src/main/resources/networks.properties` and shown below. In our system, a network slice is defined by the OFswitch outport. If two APs are using the same access switch outport, they are considered as in the same network slice. `BandWidth` is the total downstream bandwidth for this switch outport in Mbps.

    ```
    # Network-1
    # OFSwitchMAC 00:12:3f:22:45:66
    OFSwitchIP 192.168.10.125
    OutPort 1
    BandWidth 2
    AP 192.168.3.30 192.168.1.21
    ```

* other: `mobilesdn.Master.enableCellular` is not used in our current implementation, you may leave this unchanged.


**To build and run the master**:

```
$: cd SoftOffload-Master
$: ant
$: java -jar floodlight.jar
```

### SoftOffload Agent

#### Build the agent

    $ git clone https://github.com/TKTL-SDN/SoftOffload-Agent.git
    $ cd SoftOffload-Agent

    # our current agent does not support kernel mode
    # you may choose to disable linux kernel mode to speed up the building

    $ ./configure --enable-wifi --enable-local (--disable-linuxmodule)
    $ make

#### Generate custom configuration for your system

Change agent configuration [agent.click](https://github.com/TKTL-SDN/SoftOffload-Agent/tree/eit-sdn/conf/local-agent) for your system.

We provide a script to help you generate suitable config file quickly for your system.

```
$ cd SoftOffload-Agent/conf/local-agent/

# read our help instruction on parameter setting    
$ ./agent-config-generator.py -h

# run the script with suitable arguments to generate config file
$ ./agent-config-generator.py [your args...] > agent.click
```

You can find instruction about parameters with this script when you run it, or you can use `-h` to check help info.


#### Run

    # run Click in the userlevel
    sudo ./userlevel/click conf/local-agent/agent.click


### SoftOffload Client

A more detailed instruction can be found [here](https://github.com/TKTL-SDN/SoftOffload-Client).

* Build our application on your Android devices (4.0+), or install our sample apk file.

* Switch on the "SDN CONTROLLING". This enables our application to react as a SoftOffload client, response requests sent from the controller.


**Now connect clients to local agents, and the controller will trigger offloading based on system traffic loads**

## References
