"""
TODO

Copyright 2019 Red Hat, Inc.
Licensed under the GNU General Public License, version 2 as
published by the Free Software Foundation; see COPYING for details.
"""

__author__ = """
jurbanov@redhat.com (Jozef Urbanovsky)
"""

import re
from lnst.Common.ExecCmd import exec_cmd


class OvSInterfaceManager(object):
    def __init__(self):
        self._devices = {}

    # TODO attributes

    def get_devices(self):
        out, _ = exec_cmd("ovs-vsctl list interface", log_outputs=False, die_on_err=False)
        self._devices = out
        # TODO filter regex
        return self._devices

    def assign_name(self, prefix):
        index = 0
        while self._is_name_used(prefix + str(index)):
            index += 1
        return prefix + str(index)

    # TODO bond pair
    def _assign_name_pair(self, prefix):
        index1 = 0
        while self._is_name_used(prefix + str(index1)):
            index1 += 1
        index2 = index1 + 1
        while self._is_name_used(prefix + str(index2)):
            index2 += 1
        return prefix + str(index1), prefix + str(index2)

    def _is_name_used(self, name):
        out, _ = exec_cmd("ovs-vsctl --columns=name list Interface",
                          log_outputs=False, die_on_err=False)
        for line in out.split("\n"):
            m = re.match(r'.*: \"(.*)\"', line)
            if m is not None:
                if name == m.group(1):
                    return True
        return False

    def create_interface(self):
        return
