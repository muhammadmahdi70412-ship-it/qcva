\# QCVA



A Python-based assembler for the \*\*Quantum Virtual Computing Machine (QVCM)\*\*.  

This tool reads assembly and compiles it into QVCM-compatible bytecode.



\## Features



\- Assembles human-readable QVCM assembly into executable `.qvcm` bytecode.

\- Supports:

&nbsp; - Integer and string registers (`r0–r12`, `t0–t12`)

&nbsp; - Labels and jumps

&nbsp; - Arithmetic operations

&nbsp; - String operations

&nbsp; - Memory operations

&nbsp; - Quantum instructions (`nqubit`, `hadamard`, `qread`)

&nbsp; - Input/output instructions

&nbsp; - Function calls and returns

\- Optional debug output for viewing raw bytes.

\- Useful line-by-line error messages.



\## Usage

```

python qcva.py input.qcva \[-o output.qvcm] \[-e label\_entry] \[-b for binary dump]

```



\## License

Apache-2.0.

