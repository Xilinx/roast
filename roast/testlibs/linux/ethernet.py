#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import time
import functools
import logging
from roast.utils import *  # pylint: disable=unused-wildcard-import
from roast.xexpect import Xexpect

log = logging.getLogger(__name__)


class Ethernet:

    attributes = [
        "hostIp",
        "targetIp",
        "ping_intervel",
        "ping_size",
        "ping_count",
        "file_size",
        "pktgen_size",
        "pktgen_count",
        "pktgen_burst",
        "pktgen_delay",
        "pktgen_frags",
        "pktgen_vlan_id",
        "host_interface",
        "ifupdwn_count",
        "mtu",
        "eth_interface",
        "user",
        "password",
        "iperf_binary",
        "extra_iperf_args",
    ]

    targetIp = "10.10.70.101"
    hostIp = "10.10.70.21"
    ping_intervel = "1"
    ping_size = "45"
    ping_count = "10"
    file_size = "4096"
    pktgen_size = "200"
    pktgen_count = "1"
    pktgen_burst = "1"
    pktgen_delay = "0"
    pktgen_frags = "4"
    pktgen_vlan_id = "0"
    eth_interface = "eth0"
    host_interface = "enp9s0"
    updown_count = "3"
    mtu = "1500"
    udp_mtu = "1500"
    iperf_binary = "iperf"
    extra_iperf_args = ""
    timeout = "60"
    user = ""
    password = ""

    def __init__(self, config, terminal, eth_interface):
        self.config = config
        self.terminal = terminal
        self.log = log
        self.eth_interface = eth_interface
        self.terminal.prompt = "~# "
        self.terminal._setup_init()
        if config["user"]:
            self.user = config["user"]
        if config["password"]:
            self.password = config["password"]

    def _setip_config(self, config):
        self.config = config

    def eth_default_runner(func):
        @functools.wraps(func)
        def override_defaults(self, **kwargs):
            ts = time.time()
            self.log.info(f"Start ethernet test {func.__name__} ...")
            for attr, value in kwargs.items():
                if attr not in self.attributes:
                    raise ValueError("Attribute [{}] not supported.".format(attr))
                else:
                    setattr(self, attr, value)
                    self.log.info(f"key: {attr}, value: {value}")
            func(self, **kwargs)
            te = time.time()
            self.log.info(
                f"Ethernet test {func.__name__} end .. Total time taken:{round((te -ts),1)}, sec"
            )
            self.__init__(self.config, self.terminal, self.eth_interface)
            return True

        return override_defaults

    @eth_default_runner
    def ping_test(self, **kwargs):

        cmd = f"ping {self.targetIp} -s {self.ping_size} -c {self.ping_count}"
        self.terminal.runcmd(cmd=str(cmd), timeout=20, expected=" 0% packet loss")

    @eth_default_runner
    def eth_speed(self, **kwargs):
        import random

        for speed in [1000, 10, 100]:
            cmd = f"ethtool -s {self.eth_interface} speed {speed} duplex full"
            self.terminal.runcmd(cmd=cmd, timeout=30, expected="link")
            self.terminal.sendline("\r\n")
            self.terminal.runcmd(cmd=f"ethtool {self.eth_interface}")
            self.ping_test()
        cmd = f"ethtool -s {self.eth_interface} autoneg on"
        self.terminal.runcmd(cmd=cmd, timeout=30, expected="link")
        self.terminal.sendline("\r\n")
        self.terminal.runcmd(cmd=f"ethtool {self.eth_interface}")
        self.ping_test()

    @eth_default_runner
    def ifupdown(self, **kwargs):
        for count in self.updown_count:
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} down", timeout=15, expected="root"
            )
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} up;sleep 3",
                timeout=15,
                expected="root",
                expected_failures="link is not ready",
            )
            self.ping_test()

    @eth_default_runner
    def ifplugd(self, **kwargs):
        cmd = f'pgrep -f ifplugd >/dev/null || echo "ifplugd demon not running"'
        self.terminal.runcmd(
            cmd=cmd, timeout=30, expected_failures=["ifplugd demon not running"]
        )
        self.ifupdown()
        cmd = f"ifconfig {self.eth_interface} {self.hostIp} netmask 255.255.255.0"
        self.terminal.runcmd(cmd=cmd, timeout=self.timeout)

    @eth_default_runner
    def eth_tftp(self, **kwargs):
        failures = [
            "server error:",
            "(2) Access violation",
            "No such file or directory",
            "ERROR",
        ]
        cmd_list = [
            "tftp_file=$(mktemp tftp.XXXXXX)",
            f"dd if=/dev/zero of=$tftp_file bs=1 count=0 seek={self.file_size}",
        ]
        self.terminal.runcmd_list(
            cmd_list=cmd_list, timeout=30, expected_failures=failures
        )
        self.run_on_host(cmd="chmod 777 -R /tftpboot/")

        cmd_list = [
            f"tftp -p -r $tftp_file {self.targetIp}",
            "file1=$(md5sum $tftp_file | awk '{print $1}')",
            "rm $tftp_file",
        ]
        self.terminal.runcmd_list(
            cmd_list=cmd_list, timeout=300, expected_failures=failures
        )
        self.run_on_host(cmd="chmod 777 -R /tftpboot/")
        cmd_list = [
            f"tftp -g -r $tftp_file {self.targetIp}",
            "file2=$(md5sum $tftp_file | awk '{print $1}')",
            "[ $file1 == $file2 ] || return 1",
        ]
        self.terminal.runcmd_list(
            cmd_list=cmd_list, timeout=300, expected_failures=failures
        )
        self.run_on_host(cmd="rm -rf /tftpboot/tftp*")

    @eth_default_runner
    def eth_nfs(self, **kwargs):
        self.log.info("Output test files and clean up..")
        cmd_list = [
            "out_dir=/tmp/nfs_temp_output",
            "mkdir -p ${out_dir} > /dev/null 2>&1",
            "out_prefix=${out_dir}/nfs_test",
            "out_mount=${out_prefix}.mount",
            "out_mount_prefix=${out_mount}/nfs_test",
            "unmount ${out_mount} && rm -rf ${out_prefix}*",
        ]

        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=60)

        self.log.info("Mounting NFS...")
        cmd_list = [
            "mkdir -p ${out_mount}",
            f'rpcinfo "{self.targetIp}" | grep "nfs"',
            f"mount -o port=2049,nolock,proto=tcp,vers=2 {self.targetIp}:/exports/root $out_mount",
        ]
        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=200)

        self.log.info("Creating large pattern data files..")
        cmd_list = [
            " [ -c /dev/urandom ] || mknod -m 777 /dev/urandom c 1 9 > /dev/null 2>&1;",
            "dd if=/dev/urandom of=${out_prefix}.r2m-pattern.bin bs=1024 count=4096;",
            "dd if=/dev/urandom of=${out_mount_prefix}.m2r-pattern.bin bs=1024 count=4096;",
            "cp ${out_mount_prefix}.m2r-pattern.bin ${out_prefix}.m2r-pattern.bin;",
            "cp ${out_prefix}.r2m-pattern.bin ${out_mount_prefix}.r2m-pattern.bin;",
        ]

        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=200)
        self.log.info("Re-mounting the NFS.. Verifying the read back data...")
        cmd_list = [
            "umount ${out_mount};",
            f"mount -o port=2049,nolock,proto=tcp,vers=2 {self.targetIp}:/exports/root $out_mount;"
            "diff -q ${out_prefix}.m2r-pattern.bin ${out_mount_prefix}.m2r-pattern.bin",
            "diff -q ${out_mount_prefix}.r2m-pattern.bin ${out_prefix}.r2m-pattern.bin",
        ]
        self.terminal.runcmd_list(cmd_list=cmd_list, timeout=200)

    @eth_default_runner
    def eth_scp(self, **kwargs):
        cmd_list = [
            "scp_file=$(mktemp scp.XXXXXXXXX)",
            f"dd if=/dev/zero of=$scp_file bs=1 count=0 seek={self.file_size}",
            f'expect -c "spawn scp -r $scp_file {self.user}@{self.targetIp}:/home/{self.user}/;expect "password"; send "{self.password}"; interact"',
            "file1=$(md5sum $scp_file | awk '{print $1}') && rm $scp_file",
            f'expect -c "spawn scp {self.user}@{self.targetIp}:/home/{self.user}/$scp_file ./;expect "password:"; send "{self.password}"; interact"',
            "file2=$(md5sum $scp_file | awk '{print $1})'",
            "[ $file1 == $file2 ] || echo 'scp test failed'",
        ]
        self.terminal.runcmd_list(
            cmd_list=cmd_list, timeout=120, expected_failure=["scp test failed"]
        )

    @eth_default_runner
    def eth_telnet(self, **kwargs):
        self.terminal.runcmd(cmd="telnetd", timeout=20)
        self.test_host_console = Xexpect(
            hostname=self.config["eth_host_name"],
            non_interactive=False,
            log=log,
        )
        self.test_host_console.runcmd(
            cmd=f"telnet {self.hostIp}",
            timeout=20,
            expected="Peta",
            wait_for_prompt=False,
        )
        self.test_host_console.sendline("root")
        self.test_host_console.sendline("root")
        time.sleep(1)
        self.test_host_console.sendline("root")
        self.test_host_console.runcmd(
            cmd=f"ls", timeout=20, expected=":~# ", wait_for_prompt=False
        )

    @eth_default_runner
    def eth_dhcp(self, **kwargs):
        cmd = f"udhcp -i {self.eth_interface}"
        self.terminal.runcmd(cmd=cmd, timeout=30, expected_failures=["not found"])
        self.ping_test()

    @eth_default_runner
    def iperf_test(self, **kwargs):
        self.log.info("Starting an iperf server on the host...")
        cmd = f"{self.iperf_binary} -s &"
        self.run_on_host(cmd=cmd, timeout=50)
        time.sleep(3)
        self.terminal.runcmd(
            cmd=f"tftp -g -r {self.iperf_binary} {self.targetIp}", timeout=60
        )
        self.terminal.runcmd(
            cmd=f"chmod 777 {self.iperf_binary}; mv {self.iperf_binary} /usr/sbin/",
            timeout=60,
        )
        time.sleep(3)
        self.log.info(f"Measuring {self.iperf_binary} TCP throughput...")
        cmd = f"{self.iperf_binary} -c {self.targetIp} -f m {self.extra_iperf_args}"
        self.terminal.runcmd(cmd=cmd, timeout=60)
        time.sleep(3)
        self.log.info(f"Measuring {self.iperf_binary} UDP throughput...")
        cmd = f"{self.iperf_binary} -c {self.targetIp} -f m -u {self.extra_iperf_args}"
        self.terminal.runcmd(cmd=cmd, timeout=60)
        self.log.info(f"Running {self.iperf_binary} with option -d | --dualtest ....")
        cmd = f"{self.iperf_binary} -c {self.targetIp} -f m -d {self.extra_iperf_args}"
        self.terminal.runcmd(cmd=cmd, timeout=60)
        time.sleep(3)
        self.run_on_host(cmd=f"pkill {self.iperf_binary}", timeout=50)
        self.log.info(f"Starting an {self.iperf_binary} server on the target...")
        # self.terminal.runcmd(cmd="tftp -g -r {self.iperf_binary} {self.targetIp}",timeout=60)
        self.terminal.runcmd(cmd=f"{self.iperf_binary} -s &", timeout=60)
        time.sleep(3)
        self.log.info(f"Starting an iperf client on the host...")
        self.run_on_host(
            cmd=f"{self.iperf_binary} -c {self.hostIp} -f m {self.extra_iperf_args}",
            timeout=50,
        )
        time.sleep(3)

    def run_on_host(
        self, cmd, expected="root", timeout=60, expected_failures=None, **kwargs
    ):
        self.test_host_console = Xexpect(
            hostname=self.config["eth_host_name"],
            non_interactive=False,
            log=log,
        )
        if cmd == "gettest_hostmac":
            self.test_host_console.runcmd(
                cmd="ifconfig enp9s0 | awk '/HWaddr {print substr($5,1)}'", timeout=30
            )
            self.targetMac = self.test_host_console.output()
        self.test_host_console.runcmd(cmd="sudo su -", timeout=timeout, expected="root")
        if type(cmd) is list:
            self.test_host_console.runcmd_list(
                cmd_list=f"{cmd}",
                expected_failures=expected_failures,
                timeout=timeout,
                expected=expected,
            )
        else:
            self.test_host_console.runcmd(
                cmd=f"{cmd}",
                expected=expected,
                timeout=timeout,
                expected_failures=expected_failures,
            )

    @eth_default_runner
    def netperf(self, **kwargs):
        failures = ["No space left on device", "recv_response:"]
        cmd = f"ps -ef | grep netserver || netserver -D -4 &"
        self.terminal.runcmd(cmd=cmd, timeout=20)
        if self.mtu != "1500":
            time.sleep(2)
            self.log.info(f"Updating MTU size on host and device... : {self.mtu}")
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu {self.mtu} up; ifconfig"
            )
            time.sleep(3)
            self.run_on_host(
                cmd=f"ifconfig {self.host_interface} down; ifconfig {self.host_interface} mtu {self.mtu} up; ifconfig"
            )
            self.udp_mtu = f"{self.mtu} - 28"
            time.sleep(3)
        self.log.info(
            f"Device Netperf Output for TCP(Tx Mode) with MTU size {self.mtu}"
        )
        time.sleep(1)
        cmd = f"netperf -c -C -H {self.targetIp} -t TCP_STREAM"
        self.terminal.runcmd(cmd=cmd, expected_failures=failures, timeout=50)
        time.sleep(3)
        self.log.info(
            f"Device Netperf Output for UDP(Tx Mode) with MTU Size: {self.mtu}"
        )
        time.sleep(1)
        cmd = f"netperf -c -C -H {self.targetIp} -t UDP_STREAM"
        self.terminal.runcmd(cmd=cmd, timeout=50)
        time.sleep(3)
        cmd = f"ps -ef | grep netserver"
        self.run_on_host(cmd=cmd, timeout=50)
        time.sleep(1)
        self.log.info(f"Host Netperf Output for TCP(Rx Mode) with MTU size: {self.mtu}")
        cmd = f"netperf -c -C -H {self.hostIp} -t TCP_STREAM -- -m {self.mtu} -M {self.mtu}"
        self.run_on_host(cmd=cmd, expected_failures=failures, timeout=50)
        time.sleep(3)
        self.log.info(
            f"Host Netperf Output for UDP(Rx Mode) with MTU Size: {self.udp_mtu}"
        )
        cmd = f"netperf -c -C -H {self.hostIp} -t UDP_STREAM -- -m {self.mtu} -M {self.udp_mtu}"
        self.run_on_host(cmd=cmd, timeout=50)
        time.sleep(2)

    @eth_default_runner
    def vlan_test(self, **kwargs):
        cmd = "board_mac=$(ifconfig eth0 | awk '/HWaddr {print substr($5,1)}')"
        self.terminal.runcmd(cmd=cmd, timeout=60)
        self.BoardMac = self.terminal.output()
        time.sleep(2)
        self.log.info(f"Board HWaddr : {self.BoardMac}... ")
        cmd = 'tcpdump -i {self.eth_interface} "vlan and icmp" and ip host 10.10.70.2 and ether host "$board_mac" -n -ev &'
        self.terminal.runcmd(cmd=cmd, timeout=60)
        time.sleep(2)
        cmd_list = [
            "ip link set dev eth2.5 down &",
            "ip link del eth2.5 &",
            "modprobe 8021q &",
            "ip link add link eth2 name eth2.5 type vlan id 5 &",
            "ip addr add 10.10.70.2 brd 10.10.70.255 dev eth2.5 &",
            "ip link set dev eth2.5 up &",
            f"arp -s {self.hostIp} $board_mac dev eth2.5 &",
            f"{self.hostIp} -I eth2.5 -c 3 &",
        ]
        self.run_on_host(cmd=cmd_list, timeout=120)
        time.sleep(10)
        self.log.info("=================== rx output ===================")
        self.terminal.runcmd(cmd="killall -s INT tcpdump &", timeout=60)
        time.sleep(2)
        cmd_list = [
            "ip link set dev eth2.5 down &",
            "ip link del eth2.5 &",
            f"route del {self.hostIp} &",
            f"route add {self.hostIp} dev eth2 &",
            f"tcpdump -n -i eth2 dst port 9 and ip host {self.hostIp} -e -v > ~/tx_tcpdump_vlan.txt &",
        ]
        self.run_on_host(cmd=cmd_list, timeout=120)
        time.sleep(10)
        self.run_on_host(cmd="gettest_hostmac", timeout=20)
        time.sleep(1)
        commands = [
            "echo 'stop' > /proc/net/pktgen/pgctrl",
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_0",
            "echo 'add_device eth0' > /proc/net/pktgen/kpktgend_0",
            "echo 'count 1' > /proc/net/pktgen/eth0",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0",
            "echo 'pkt_size 200' > /proc/net/pktgen/eth0",
            "echo 'delay 0' > /proc/net/pktgen/eth0",
            "echo 'frags 4' > /proc/net/pktgen/eth0",
            "echo 'vlan_id 0' > /proc/net/pktgen/eth0",
            "echo 'vlan_p 0' > /proc/net/pktgen/eth0",
            "echo 'vlan_cfi 0' > /proc/net/pktgen/eth0",
            f"echo 'dst {self.targetIp}' > /proc/net/pktgen/eth0",
            f"echo 'dst_mac {self.targetMac}' > /proc/net/pktgen/eth0",
            "echo 'start' > /proc/net/pktgen/pgctrl",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(4)
        self.log.info("=================== tx output ===================")
        cmd_list = [
            "killall -s INT tcpdump &",
            "cat ~/tx_tcpdump_vlan.txt",
            "rm ~/tx_tcpdump_vlan.txt",
        ]
        self.run_on_host(cmd=cmd_list, timeout=120)
        time.sleep(10)

    @eth_default_runner
    def ping_flood(self, **kwargs):
        self.terminal.runcmd(cmd=f"tftp -g -r ping 10.10.70.101; chmod 777 ping")
        self.terminal.runcmd(
            cmd=f"./ping -f {self.hostIp} -i 5 -c 5",
            timeout=60,
            expected=" 0% packet loss",
        )
        self.terminal.runcmd(
            cmd=f"ping {self.targetIp} -c 5", timeout=30, expected=" 0% packet loss"
        )

    @eth_default_runner
    def ping_jumbo_frame(self, **kwargs):
        for mtu in [2048, 4096, 8192]:
            self.log.info(f"Updating MTU size on device... : {mtu}")
            self.terminal.runcmd(
                cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu {mtu} up; ifconfig"
            )
            time.sleep(2)
            self.log.info(f"Updating MTU size on test host... : {mtu}")
            self.run_on_host(
                cmd=f"ifconfig {self.host_interface} down; ifconfig {self.host_interface} mtu {mtu} up; ifconfig"
            )
            time.sleep(2)
            self.run_on_host(
                cmd=f"ping {self.hostIp} -l {mtu-28} -c 5",
                timeout=30,
                expected=" 0% packet loss",
            )
            time.sleep(2)
        self.terminal.runcmd(
            cmd=f"ifconfig {self.eth_interface} down; ifconfig {self.eth_interface} mtu 1500 up; ifconfig"
        )
        time.sleep(3)
        self.run_on_host(
            cmd=f"ifconfig {self.host_interface} down; ifconfig {self.host_interface} mtu {mtu} up; ifconfig"
        )

    @eth_default_runner
    def eth_pktgen(self, **kwargs):
        self.run_on_host(cmd="gettest_hostmac", timeout=20)
        commands = [
            "echo 'stop' > /proc/net/pktgen/pgctrl",
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_0",
            f"echo 'add_device {self.eth_interface}' > /proc/net/pktgen/kpktgend_0",
            f"echo 'count {self.pktgen_count}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'clone_skb 100' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'pkt_size {self.pktgen_size}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'burst {self.pktgen_burst} > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'delay {self.pktgen_delay}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'vlan_id {self.pktgen_vlan_id}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'vlan_p 0' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'vlan_cfi 0' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'frags {self.pktgen_frags}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'dst {self.targetIp}' > /proc/net/pktgen/{self.eth_interface}",
            f"echo 'dst_mac {self.targetMac}' > /proc/net/pktgen/{self.eth_interface}",
            "echo 'start' > /proc/net/pktgen/pgctrl",
            f"cat /proc/net/pktgen/{self.eth_interface}",
            "paramsCount=$(grep -E 'Params: count' /proc/net/pktgen/eth0 | awk '{print substr($3,1)}')",
            "pktSofar=$(grep -E 'pkts-sofar' /proc/net/pktgen/eth0 | awk '{print substr($2,1)}')",
            '[ "$paramsCount" -eq "$pktSofar" ] || echo "fail"',
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)

    @eth_default_runner
    def eth_pqueue(self, **kwargs):
        self.run_on_host(cmd="gettest_hostmac", timeout=20)
        self.run_on_host(cmd="killall -s INT tcpdump &", timeout=20)
        self.run_on_host(cmd="rm ~/priority.txt &", timeout=20)
        self.run_on_host(
            cmd=f"tcpdump -n -i {self.host_interface} ip host {self.targetIp} -ev > ~/priority.txt &",
            timeout=20,
        )
        time.sleep(5)
        self.log.info(f"targetMac = {self.targetMac}")
        commands = [
            "echo 'stop' > /proc/net/pktgen/pgctrl",
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_0",
            "echo 'add_device eth0@0' > /proc/net/pktgen/kpktgend_0",
            "echo 'count 500' > /proc/net/pktgen/eth0@0",
            "echo 'burst 50' > /proc/net/pktgen/eth0@0",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@0",
            "echo 'pkt_size 1500' > /proc/net/pktgen/eth0@0",
            "echo 'delay 0' > /proc/net/pktgen/eth0@0",
            "echo 'frags 0' > /proc/net/pktgen/eth0@0",
            f"echo 'dst {self.targetIp}' > /proc/net/pktgen/eth0@0",
            f"echo 'dst_mac {self.targetMac}' > /proc/net/pktgen/eth0@0",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@0",
            "echo 'queue_map_min 0' > /proc/net/pktgen/eth0@0",
            "echo 'queue_map_max 0' > /proc/net/pktgen/eth0@0",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        commands = [
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_1",
            "echo 'add_device eth0@1' > /proc/net/pktgen/kpktgend_1",
            "echo 'count 20' > /proc/net/pktgen/eth0@1",
            "echo 'burst 20' > /proc/net/pktgen/eth0@1",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@1",
            "echo 'pkt_size 1400' > /proc/net/pktgen/eth0@1",
            "echo 'delay 0' > /proc/net/pktgen/eth0@1",
            "echo 'frags 0' > /proc/net/pktgen/eth0@1",
            f"echo 'dst {self.targetIp}' > /proc/net/pktgen/eth0@1",
            f"echo 'dst_mac {self.targetMac}' > /proc/net/pktgen/eth0@1",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@1",
            "echo 'queue_map_min 1' > /proc/net/pktgen/eth0@1",
            "echo 'queue_map_max 1' > /proc/net/pktgen/eth0@1",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        commands = [
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_2",
            "echo 'add_device eth0@2' > /proc/net/pktgen/kpktgend_2",
            "echo 'count 500' > /proc/net/pktgen/eth0@2",
            "echo 'burst 50' > /proc/net/pktgen/eth0@2",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@2",
            "echo 'pkt_size 1200' > /proc/net/pktgen/eth0@2",
            "echo 'delay 0' > /proc/net/pktgen/eth0@2",
            "echo 'frags 0' > /proc/net/pktgen/eth0@2",
            f"echo 'dst {self.targetIp}' > /proc/net/pktgen/eth0@2",
            f"echo 'dst_mac {self.targetMac}' > /proc/net/pktgen/eth0@2",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@2",
            "echo 'queue_map_min 0' > /proc/net/pktgen/eth0@2",
            "echo 'queue_map_max 0' > /proc/net/pktgen/eth0@2",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        commands = [
            "echo 'rem_device_all' > /proc/net/pktgen/kpktgend_3",
            "echo 'add_device eth0@3' > /proc/net/pktgen/kpktgend_3",
            "echo 'count 20' > /proc/net/pktgen/eth0@3",
            "echo 'burst 20' > /proc/net/pktgen/eth0@3",
            "echo 'clone_skb 0' > /proc/net/pktgen/eth0@3",
            "echo 'pkt_size 1100' > /proc/net/pktgen/eth0@3",
            "echo 'delay 0' > /proc/net/pktgen/eth0@3",
            "echo 'frags 0' > /proc/net/pktgen/eth0@3",
            f"echo 'dst {self.targetIp}' > /proc/net/pktgen/eth0@3",
            f"echo 'dst_mac {self.targetMac}' > /proc/net/pktgen/eth0@3",
            "echo 'skb_priority 1' > /proc/net/pktgen/eth0@3",
            "echo 'queue_map_min 1' > /proc/net/pktgen/eth0@3",
            "echo 'queue_map_max 1' > /proc/net/pktgen/eth0@3",
            "echo 'start' > /proc/net/pktgen/pgctrl &",
        ]
        self.terminal.runcmd_list(cmd_list=commands, timeout=60)
        time.sleep(5)
        self.run_on_host(cmd="killall -s INT tcpdump &", timeout=20)
        self.run_on_host(cmd="cat ~/priority.txt &", timeout=20)
