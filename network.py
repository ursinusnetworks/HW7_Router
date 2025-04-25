#!/usr/bin/python3

from mininet.net import Mininet
from mininet.node import RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel
import struct
import argparse
import json

def make_network(filename, controller_ip, controller_port):
    """
    Make a network from a JSON file specification

    Parameters
    ----------
    filename: string
        Path to JSON file containing network information
    controller_ip: string
        IP address where the POX controller is running
    controller_port: int
        Port where the pox controller is running
    """
    with open(filename) as fin:
        network_spec = json.load(fin)
    
    ## Step 1: Setup pox controller
    net = Mininet(topo=None, build=False)
    pox_ctrl = net.addController('c0', controller=RemoteController, ip=controller_ip, port=controller_port)

    ## Step 2: Initialize switches and hosts
    ip2router = {}
    ip2hosts = {}
    for i, r in enumerate(network_spec["routers"]):
        num = i+1
        mac = ":".join(["%.2x"%x for x in struct.pack("!Q", num)[2:]])
        subnet = r["ip"].split("/")[-1]
        router = net.addSwitch(f"s{num}", mac=mac)
        ip2router[r["ip"]] = router
        ip2hosts [r["ip"]] = []
        for h in r["hosts"]:
            ip = f"{h["ip"]}/{subnet}"
            host = net.addHost(h["name"], ip=ip, mac=h["mac"])
            net.addLink(router, host)
            ip2hosts[r["ip"]].append(host)

    ## Step 3: Setup links between switches
    for [r1, r2] in network_spec["links"]:
        print("Linking", r1, ",", r2)
        r1 = ip2router[r1]
        r2 = ip2router[r2]
        net.addLink(r1, r2)
    net.build()

    ## Step 4: Add controllers to switches
    for r in ip2router.values():
        r.start([pox_ctrl])

    ## Step 5: Setup default routes for hosts
    for r_ip, hosts in ip2hosts.items():
        for h in hosts:
            h.cmd(f"route add default gw {r_ip.split("/")[0]}")
    
    ## Step 6: Run command line interface until it's closed
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    parser = argparse.ArgumentParser()
    parser.add_argument("--filename", type=str, required=True, help="Path to JSON file containing network information")
    parser.add_argument("--controller_ip", type=str, default="127.0.0.1", help="Path to IP running pox controller")
    parser.add_argument("--controller_port", type=int, default=6633, help="Port that the pox controller is using")
    
    opt = parser.parse_args()
    make_network(opt.filename, opt.controller_ip, opt.controller_port)