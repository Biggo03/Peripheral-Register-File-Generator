#!/usr/bin/env python3
from openpyxl import load_workbook
from jinja2 import Environment, FileSystemLoader
import yaml
import sys
import os

def process_groups(groups):
    group_headers = [cell.value for cell in next(groups.iter_rows(min_row=1, max_row=1))]
    group_data = {}

    for row in groups.iter_rows(min_row=2, values_only=True):
        entry = dict(zip(group_headers, row))
        group_name = entry.pop("GROUP")

        group_data[group_name] = entry

    return group_data

def process_registers(registers):
    reg_data = {}
    reg_info = {}
    active_reg = ""
    active_group = ""
    offset_max = 0

    reg_headers = [cell.value for cell in next(registers.iter_rows(min_row=1, max_row=1))]
    for row in registers.iter_rows(min_row=2, values_only=True):
        entry = dict(zip(reg_headers, row))
        addr_offset = entry.pop("ADDR_OFFSET")

        # All 32-bit registers have an address offset
        # Fields do not
        if (addr_offset):
            # Complete entry for previous register
            if (active_reg):
                reg_data[active_group][active_reg] = reg_info

            # Extract relavent registers
            offset_max = int(addr_offset, 16)
            active_reg = entry.pop("NAME").upper()
            active_group = entry.pop("ACCESS/GROUP")
            reg_description = entry.pop("REG_DESCRIPTION")

            # Initialize for next register
            reg_data.setdefault(active_group, {})
            reg_data[active_group][active_reg] = {}
            reg_info = {}

            # Store relavent info
            reg_info["FIELDS"] = {}
            reg_info["REG_DESCRIPTION"] = reg_description
            reg_info["ADDR_OFFSET"] = addr_offset
            reg_info["ADDR_MACRO"] = f"{active_reg.upper()}_ADDR"
        else:
            # Extract relavent registers
            field_info = {}
            field = entry.pop("NAME").upper()
            access = entry.pop("ACCESS/GROUP").upper()
            bits = entry.pop("BITS")
            reset_val = entry.pop("RESET_VAL")
            field_description = entry.pop("FIELD_DESCRIPTION")

            # param calculation
            if (":" in bits):
                high_bit, low_bit = bits.replace("[", "").replace("]", "").split(":")
                field_info["WIDTH"] = int(high_bit) - int(low_bit) + 1
            else:
                field_info["WIDTH"] = 1

            field_info["ACCESS"] = access
            field_info["BITS"] = bits
            field_info["RESET_VAL"] = reset_val
            field_info["FIELD_DESCRIPTION"] = field_description

            reg_info["FIELDS"][field] = field_info

    # Write info for last register
    reg_data[active_group][active_reg] = reg_info
    reg_data["ADDR_WIDTH"] = int(offset_max - 1).bit_length()

    return reg_data

def excel_to_yaml(input_file, output_file):
    wb = load_workbook(input_file)
    registers = wb["Registers"]
    groups = wb["Groups"]

    group_data = process_groups(groups)
    reg_data = process_registers(registers)

    combined_data = {}

    combined_data["GROUPS"] = group_data
    combined_data["REGISTERS"] = reg_data

    with open(output_file, "w") as f:
        yaml_str = yaml.dump(combined_data, sort_keys=False)
        yaml_str = yaml_str.replace("\n- ", "\n\n- ")

        f.write(yaml_str)

    return

def generate_macros(yaml_file, macro_dir):
    with open(yaml_file, "r") as f:
        combined_data = yaml.safe_load(f)
        reg_data = combined_data.get("REGISTERS")

    with open(macro_file, "w") as f:
        f.write("////////////////////////////////////////////////\n")
        f.write("// AUTO-GENERATED PERIPHERAL REGISTER MACROS //\n")
        f.write("///////////////////////////////////////////////\n")

        # figure out longest register name for alignment
        max_name_len = max(len(reg_name) for reg_name in reg_data.keys())

        for reg_group in reg_data.keys():
            if (reg_group == "ADDR_WIDTH"):
                continue
            group_header = f"// REGISTER GROUP: {reg_group}\n"
            f.write(group_header)
            for reg_info in reg_data[reg_group].values():
                name_field = reg_info['ADDR_MACRO'].ljust(max_name_len + 10)
                addr_field = f"{reg_data['ADDR_WIDTH']}'h{reg_info['ADDR_OFFSET'].replace('0x', '')}"
                line = f"`define {name_field} {addr_field} // {reg_info['REG_DESCRIPTION']}\n"
                f.write(line)
            f.write("\n")
    return

