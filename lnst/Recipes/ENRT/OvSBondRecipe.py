from lnst.Common.Parameters import StrParam
from lnst.Common.IpAddress import ipaddress
from lnst.Controller import HostReq, DeviceReq, RecipeParam
from lnst.Recipes.ENRT.BaseEnrtRecipe import BaseEnrtRecipe
from lnst.Recipes.ENRT.ConfigMixins.CommonHWSubConfigMixin import (
    CommonHWSubConfigMixin)
from lnst.Devices import OvsBridge


class OvSBondRecipe(CommonHWSubConfigMixin, BaseEnrtRecipe):
    host1 = HostReq()
    host1.eth0 = DeviceReq(label="to_switch", driver=RecipeParam("driver"))
    host1.eth1 = DeviceReq(label="to_switch", driver=RecipeParam("driver"))

    host2 = HostReq()
    host2.eth0 = DeviceReq(label="to_switch", driver=RecipeParam("driver"))
    host2.eth1 = DeviceReq(label="to_switch", driver=RecipeParam("driver"))

    bonding_mode = StrParam(mandatory=True)
    lacp_mode = StrParam(mandatory=True)

    def test_wide_configuration(self):
        host1, host2 = self.matched.host1, self.matched.host2

        net_addr = "192.168.101"
        net_addr6 = "fc00:0:0:0"

        for i, host in enumerate([host1, host2]):

            host.run("modprobe vfio-pci")

            bus0 = host.eth0.bus_info
            bus1 = host.eth1.bus_info

            host.eth0.enable_readonly_cache()
            host.eth1.enable_readonly_cache()

            host.run("driverctl set-override %s vfio-pci" % bus0)
            host.run("driverctl set-override %s vfio-pci" % bus1)

            host.run("driverctl -v list-devices | grep -i vfio-pci")

            dpdk_bridge = OvsBridge()
            dpdk_bridge.set_br(datapath_type="netdev")

            dpdk_bond = dpdk_bridge.init_bond("dpdk_bond", ("dpdk0", "dpdk1"))
            dpdk_bond.set_options(bond_mode="balance-tcp", lacp="active")
            dpdk_bond.set_interface("dpdk0", type="dpdk", options="dpdk-devargs=0000:19:00.0")
            dpdk_bond.set_interface("dpdk1", type="dpdk", options="dpdk-devargs=0000:19:00.1")
            dpdk_bond.exec_bond()

            test_bridge = OvsBridge()




            # assignment of IPs to implicit internal port
            host.test_bridge.ip_add(ipaddress(net_addr + "." + str(i + 1) + "/24"))
            host.test_bridge.ip_add(ipaddress(net_addr6 + "::" + str(i + 1) + "/64"))

            for dev in [host.test_bridge, host.bond_bridge]:
                dev.up()

        configuration = super().test_wide_configuration()
        configuration.test_wide_devices = [host1.bond_bridge, host2.bond_bridge]

        self.wait_tentative_ips(configuration.test_wide_devices)

        return configuration

    def generate_test_wide_description(self, config):
        host1, host2 = self.matched.host1, self.matched.host2
        desc = super().generate_test_wide_description(config)
        desc += [
            "\n".join([
                "Configured {}.{}.ips = {}".format(
                    dev.host.hostid, dev.name, dev.ips
                )
                for dev in config.test_wide_devices
            ]),
            "\n".join([
                "Configured {}.{}.bonds = {}".format(
                    dev.host.hostid, dev.name, dev.bonds
                )
                for dev in [host1.bond_bridge, host2.bond_bridge,
                            host1.test_bridge, host2.test_bridge]
            ]),
            "\n".join([
                "Configured {}.{}.ports = {}".format(
                    dev.host.hostid, dev.name, dev.ports
                )
                for dev in [host1.bond_bridge, host2.bond_bridge,
                            host1.test_bridge, host2.test_bridge]
            ])
        ]
        return desc

    def test_wide_deconfiguration(self, config):
        del config.test_wide_devices

        super().test_wide_deconfiguration(config)

    def generate_ping_endpoints(self, config):
        return [(self.matched.host1.test_bridge, self.matched.host2.test_bridge)]

    def generate_perf_endpoints(self, config):
        return [(self.matched.host1.test_bridge, self.matched.host2.test_bridge)]

    def wait_tentative_ips(self, devices):
        def condition():
            return all(
                [not ip.is_tentative for dev in devices for ip in dev.ips]
            )

        self.ctl.wait_for_condition(condition, timeout=5)

    @property
    def mtu_hw_config_dev_list(self):
        return [self.matched.host1.test_bridge, self.matched.host2.test_bridge]

    @property
    def dev_interrupt_hw_config_dev_list(self):
        return [self.matched.host1.eth0, self.matched.host2.eth0]

    @property
    def parallel_stream_qdisc_hw_config_dev_list(self):
        return [self.matched.host1.eth0, self.matched.host2.eth0]
