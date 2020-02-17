import re

from lnst.Common.ExecCmd import exec_cmd
from lnst.Slave.OvsInterfaceManager import OvSInterfaceManager


class OvsBond(object):
    def __init__(self, init_cmd):
        self._cmd = init_cmd

    def set_interface(self, interface, **kwargs):
        options = ""
        for opt_name, opt_value in kwargs.items():
            if opt_name == "options":
                options += f" {opt_name}:{opt_value}"
            else:
                options += f" {opt_name}={opt_value}"

        set_if = f" -- set Interface {interface} {options}"
        self._cmd += set_if

    def set_options(self, **kwargs):
        options = ""
        for opt_name, opt_value in kwargs.items():
            options += f" {opt_name}={opt_value}"

        self._cmd += options

    def exec_bond(self):
        exec_cmd(self._cmd)


class OvsBridge(object):
    _name_template = "t_ovsbr"
    _command = "ovs-vsctl"

    def __init__(self, **kwargs):
        if "name" not in kwargs:
            kwargs["name"] = OvSInterfaceManager.assign_name(self._name_template)
        self.name = kwargs["name"]
        self._type_init()
        self._create()

    @classmethod
    def _type_init(cls):
        exec_cmd("systemctl start openvswitch.service")

    def _create(self):
        exec_cmd(f"ovs-vsctl add-br {self.name}")

    def destroy(self):
        exec_cmd(f"ovs-vsctl del-br {self.name}")

    def set_br(self, **kwargs):
        options = ""
        for opt_name, opt_value in kwargs.items():
            options += " %s=%s" % (opt_name, opt_value)

        exec_cmd(f"ovs-vsctl set bridge {self.name} {options}")

    def init_bond(self, bond_name, devices):
        dev_names = " ".join(devices)
        return OvsBond(f"ovs-vsctl add-bond {self.name} {bond_name} {dev_names}")

    def _get_port_info(self):
        numbered_ports = {}
        port_lines = []

        dumped_ports = exec_cmd("ovs-ofctl dump-ports-desc %s" %
                                self.name, log_outputs=False)[0]

        for match in re.finditer(r'(\w+)\((\w*)\)',
                                 dumped_ports):
            numbered_ports[match.groups()[1]] = match.groups()[0]

        ovs_show = exec_cmd("ovs-vsctl show",
                            log_outputs=False)[0]
        regex = r'(Port[\w\W]*?)(?=Port|ovs_version)'

        for match in re.finditer(regex, ovs_show):
            line = match.groups()[0].replace('\n', ' ')
            line = self._port_format(line)
            port_lines.append(line)

        return numbered_ports, port_lines

    @property
    def ports(self):
        numbered_ports, port_lines = self._get_port_info()
        ports = {}

        for line in port_lines:
            if not re.search('type=', line):
                self._line_to_port_number(line, numbered_ports, ports)

        return ports

    @staticmethod
    def _port_format(line):
        res = re.sub(r":", "", line)
        res = re.sub(r"(\S[^,])\s(\S)", "\\1=\\2", res)
        res = re.sub(r"\s{2,}(?=\S)", ", ", res)
        res = re.sub(r"\s*$", "", res)

        return res

    @staticmethod
    def _line_to_port_number(line, ref, result):
        name = re.match(r"Port=\"(\w+)\"", line)

        try:
            number = ref[name]
            result[number] = line
        except KeyError:
            pass