def generate_package(peripheral_name, yaml_file, package_op_dir):
    with open(yaml_file, "r") as f:
        combined_data = yaml.safe_load(f)
        reg_data = combined_data.get("REGISTERS")

    # Jinja setup
    env = Environment(loader=FileSystemLoader("templates"))

    package_template = env.get_template("reg_package_template.sv.j2")
    package_output = package_template.render(peripheral_name=peripheral_name,
                                             reg_data=reg_data)

    with open(f"{package_op_dir}/{peripheral_name}_reg_package.sv", "w") as f:
        f.write(package_output)

    return

def generate_rtl(peripheral_name, yaml_file, rtl_op_dir, tb_op_dir):
    with open(yaml_file, "r") as f:
        combined_data = yaml.safe_load(f)
        reg_data = combined_data.get("REGISTERS")
        group_data = combined_data.get("GROUPS")

    for reg_group in reg_data.keys():
        if (reg_group == "ADDR_WIDTH"):
            continue
        for reg_name, reg_info in reg_data[reg_group].items():
            reg_data[reg_group][reg_name]["ADDR_MACRO"] = f"`{reg_info['ADDR_MACRO']}"
            for field_name, field_info in reg_info["FIELDS"].items():
                reg_data[reg_group][reg_name]["FIELDS"][field_name]["RESET_VAL"] = f"{field_info['WIDTH']}'h{field_info['RESET_VAL'].replace('x0', '')}"


    max_name_len = max(len(name) for name in reg_data.keys())

    # Jinja setup
    env = Environment(loader=FileSystemLoader("templates"))

    rtl_template = env.get_template("peripheral_regfile_template.sv.j2")
    rtl_output = rtl_template.render(peripheral_name=peripheral_name,
                                     reg_data=reg_data,
                                     group_data=group_data,
                                     max_name_len=max_name_len)

    tb_template = env.get_template("peripheral_regfile_tb_template.sv.j2")
    tb_output = tb_template.render(peripheral_name=peripheral_name,
                                   reg_data=reg_data,
                                   group_data=group_data,
                                   max_name_len=max_name_len)

    with open(f"{rtl_op_dir}/{peripheral_name}_regfile.sv", "w") as rtl_file, open(f"{tb_op_dir}/{peripheral_name}_regfile_tb.sv", "w") as tb_file:
        rtl_file.write(rtl_output)
        tb_file.write(tb_output)

    return

def generate_c_defs(yaml_file, cdef_op_dir):
    with open(yaml_file, "r") as f:
        reg_data = yaml.safe_load(f)

    define_info = {}
    for csr_name, csr_info in reg_data.items():
        define_info[f"CSR_{csr_name}"] = {
                                          "ADDRESS": f"0x{csr_info['ADDRESS']}u",
                                          "DESCRIPTION": csr_info["DESCRIPTION"]
                                         }

    max_name_len = max(len(name) for name in define_info.keys())

    env = Environment(loader=FileSystemLoader("templates"))

    csr_defs_template = env.get_template("csr_defs.h.j2")
    csr_defs_output = csr_defs_template.render(define_info=define_info, max_name_len=max_name_len)

    with open(cdef_op_dir, "w") as cdef_file:
        cdef_file.write(csr_defs_output)

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 peripheral_regblk_gen.py <yaml_config_file>")
        sys.exit(1)

    config_file = sys.argv[1]

    with open(config_file, "r") as f:




    peripheral_name = sys.argv[1]
    spreadsheet_path = sys.argv[2]
    rtl_output_path = sys.argv[3]
    tb_output_path = sys.argv[4]
    macro_output_path = sys.argv[5]
    cdef_output_path = sys.argv[6]

    yaml_file = "./outputs/csr_registers.yml"

    os.makedirs(os.path.dirname(rtl_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(tb_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(macro_output_path), exist_ok=True)
    os.makedirs(os.path.dirname(cdef_output_path), exist_ok=True)
    os.makedirs(os.path.dirname("./outputs"), exist_ok=True)

    excel_to_yaml(spreadsheet_path, yaml_file)
    generate_macros(yaml_file, macro_output_path)
    generate_package("example", yaml_file, package_file)
    generate_rtl("example", yaml_file, rtl_output_path, tb_output_path)
    # generate_c_defs(yaml_file, cdef_output_path)
    #
    # print(f"[OK] Generated RTL:   {rtl_output_path}")
    # print(f"[OK] Generated TB:    {tb_output_path}")
    # print(f"[OK] Generated Macros:{macro_output_path}")
    # print(f"[OK] Generated C Defines:{cdef_output_path}")

if __name__ == "__main__":
    main()
