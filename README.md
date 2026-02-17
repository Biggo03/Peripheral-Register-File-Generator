# Peripheral Register File Generator

Deterministic, spreadsheet-driven generation of SystemVerilog register files and C register definitions for FPGA and ASIC designs.

**Repository:**
https://github.com/Biggo03/Peripheral-Register-File-Generator

---

## Overview

The Peripheral Register File Generator converts a structured Excel register map into:

- SystemVerilog RTL register file
- SystemVerilog package
- SystemVerilog testbench
- SystemVerilog macro header
- C macro header definitions
- Simulation run script
- Intermediate YAML representation

This tool was built to support clean, reproducible peripheral development in larger SoC or CPU projects. It enforces structure at the specification level and produces consistent, traceable outputs suitable for both hardware and firmware integration.

---

## Motivation

Register blocks are often:

- Hand-written
- Inconsistently formatted
- Error-prone
- Difficult to maintain

This generator introduces:

- Spreadsheet-driven specification
- Deterministic generation
- Git-traceable outputs
- Clear separation of generation logic and templates

The result is a maintainable, scalable register definition flow appropriate for FPGA prototyping and ASIC development.

---

## Key Components

- **peripheral_regblk_gen.py**
  Main generation script.

- **example_config.yml**
  Example configuration template.

- **spreadsheets/example_spreadsheet.xlsx**
  Required spreadsheet format reference.

- **templates/**
  Jinja2 templates used for code generation.

---

## Requirements

- Python 3.8+
- PyYAML
- Jinja2
- openpyxl (or equivalent Excel reader)

Install dependencies:

```bash
pip install pyyaml jinja2 openpyxl
```

---

## Spreadsheet Format

The Excel input file must contain two sheets:

### 1. `Groups`

Defines logical register groupings and permissions.

Required fields:
- Group Name
- Permissions (e.g., RW, RO, WO)

---

### 2. `Registers`

Defines:

- Register name
- Register address offset
- Register group
- Field names
- Field bit ranges
- Field reset values
- Register description
- Field descriptions

The format must match `example_spreadsheet.xlsx` exactly.

The spreadsheet serves as the single source of truth.

---

## Configuration

The generator is driven by a YAML configuration file. See `example_config.yml` for an example.

### Configuration Fields

| Field | Description |
|--------|------------|
| `peripheral_name` | Peripheral name (used for file naming and macro prefixing) |
| `spreadsheet_path` | Path to Excel register map |
| `rtl_output_dir` | RTL output directory |
| `tb_output_dir` | Testbench output directory |
| `package_output_dir` | SystemVerilog package output directory |
| `macro_output_dir` | SV macro header output directory |
| `cdef_output_dir` | C header output directory |
| `script_output_dir` | Simulation script output directory |
| `sim_output_dir` | Simulation build/output directory |

All directories are created automatically if they do not exist.

---

## Usage

Run the generator:

```bash
python3 peripheral_regblk_gen.py <config_yaml>
```

Generation flow:

1. Excel → YAML intermediate representation
2. Generate SystemVerilog macros
3. Generate SystemVerilog package
4. Generate register file RTL
5. Generate testbench
6. Generate simulation run script
7. Generate C header definitions

All outputs are written to the path specified in the configuration yaml file, as well as the `./outputs` directory in the running directory

---

## Generated Outputs

Typical outputs include:

- `<peripheral>_regfile.sv`
- `<peripheral>_reg_pkg.sv`
- `<peripheral>_tb.sv`
- `<peripheral>_macros.svh`
- `<peripheral>_regs.h`
- `run_<peripheral>_tb.sh`
- `<peripheral>_registers.yml`

All generated files include:

- Auto-generated warning header
- Generator repository link
- Git revision (commit SHA)
- Generation timestamp (UTC, ISO-8601)

This ensures reproducibility and traceability.

---

## Design Philosophy

- Spreadsheet as specification layer
- YAML as intermediate representation
- Python handles structure and naming
- Jinja handles formatting only
- Deterministic output
- No manual edits to generated files

The goal is clean separation between:
- Specification
- Transformation
- Presentation

---

## Intended Use

This tool is designed to integrate into:

- FPGA-based CPU or SoC projects
- Peripheral IP development flows
- Educational processor projects
- ASIC pre-silicon register modeling

It is especially useful when multiple collateral types (RTL, C headers, simulation harnesses) must remain consistent.

---

## Future Extensions

Potential improvements:

- CLI argument parsing via `argparse`
- Spreadsheet schema validation
- Documentation generation (Markdown/HTML register docs)
- Multi-instance peripheral support
- CI integration

---
