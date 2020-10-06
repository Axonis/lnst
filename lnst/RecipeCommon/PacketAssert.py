import signal
from lnst.Controller.Recipe import BaseRecipe
from lnst.Tests import PacketAssert
from lnst.Common.LnstError import LnstError

class PacketAssertConf(object):
    """
    Class for the configuration of the :any:`PacketAssert` class

    :param host: client in :any:`PingConf` object used to specify host for the ping test
    :param iface: interface to be used by the tcpdump
    :param p_filter: tcpdump's pcap filter expression to be matched
    :param grep_for: regex to be matched in the string representation of a
    packet in the tcpdump output
    :param p_min: minimum count of the packets to be found in the dump
    :param p_max: maximum count of the packets to be found in the dump
    :param promiscuous: toggle of promiscuous mode
    """
    def __init__(self, host, iface, **kwargs):
        self._host = host
        self._iface = iface
        self._p_filter = kwargs.get("p_filter", '')
        self._grep_for = kwargs.get("grep_for", [])
        self._p_min = kwargs.get("p_min", 10)
        self._p_max = kwargs.get("p_max", 0)
        self._promiscuous = kwargs.get("promiscuous", False)

    @property
    def host(self):
        return self._host

    @property
    def iface(self):
        return self._iface

    @property
    def p_filter(self):
        return self._p_filter

    @property
    def grep_for(self):
        return self._grep_for

    @property
    def p_min(self):
        return self._p_min

    @property
    def p_max(self):
        return self._p_max

    @property
    def promiscuous(self):
        return self._promiscuous

class PacketAssertTestAndEvaluate(BaseRecipe):
    """
    This class provides an extension to BaseRecipe class to perform an
    evaluation of the captured packets on an interface. The class uses
    :any:`PacketAssert` test module to capture the packets based on the filters
    defined in :any:`PacketAssertConf` configuration. The pass or fail
    decision is made upon whether the number of the captured packets
    matching the criteria fits the min/max interval defined through
    :any:`PacketAssertConf`.
    """
    started_job = None

    def packet_assert_test_start(self, packet_assert_config):
        """
        Method starts a :any:`PacketAssert` job and stores ***started_job*** attribute
        containing LNST :any:`Job: object.

        :param packet_assert_config: configuration in a form of :any:`PacketAssertConf`
        class
        """
        if self.started_job:
            raise LnstError("Only 1 packet_assert job is allowed to run at a time.")

        host = packet_assert_config.host
        kwargs = self._generate_packet_assert_kwargs(packet_assert_config)
        packet_assert = PacketAssert(**kwargs)
        self.started_job = host.prepare_job(packet_assert).start(bg=True)

    def packet_assert_test_stop(self):
        """
        Method kills a process executing :any:`PacketAssert` job and
        resets the value of the ***started_job*** attribute.

        :return: result of the packet assert job
        """
        if not self.started_job:
            raise LnstError("No packet_assert job is running.")

        self.started_job.kill(signal=signal.SIGINT)
        self.started_job.wait()
        result = self.started_job.result
        self.started_job = None
        return result

    def packet_assert_evaluate_and_report(self, packet_assert_config, results):
        """
        Method evaluates the result of the packet assert job based on the
        received packets.

        :param packet_assert_config: configuration containing values crucial to
        the evaluation process
        :param results: object where results are stored
        """
        if results["p_recv"] >= packet_assert_config.p_min and \
            (results["p_recv"] <= packet_assert_config.p_max or
             not packet_assert_config.p_max):
            self.add_result(True, "Packet assert succesful", results)
        else:
            self.add_result(False, "Packet assert unsuccesful", results)

    def _generate_packet_assert_kwargs(self, packet_assert_config):
        kwargs = dict(interface=packet_assert_config.iface)

        if packet_assert_config.p_filter:
            kwargs["p_filter"] = packet_assert_config.p_filter

        if packet_assert_config.grep_for:
            kwargs["grep_for"] = packet_assert_config.grep_for

        if packet_assert_config.promiscuous:
            kwargs["promiscuous"] = packet_assert_config.promiscuous

        return kwargs
