# SPDX-License-Identifier: GPL-3.0-or-later
import raptorscope


def test_package_has_version():
    assert isinstance(raptorscope.__version__, str)
