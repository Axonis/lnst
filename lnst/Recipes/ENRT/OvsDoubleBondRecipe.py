from lnst.Common.Parameters import StrParam
from lnst.Common.IpAddress import ipaddress
from lnst.Controller import HostReq, DeviceReq, RecipeParam
from lnst.Recipes.ENRT.BaseEnrtRecipe import BaseEnrtRecipe
from lnst.Recipes.ENRT.ConfigMixins.CommonHWSubConfigMixin import (
    CommonHWSubConfigMixin)
from lnst.Devices import OvsBridgeDevice


class NoVirtOvSBondRecipe(CommonHWSubConfigMixin, BaseEnrtRecipe):
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
            host.eth0.down()
            host.eth1.down()

            host.br0 = OvsBridgeDevice()

            host.br0.bond_add("bond" + str(i+1), (host.eth0, host.eth1),
                              bond_mode=self.params.bonding_mode,
                              lacp=self.params.lacp_mode)

            host.br0.ip_add(ipaddress(net_addr + "." + str(i+1) + "/24"))
            host.br0.ip_add(ipaddress(net_addr6 + "::" + str(i+1) + "/64"))

            for dev in [host.eth0, host.eth1, host.br0]:
                dev.up()

        configuration = super().test_wide_configuration()
        configuration.test_wide_devices = [host1.br0, host2.br0]

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
                for dev in [host1.br0, host2.br0]
            ])
        ]
        return desc

    def test_wide_deconfiguration(self, config):
        del config.test_wide_devices

        super().test_wide_deconfiguration(config)

    def generate_ping_endpoints(self, config):
        return [(self.matched.host1.br0, self.matched.host2.br0)]

    def generate_perf_endpoints(self, config):
        return [(self.matched.host1.br0, self.matched.host2.br0)]

    def wait_tentative_ips(self, devices):
        def condition():
            return all(
                [not ip.is_tentative for dev in devices for ip in dev.ips]
            )

        self.ctl.wait_for_condition(condition, timeout=5)

    @property
    def mtu_hw_config_dev_list(self):
        return [self.matched.host1.br0, self.matched.host2.br0]

    @property
    def dev_interrupt_hw_config_dev_list(self):
        return [self.matched.host1.eth0, self.matched.host2.eth0]

    @property
    def parallel_stream_qdisc_hw_config_dev_list(self):
        return [self.matched.host1.eth0, self.matched.host2.eth0]
