#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

import pytest
from roast.component.relay import Relay


def test_relay_interface(mocker):
    r = Relay(relay_type=None)
    assert isinstance(r, Relay)
    r.disconnect()
    assert r.driver.disconnected == True
    r.connect()
    assert r.driver.connected == True
    r.reconnect(7)
    assert r.driver.reconnected == True
    assert r.driver.seconds == 7
