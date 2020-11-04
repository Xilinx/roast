#
# Copyright (c) 2020 Xilinx, Inc. All rights reserved.
# SPDX-License-Identifier: MIT
#

from hwflow import PROJECT
from hwflow_configs.boards import tenzing, se1


def main():
    proj = PROJECT("versal_3bram")

    proj.output.extend(["xsa", "bit"])
    proj.vivado_mode = "batch"
    proj.auto_addr_assign = 1
    proj.lsf = True

    tenzing.config_proj(proj)

    ps = proj.add_ip("CIPS")
    tenzing.config_ps(ps)
    se1.config_ps(ps)

    # PL IP's
    bram_ctrl_0 = proj.add_ip("AXI_BRAM_CTRL")
    bram_ctrl_0.data_width = 128

    bram_ctrl_1 = proj.add_ip("AXI_BRAM_CTRL")
    bram_ctrl_1.data_width = 128

    bram_ctrl_2 = proj.add_ip("AXI_BRAM_CTRL")
    bram_ctrl_2.data_width = 128

    mem_0 = proj.add_ip("EMB_MEM_GEN")
    mem_0.memory_type = "True_Dual_Port_RAM"
    mem_0.memory_primitive = "URAM"

    mem_1 = proj.add_ip("EMB_MEM_GEN")
    mem_1.memory_type = "True_Dual_Port_RAM"
    mem_1.memory_primitive = "URAM"

    mem_2 = proj.add_ip("EMB_MEM_GEN")
    mem_2.memory_type = "True_Dual_Port_RAM"
    mem_2.memory_primitive = "BRAM"

    # CONNECTIONS
    e0 = proj.connect(ps, bram_ctrl_2.s_axi)
    e1 = proj.connect(ps.ps_noc_cci0, bram_ctrl_0.s_axi)
    e2 = proj.connect(ps.ps_noc_cci0, bram_ctrl_1.s_axi)
    e3 = proj.connect(bram_ctrl_0.bram_porta, mem_0.bram_porta)
    e4 = proj.connect(bram_ctrl_0.bram_portb, mem_0.bram_portb)
    e5 = proj.connect(bram_ctrl_1.bram_porta, mem_1.bram_porta)
    e6 = proj.connect(bram_ctrl_1.bram_portb, mem_1.bram_portb)
    e7 = proj.connect(bram_ctrl_2.bram_porta, mem_2.bram_porta)
    e8 = proj.connect(bram_ctrl_2.bram_portb, mem_2.bram_portb)

    proj.generate_tcl()

    proj.run_vivado()


if __name__ == "__main__":
    main()
