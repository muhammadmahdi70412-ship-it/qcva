import sys
import time

writebytes = False

def canint(val):
    try:
        val = int(val)
        return True
    except ValueError:
        return False

qvm_bytes = bytearray()

qvm_bytes.extend(b'\x67\x43\x98')

labelcheck = None

offset = 4

offsets = []

int_registers = {f"r{y}": x for x, y in enumerate(range(13))}
str_registers = {f"t{y}": x for x, y in enumerate(range(13))}
#int_registers = {y: x for x, y in enumerate("abcdefghijklmn")}
#str_registers = {y: x for x, y in enumerate("opqrstuvwxyz")}

if len(sys.argv) < 2:
	print("QVA fatal error: no input file")
	sys.exit(1)

if '-e' in sys.argv:
	labelcheck = sys.argv[sys.argv.index('-e') + 1]
else:
	qvm_bytes.extend(b'\x04')

default_output = "code.qvm"
file = sys.argv[1]
if '-o' in sys.argv:
	if len(sys.argv) < sys.argv.index('-o') + 1:
		print("error: specify output file.")
		sys.exit(1)
	output_index = sys.argv.index('-o') + 1
	default_output = sys.argv[output_index]

if '-b' in sys.argv:
	writebytes = True

labels = {}

time1 = time.time()
with open(file, 'r') as f:
	lines = [line.strip() for line in f if line.strip()]
	for line in lines:
		if line.startswith(':'):
			label = line[1:].strip()
			if label == labelcheck and labelcheck:
				qvm_bytes.extend(offset.to_bytes(1, "big"))
			labels[label] = offset
			continue
		else:
			args = line.split()
			match args[0]:
				case 'mov' | 'cmpstr':
					if args[2] in int_registers.keys() or args[2] in str_registers.keys():
						offset += 5  
					else:
						offset += 4 + len(args[2].replace("+", " ").encode('utf-8'))  
				case "cat":
					if args[2] in str_registers.keys():
						offset += 5
					else:
						offset += 4 + len(args[2].encode('utf-8'))
				case 'in':
					if args[2] in str_registers.keys():
						offset += 5
					else:
						offset += 4 + len(args[2].encode('utf-8'))
				case 'inc' | 'dec':
					offset += 2
				case 'load' | 'toint' | 'tostr' | 'hadamard' | "mread" | "malloc" | 'asb':
					offset += 3
				case 'add' | 'sub' | 'qread':
					offset += 4
				case 'jmp' | 'je' | 'jne' | 'jg' | 'jl' | 'call':
					offset += 3
				case 'end' | 'ret' | 'nqubit':
					offset += 1
				case 'cmp':
					offset += 4


	for i, line in enumerate(lines):
		if line.startswith(':'):
			if ';' in line:
				index = line.find(';')
				line = line[:index]
			label = line[1:].strip()
			continue

		if line.startswith(";"):
			continue
		if ';' in line:
			index = line.find(';')
			line = line[:index]

		args = line.split()
		line_index = i + 1
		match args[0]:
				
			case 'mov' if len(args) == 3:
				args[1] = args[1].replace(',', '')
				if canint(args[2]) and int(args[2]) > 255:
					print(f"error: cannot store numbers bigger than 255. line {line_index},  {line}")
					sys.exit(1)
				elif args[1] in int_registers.keys() and args[2] not in int_registers.keys():
					register = int_registers[args[1]].to_bytes(1, 'big')
					value = int(args[2]).to_bytes(1, 'big')
					extra = b'\x00'
					length = b'\x00'
					final_bytes = b'\x01' + extra + register + length + value
					qvm_bytes.extend(final_bytes)
				elif args[2] in int_registers.keys():
					register = int_registers[args[1]].to_bytes(1, 'big')
					value = int_registers[args[2]].to_bytes(1, 'big')
					extra = b'\x19'
					length = b'\x00'
					final_bytes = b'\x01' + extra + register + length + value
					qvm_bytes.extend(final_bytes)
				elif args[1] in str_registers.keys() and args[2] not in str_registers.keys():
					args[2] = args[2].replace("+", " ")
					register = str_registers[args[1]].to_bytes(1, 'big')
					value = args[2].encode('utf-8')
					extra = b'\x40'
					length = len(value).to_bytes(1, 'big')
					final_bytes = b'\x01' + extra + register + length + value
					qvm_bytes.extend(final_bytes)
				elif args[1] in str_registers.keys() and args[2] in str_registers.keys():
					register = str_registers[args[1]].to_bytes(1, 'big')
					value = str_registers[args[2]].to_bytes(1, 'big')
					extra = b'\x20'
					length = b'\x00'
					final_bytes = b'\x01' + extra + register + length + value
					qvm_bytes.extend(final_bytes)

			case 'load' if len(args) == 2:
				args[1] = args[1].replace(',', '')
				if args[1] in int_registers.keys():
					register = int_registers[args[1]].to_bytes(1, 'big')
					extra = b'\x00'
					final_bytes = b'\x02' + extra + register
					qvm_bytes.extend(final_bytes)
				else:
					register = str_registers[args[1]].to_bytes(1, 'big')
					extra = b'\x40'
					final_bytes = b'\x02' + extra + register
					qvm_bytes.extend(final_bytes)

			case 'inc' if len(args) == 2:
				register = int_registers[args[1]].to_bytes(1, 'big')
				final_bytes = b'\x03' + register
				qvm_bytes.extend(final_bytes)
			
			case 'dec' if len(args) == 2:
				register = int_registers[args[1]].to_bytes(1, 'big')
				final_bytes = b'\x04' + register
				qvm_bytes.extend(final_bytes)

			case 'add' if len(args) == 3:
				args[1] = args[1].replace(',', '')
				if canint(args[2]):
					extra = b'\x67'
					val2 = int(args[2]).to_bytes(1, 'big')
				else:
					extra = b'\x00'
					val2 = int_registers[args[2]].to_bytes(1, 'big')

				val1 = int_registers[args[1]].to_bytes(1, 'big')
				final_bytes = b'\x05' + val1 + extra + val2
				qvm_bytes.extend(final_bytes)

			case 'sub' if len(args) == 3:
				args[1] = args[1].replace(',', '')
				if canint(args[2]):
					extra = b'\x67'
					val2 = int(args[2]).to_bytes(1, 'big')
				else:
					extra = b'\x00'
					val2 = int_registers[args[2]].to_bytes(1, 'big')

				val1 = int_registers[args[1]].to_bytes(1, 'big')
				final_bytes = b'\x06' + val1 + extra + val2
				qvm_bytes.extend(final_bytes)
			
			
			case 'jmp' if len(args) == 2:
				if not canint(args[1]):
					label = (labels[args[1]] - 0).to_bytes(2, 'big')
					final_bytes = b'\x08' + label
					qvm_bytes.extend(final_bytes)
				else:
					print(f"error: labels cannot be numerical. line {line_index},  {line}")
					sys.exit(1)

			case 'cmp' if len(args) == 3:
				args[1] = args[1].replace(',', '')
				val1 = int_registers[args[1]].to_bytes(1, 'big')
				
				if canint(args[2]):
					val2 = int(args[2]).to_bytes(1, 'big')
					extra = b'\x67'
				else:
					val2 = int_registers[args[2]].to_bytes(1, 'big')
					extra = b'\x00'

				final_bytes = b'\x09' + val1 + extra + val2
				qvm_bytes.extend(final_bytes)

			case 'je' if len(args) == 2:
				if not canint(args[1]):
					label = (labels[args[1]] - 0).to_bytes(2, 'big')
					final_bytes = b'\x0A' + label
					qvm_bytes.extend(final_bytes)
				else:
					print(f"error: labels cannot be numerical. line {line_index},  {line}")
					sys.exit(1)

			case 'jne' if len(args) == 2:
				if not canint(args[1]):
					label = (labels[args[1]] - 0).to_bytes(2, 'big')
					final_bytes = b'\x0B' + label
					qvm_bytes.extend(final_bytes)
				else:
					print(f"error: labels cannot be numerical. line {line_index},  {line}")
					sys.exit(1)
			
			case "jg" if len(args) == 2:
				if not canint(args[1]):
					label = (labels[args[1]] - 0).to_bytes(2, 'big')
					final_bytes = b'\x0C' + label
					qvm_bytes.extend(final_bytes)
				else:
					print(f"error: labels cannot be numerical. line {line_index},  {line}")
					sys.exit(1)
			
			case 'jl' if len(args) == 2:
				if not canint(args[1]):
					label = (labels[args[1]] - 0).to_bytes(2, 'big')
					final_bytes = b'\x0D' + label
					qvm_bytes.extend(final_bytes)
				else:
					print(f"error: labels cannot be numerical. line {line_index},  {line}")
					sys.exit(1)

			case 'in' if len(args) == 3:
				args[1] = args[1].replace(',', '')
				if args[1] in int_registers.keys() or args[2] in int_registers.keys():
					print(f"error: cannot write string input to int register, or take string input from int register. line {line_index},  {line}")
					sys.exit(1)
				if args[2] in str_registers.keys():
					save_register = str_registers[args[1]].to_bytes(1, 'big')
					print_register = str_registers[args[2]].to_bytes(1, 'big')
					extra = b'\x00'
					length = b'\x00'
					final_bytes = b'\x0E' + save_register + extra + length + print_register
					qvm_bytes.extend(final_bytes)
				else:
					args[2] = args[2].replace("+", " ")
					save_register = save_register = str_registers[args[1]].to_bytes(1, 'big')
					print_lit = args[2].encode('utf-8')
					extra = b'\x40'
					length = len(print_lit).to_bytes(1, 'big')
					final_bytes = b'\x0E' + save_register + extra + length + print_lit
					qvm_bytes.extend(final_bytes)


			case 'toint' if len(args) == 3:
				args[1] = args[1].replace(",", "")
				int_reg = int_registers[args[1]].to_bytes(1, 'big')
				str_reg = str_registers[args[2]].to_bytes(1, 'big')
				final_bytes = b'\x0F' + int_reg + str_reg
				qvm_bytes.extend(final_bytes)

			case 'tostr' if len(args) == 3:
				args[1] = args[1].replace(",", "")
				int_reg = int_registers[args[2]].to_bytes(1, 'big')
				str_reg = str_registers[args[1]].to_bytes(1, 'big')
				final_bytes = b'\x10' + str_reg + int_reg
				qvm_bytes.extend(final_bytes)

			case 'cat' if len(args) == 3:
				args[1] = args[1].replace(",", "")
				if args[2] in str_registers.keys():
					first_reg = str_registers[args[1]].to_bytes(1, 'big')
					second_reg = str_registers[args[2]].to_bytes(1, 'big')
					extra = b'\x00'
					length = b'\x00'
					final_bytes = b'\x11' + first_reg + extra + length + second_reg
					qvm_bytes.extend(final_bytes)
				else:
					args[2] = args[2].replace("+", " ")
					first_reg = str_registers[args[1]].to_bytes(1, 'big')
					second_lit = args[2].encode('utf-8')
					extra = b'\x40'
					length = len(second_lit).to_bytes(1, 'big')
					final_bytes = b'\x11' + first_reg + extra + length + second_lit
					qvm_bytes.extend(final_bytes)

			
			case 'cmpstr' if len(args) == 3:
				args[1] = args[1].replace(',', '')
				val1 = str_registers[args[1]].to_bytes(1, 'big')
				if args[2] not in str_registers.keys():
					literal = args[2].encode('utf-8')
					extra = b'\x40'
					length = len(literal).to_bytes(1, 'big')
					final_bytes = b'\x12'+ val1 + extra + length + literal
					qvm_bytes.extend(final_bytes)
				else:
					val2 = str_registers[args[2]].to_bytes(1, 'big')
					extra = b'\x00'
					length = b'\x00'
					final_bytes = b'\x12' + val1 + extra + length + val2
					qvm_bytes.extend(final_bytes)

			case "call" if len(args) == 2:
				if not canint(args[1]):
					label = labels[args[1]].to_bytes(2, 'big')
					final_bytes = b'\x13' + label
					qvm_bytes.extend(final_bytes)
				else:
					print(f"error: labels cannot be numerical. line {line_index},  {line}")
					sys.exit(1)

			case "ret":
				qvm_bytes.extend(b'\x14')

			case "nqubit":
				qvm_bytes.extend(b'\x15')

			case "hadamard" if len(args) == 2:
				if args[1] not in int_registers.keys():
					qvm_bytes.extend(b'\x16' + b'\x00' + (int(args[1]) - 1).to_bytes(1, 'big'))
				else:
					qvm_bytes.extend(b'\x16' + b'\x40' + int_registers[args[1]].to_bytes(1, 'big'))

			case "qread" if len(args) == 3:
				args[1] = args[1].replace(",", "")
				if args[1] in int_registers.keys() and args[2] not in int_registers.keys():
					index = (int(args[2]) - 1).to_bytes(1, 'big')
					reg = int_registers[args[1]].to_bytes(1, 'big')
					extra = b'\x00'
					final_bytes = b'\x17' + extra + reg + index
					qvm_bytes.extend(final_bytes)
				elif args[2] in int_registers.keys() and args[1] in int_registers.keys():
					index = int_registers[args[2]].to_bytes(1, 'big')
					reg = int_registers[args[1]].to_bytes(1, 'big')
					extra = b'\x40'
					final_bytes = b'\x17' + extra + reg + index
					qvm_bytes.extend(final_bytes)
			
			case "malloc" if len(args) == 3:
				args[1] = args[1].replace(",", "")
				reg1 = int_registers[args[1]].to_bytes(1, 'big')
				reg2 = int_registers[args[2]].to_bytes(1, 'big')
				final_bytes = b'\x18' + reg1 + reg2
				qvm_bytes.extend(final_bytes)
			
			case "mread" if len(args) == 3:
				args[1] = args[1].replace(",", "")
				reg1 = int_registers[args[1]].to_bytes(1, 'big')
				reg2 = int_registers[args[2]].to_bytes(1, 'big')
				final_bytes = b'\x19' + reg1 + reg2
				qvm_bytes.extend(final_bytes)
				
			case 'asb' if len(args) == 3:
				args[1] = args[1].replace(",", "")
				reg1 = int_registers[args[1]].to_bytes(1, 'big')
				reg2 = int_registers[args[2]].to_bytes(1, 'big')
				final_bytes = b'\x1A' + reg1 + reg2
				qvm_bytes.extend(final_bytes)

			case 'end':
				qvm_bytes.extend(b'\x67')

		

			case _:
				print(f"error: unknown instruction or wrong amount of args. line {line_index},  {line}")
				sys.exit(1)


if writebytes:
	print("Bytes:\n" + ''.join(str(i) for i in qvm_bytes))
	print("Bytes in hex:\n" + ' '.join(hex(b) for b in qvm_bytes))
	sys.exit(0)

time2 = time.time()

total_time = (time2 - time1) * 1000

with open(default_output, 'wb') as f:
	f.write(qvm_bytes)



print(f"Output written\n-assembly: {round(total_time, 3)}ms\n-out: {default_output}")