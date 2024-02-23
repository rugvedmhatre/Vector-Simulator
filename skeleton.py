import os
import argparse

class IMEM(object):
    def __init__(self, iodir):
        self.size = pow(2, 16) # Can hold a maximum of 2^16 instructions.
        self.filepath = os.path.abspath(os.path.join(iodir, "Code.asm"))
        self.instructions = []

        try:
            with open(self.filepath, 'r') as insf:
                self.instructions = [ins.strip() for ins in insf.readlines()]
            print("IMEM - Instructions loaded from file:", self.filepath)
            # print("IMEM - Instructions:", self.instructions)
        except:
            print("IMEM - ERROR: Couldn't open file in path:", self.filepath)

    def Read(self, idx): # Use this to read from IMEM.
        if idx < self.size:
            return self.instructions[idx]
        else:
            print("IMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)

class DMEM(object):
    # Word addressible - each address contains 32 bits.
    def __init__(self, name, iodir, addressLen):
        self.name = name
        self.size = pow(2, addressLen)
        self.min_value  = -pow(2, 31)
        self.max_value  = pow(2, 31) - 1
        self.ipfilepath = os.path.abspath(os.path.join(iodir, name + ".txt"))
        self.opfilepath = os.path.abspath(os.path.join(iodir, name + "OP.txt"))
        self.data = []

        try:
            with open(self.ipfilepath, 'r') as ipf:
                self.data = [int(line.strip()) for line in ipf.readlines()]
            print(self.name, "- Data loaded from file:", self.ipfilepath)
            # print(self.name, "- Data:", self.data)
            self.data.extend([0x0 for i in range(self.size - len(self.data))])
        except:
            print(self.name, "- ERROR: Couldn't open input file in path:", self.ipfilepath)

    def Read(self, idx: int): # Use this to read from DMEM.
        if idx < self.size:
            return self.data[idx]
        else:
            print("DMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)

    def Write(self, idx: int, val): # Use this to write into DMEM.
        if idx < self.size:
            self.data[idx] = val
            return self.data[idx]
        else:
            print("DMEM - ERROR: Invalid memory access at index: ", idx, " with memory size: ", self.size)

    def dump(self):
        try:
            with open(self.opfilepath, 'w') as opf:
                lines = [str(data) + '\n' for data in self.data]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", self.opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", self.opfilepath)

class RegisterFile(object):
    def __init__(self, name, count, length = 1, size = 32):
        self.name       = name
        self.reg_count  = count
        self.vec_length = length # Number of 32 bit words in a register.
        self.reg_bits   = size
        self.min_value  = -pow(2, self.reg_bits-1)
        self.max_value  = pow(2, self.reg_bits-1) - 1
        self.registers  = [[0x0 for e in range(self.vec_length)] for r in range(self.reg_count)] # list of lists of integers

    def Read(self, idx: int):
        if idx < self.reg_count:
            return self.registers[idx]
        else:
            print(self.name, "- ERROR: Invalid register access at index: ", idx, " with register count: ", self.reg_count)

    def Write(self, idx: int, val: list):
        if idx < self.reg_count:
            self.registers[idx] = val
            return self.registers[idx]
        else:
            print(self.name, "- ERROR: Invalid register access at index: ", idx, " with register count: ", self.reg_count)

    def dump(self, iodir):
        opfilepath = os.path.abspath(os.path.join(iodir, self.name + ".txt"))
        try:
            with open(opfilepath, 'w') as opf:
                row_format = "{:<13}"*self.vec_length
                lines = [row_format.format(*[str(i) for i in range(self.vec_length)]) + "\n", '-'*(self.vec_length*13) + "\n"]
                lines += [row_format.format(*[str(val) for val in data]) + "\n" for data in self.registers]
                opf.writelines(lines)
            print(self.name, "- Dumped data into output file in path:", opfilepath)
        except:
            print(self.name, "- ERROR: Couldn't open output file in path:", opfilepath)

class Core():
    def __init__(self, imem: IMEM, sdmem: DMEM, vdmem: DMEM):
        self.IMEM = imem
        self.SDMEM = sdmem
        self.VDMEM = vdmem

        self.RFs = {"SRF": RegisterFile("SRF", 8),
                    "VRF": RegisterFile("VRF", 8, 64)}
        
        ### Special Purpose Registers
        self.SRs = {"VM": RegisterFile("VM", 1, 1, 64),
                     "VL": RegisterFile("VL", 1)}
        
        # Initialising Vector Length Register as the MVL
        self.SRs["VL"].Write(0, [self.RFs["VRF"].vec_length])

    def get_operands(self, instruction: list):
        if len(instruction) == 4:
            destination = str(instruction[1])
            operand1 = str(instruction[2])
            operand2 = str(instruction[3])
            destination_reg_idx = int(destination[2:])
            operand1_reg_idx = int(operand1[2:])
            if operand2.isdigit() or operand2[0] == '-':
                imm = int(operand2)
                return destination_reg_idx, operand1_reg_idx, imm
            else:
                operand2_reg_idx = int(operand2[2:])
                return destination_reg_idx, operand1_reg_idx, operand2_reg_idx
        elif len(instruction) == 3:
            destination = str(instruction[1])
            operand1 = str(instruction[2])
            destination_reg_idx = int(destination[2:])
            operand1_reg_idx = int(operand1[2:])
            return destination_reg_idx, operand1_reg_idx
        elif len(instruction) == 2:
            operand1 = str(instruction[1])
            operand1_reg_idx = int(operand1[2:])
            return operand1_reg_idx
        else:
            # -- ERROR --
            return None
        
    def run(self):
        program_counter = 0
        
        while(True):
            # --- ISSUE Stage ---
            current_instruction = imem.Read(program_counter).split(" ")
            print("Program Counter     : ", program_counter)
            print("Current Instruction : ", current_instruction)
            
            # --- DECODE + EXECUTE + WRITEBACK Stage ---
            instruction_word = current_instruction[0]
            print("Instruction Word    : ", instruction_word)

            if instruction_word == "HALT":
                # --- EXECUTE : HALT --- 
                print("Stopping the program execution!")
                break
            
            # ----- VECTOR ARITHMETIC OPERATIONS
            elif instruction_word == "ADDVV":
                # --- DECODE : ADDVV ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : ADDVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] + vector2[i]
                # --- WRITEBACK : ADDVV ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "ADDVS":
                # --- DECODE : ADDVS ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : ADDVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] + vector2[i]
                # --- WRITEBACK : ADDVS ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "SUBVV":
                # --- DECODE : SUBVV ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SUBVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] - vector2[i]
                # --- WRITEBACK : SUBVV ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "SUBVS":
                # --- DECODE : SUBVS ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SUBVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] - vector2[i]
                # --- WRITEBACK : SUBVS ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "MULVV":
                # --- DECODE : MULVV ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : MULVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] * vector2[i]
                # --- WRITEBACK : MULVV ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "MULVS":
                # --- DECODE : MULVS ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : MULVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] * vector2[i]
                # --- WRITEBACK : MULVS ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "DIVVV":
                # --- DECODE : DIVVV ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : DIVVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    # TODO - Check Divide by zero condition
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] // vector2[i]
                # --- WRITEBACK : DIVVV ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            elif instruction_word == "DIVVS":
                # --- DECODE : DIVVS ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : DIVVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                # print("Current vector 1 value : ", vector1)
                # print("Current vector 2 value : ", vector2)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                vector_mask_string = "{:064b}".format(self.SRs["VM"].Read(0)[0])
                vector_mask_list = list(vector_mask_string)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    # TODO - Check Divide by zero condition
                    if int(vector_mask_list[i]) == 1:
                        result[i] = vector1[i] // vector2[i]
                # --- WRITEBACK : DIVVS ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # print("Updated result value   : ", self.RFs["VRF"].Read(destination_reg_idx))
                # TODO - Test this instruction
            
            # ----- VECTOR MASK REGISTER OPERATIONS
            elif instruction_word == "SEQVV":
                # --- DECODE : SEQVV ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SEQVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] == vector2[i] else 0
                # --- WRITEBACK : SEQVV ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SEQVS":
                # --- DECODE : SEQVS ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SEQVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] == vector2[i] else 0
                # --- WRITEBACK : SEQVS ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SNEVV":
                # --- DECODE : SNEVV ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SNEVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] != vector2[i] else 0
                # --- WRITEBACK : SNEVV ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SNEVS":
                # --- DECODE : SNEVS ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SNEVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] != vector2[i] else 0
                # --- WRITEBACK : SNEVS ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SGTVV":
                # --- DECODE : SGTVV ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SGTVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] > vector2[i] else 0
                # --- WRITEBACK : SGTVV ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SGTVS":
                # --- DECODE : SGTVS ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SGTVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] > vector2[i] else 0
                # --- WRITEBACK : SGTVS ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SLTVV":
                # --- DECODE : SLTVV ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SLTVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] < vector2[i] else 0
                # --- WRITEBACK : SLTVV ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SLTVS":
                # --- DECODE : SLTVS ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SLTVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] < vector2[i] else 0
                # --- WRITEBACK : SLTVS ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SGEVV":
                # --- DECODE : SGEVV ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SGEVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] >= vector2[i] else 0
                # --- WRITEBACK : SGEVV ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SGEVS":
                # --- DECODE : SGEVS ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SGEVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] >= vector2[i] else 0
                # --- WRITEBACK : SGEVS ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SLEVV":
                # --- DECODE : SLEVV ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SLEVV ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] <= vector2[i] else 0
                # --- WRITEBACK : SLEVV ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "SLEVS":
                # --- DECODE : SLEVS ---
                operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SLEVS ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector2 = [scalar2 for _ in range(self.RFs["VRF"].vec_length)]
                result = [0] * self.RFs["VRF"].vec_length
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = 1 if vector1[i] <= vector2[i] else 0
                # --- WRITEBACK : SLEVS ---
                result_string = ''.join(str(x) for x in result)
                vector_mask_value = int(result_string, 2)
                self.SRs["VM"].Write(0, [vector_mask_value])
                # TODO - Test this instruction
            elif instruction_word == "CVM":
                # --- EXECUTE : CVM --- 
                # print("Clearing the Vector Mask Register...")
                # print("Current VM Value : ", bin(self.SRs["VM"].Read(0)[0]))
                self.SRs["VM"].Write(0, [int('1' * self.RFs["VRF"].vec_length, 2)])
                # print("Updated VM Value : ", bin(self.SRs["VM"].Read(0)[0]), self.SRs["VM"].Read(0)[0])
            elif instruction_word == "POP":
                # --- DECODE : POP ---
                destination_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : POP --- 
                count = bin(self.SRs["VM"].Read(0)[0]).count("1")
                if count <= self.SRs["VM"].reg_bits:
                    self.RFs["SRF"].Write(destination_reg_idx, [count])
                else:
                    print("Invalid number popped, debug code!")
                    self.RFs["SRF"].Write(destination_reg_idx, [self.SRs["VM"].reg_bits])
                # TODO - Test this instruction
            
            # ----- VECTOR LENGTH REGISTER OPERATIONS
            elif instruction_word == "MTCL":
                # --- DECODE : MTCL ---
                operand_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : MTCL --- 
                # print("Moving the current value of operand in Vector Length Register...")
                # print("Current VL Value  : ", self.SRs["VL"].Read(0)[0])
                # print("Current operand Value : ", self.RFs["SRF"].Read(operand_reg_idx)[0])
                value = self.RFs["SRF"].Read(operand_reg_idx)[0]
                if value <= self.RFs["VRF"].vec_length:
                    self.SRs["VL"].Write(0, [value])
                    # print("Updated VL Value  : ", self.SRs["VL"].Read(0)[0])
                else:
                    print("Invalid Value for Vector Length Register, debug code!")
            elif instruction_word == "MFCL":
                # --- DECODE : MFCL ---
                operand_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : MFCL --- 
                # print("Moving the current value of Vector Length Register in operand...")
                # print("Current VL Value  : ", self.SRs["VL"].Read(0)[0])
                # print("Current operand Value : ", self.RFs["SRF"].Read(operand_reg_idx)[0])
                self.RFs["SRF"].Write(operand_reg_idx, self.SRs["VL"].Read(0))
                # print("Updated operand Value : ", self.RFs["SRF"].Read(operand_reg_idx)[0])
            
            # ----- MEMORY ACCESS OPERATIONS
            elif instruction_word == "LV":
                ### --- DECODE : LV ---
                destination_reg_idx, operand1_reg_idx = self.get_operands(current_instruction)
                ### --- EXECUTE : LV ---
                memory_address = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = self.VDMEM.Read(memory_address + i)
                self.RFs["VRF"].Write(destination_reg_idx, result)
            elif instruction_word == "SV":
                ### --- DECODE : SV ---
                destination_reg_idx, operand1_reg_idx = self.get_operands(current_instruction)
                ### --- EXECUTE : SV ---
                memory_address = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                vector1 = self.RFs["VRF"].Read(destination_reg_idx)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    self.VDMEM.Write(memory_address + i, vector1[i])
            elif instruction_word == "LVWS":
                ### --- DECODE : LVWS ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                ### --- EXECUTE : LVWS ---
                memory_address = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                stride = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = self.VDMEM.Read(memory_address + (i * stride))
                self.RFs["VRF"].Write(destination_reg_idx, result)
            elif instruction_word == "SVWS":
                ### --- DECODE : SVWS ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                ### --- EXECUTE : SVWS ---
                memory_address = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                stride = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                vector1 = self.RFs["VRF"].Read(destination_reg_idx)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    self.VDMEM.Write(memory_address + (i * stride), vector1[i])
                # TODO - Test this instruction
            elif instruction_word == "LVI":
                ### --- DECODE : LVI ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                ### --- EXECUTE : LVI ---
                base_address = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                offsets = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                for i in range(self.SRs["VL"].Read(0)[0]):
                    result[i] = self.VDMEM.Read(base_address + offsets[i])
                self.RFs["VRF"].Write(destination_reg_idx, result)
            elif instruction_word == "SVI":
                ### --- DECODE : SVI ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                ### --- EXECUTE : SVI ---
                base_address = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                offsets = self.RFs["VRF"].Read(operand2_reg_idx)
                vector1 = self.RFs["VRF"].Read(destination_reg_idx)
                for i in range(self.SRs["VL"].Read(0)[0]):
                    self.VDMEM.Write(base_address + offsets[i], vector1[i])
                # TODO - Test this instruction
            elif instruction_word == "LS":
                # --- DECODE : LS ---
                destination_reg_idx, operand1_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : LS ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                memory_address = scalar1 + imm
                data = self.SDMEM.Read(memory_address)
                self.RFs["SRF"].Write(destination_reg_idx, [data])
            elif instruction_word == "SS":
                # --- DECODE : SS ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : SS ---
                data = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar1 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                memory_address = scalar1 + imm
                self.SDMEM.Write(memory_address, data)

            # ----- SCALAR OPERATIONS
            elif instruction_word == "ADD":
                # --- DECODE : ADD ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : ADD ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 + scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
            elif instruction_word == "SUB":
                # --- DECODE : SUB ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SUB ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 - scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
            elif instruction_word == "AND":
                # --- DECODE : AND ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : AND ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 & scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
                # TODO - Test this instruction
            elif instruction_word == "OR":
                # --- DECODE : OR ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : OR ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 | scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
                # TODO - Test this instruction
            elif instruction_word == "XOR":
                # --- DECODE : XOR ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : XOR ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 ^ scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
                # TODO - Test this instruction
            elif instruction_word == "SLL":
                # --- DECODE : SLL ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SLL ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 << scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
                # TODO - Test this instruction
            elif instruction_word == "SRL":
                # --- DECODE : SRL ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SRL ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                unsigned_integer = scalar1 % (1 << self.RFs["SRF"].reg_bits)
                result = unsigned_integer >> scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
                # TODO - Test this instruction
                # https://realpython.com/python-bitwise-operators/#arithmetic-vs-logical-shift
            elif instruction_word == "SRA":
                # --- DECODE : SRA ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : SRA ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                result = scalar1 >> scalar2
                self.RFs["SRF"].Write(destination_reg_idx, [result])
                # TODO - Test this instruction

            # ----- CONTROL OPERATIONS
            elif instruction_word == "BEQ":
                # --- DECODE : BEQ ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : BEQ ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                if scalar1 == scalar2:
                    program_counter = program_counter + imm
                # TODO - Test this instruction
            elif instruction_word == "BNE":
                # --- DECODE : BNE ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : BNE ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                if scalar1 != scalar2:
                    program_counter = program_counter + imm
                # TODO - Test this instruction
            elif instruction_word == "BGT":
                # --- DECODE : BGT ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : BGT ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                if scalar1 > scalar2:
                    program_counter = program_counter + imm
                # TODO - Test this instruction
            elif instruction_word == "BLT":
                # --- DECODE : BLT ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : BLT ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                if scalar1 < scalar2:
                    program_counter = program_counter + imm
                # TODO - Test this instruction
            elif instruction_word == "BGE":
                # --- DECODE : BGE ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : BGE ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                if scalar1 >= scalar2:
                    program_counter = program_counter + imm
                # TODO - Test this instruction
            elif instruction_word == "BLE":
                # --- DECODE : BLE ---
                operand1_reg_idx, operand2_reg_idx, imm = self.get_operands(current_instruction)
                # --- EXECUTE : BLE ---
                scalar1 = self.RFs["SRF"].Read(operand1_reg_idx)[0]
                scalar2 = self.RFs["SRF"].Read(operand2_reg_idx)[0]
                if scalar1 <= scalar2:
                    program_counter = program_counter + imm
                # TODO - Test this instruction
            
            # ----- REGISTER-REGISTER SHUFFLE
            elif instruction_word == "UNPACKLO":
                # --- DECODE : UNPACKLO ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : UNPACKLO ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                j = 0
                for i in range(0, self.SRs["VL"].Read(0)[0] // 2):
                    result[j] = vector1[i]
                    result[j+1] = vector2[i]
                    j += 2
                # --- WRITEBACK : UNPACKLO ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # TODO - Test this instruction
            elif instruction_word == "UNPACKHI":
                # --- DECODE : UNPACKHI ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : UNPACKHI ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                j = 0
                for i in range(self.SRs["VL"].Read(0)[0] // 2, self.SRs["VL"].Read(0)[0]):
                    result[j] = vector1[i]
                    result[j+1] = vector2[i]
                    j += 2
                # --- WRITEBACK : UNPACKHI ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # TODO - Test this instruction
            elif instruction_word == "PACKLO":
                # --- DECODE : PACKLO ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : PACKLO ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                j = 0
                mvl = self.SRs["VL"].Read(0)[0]
                for i in range(0, mvl, 2):
                    result[j] = vector1[i]
                    result[(mvl // 2) + j] = vector2[i]
                    j += 1
                # --- WRITEBACK : PACKLO ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # TODO - Test this instruction
            elif instruction_word == "PACKHI":
                # --- DECODE : PACKHI ---
                destination_reg_idx, operand1_reg_idx, operand2_reg_idx = self.get_operands(current_instruction)
                # --- EXECUTE : PACKHI ---
                vector1 = self.RFs["VRF"].Read(operand1_reg_idx)
                vector2 = self.RFs["VRF"].Read(operand2_reg_idx)
                result = [0x0 for e in range(self.RFs["VRF"].vec_length)]
                j = 0
                mvl = self.SRs["VL"].Read(0)[0]
                for i in range(1, mvl, 2):
                    result[j] = vector1[i]
                    result[(mvl // 2) + j] = vector2[i]
                    j += 1
                # --- WRITEBACK : PACKHI ---
                self.RFs["VRF"].Write(destination_reg_idx, result)
                # TODO - Test this instruction

            else:
                print("DECODE - ERROR: Invalid instruction at program counter: ", program_counter)

            program_counter += 1
            print("")

    def dumpregs(self, iodir):
        for rf in self.RFs.values():
            rf.dump(iodir)

# class VectorCore(object):
#     def handle_scalar(self, element, length):
#         if not (isinstance(element, (list, tuple, dict, set, frozenset)) or hasattr(element, '__iter__')):
#             # If element is scalar, make a vector of length length
#             return [element for _ in range(length)]
#         return element
#     # Vector Arithmatic
#     def addv_(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i]+v2[i])
#         return res
#     def subv_(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i]-v2[i])
#         return res
#     def mulv_(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i]*v2[i])
#         return res
#     def divv_(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i]/v2[i])
#         return res
#     # Vector Mask
#     def EQ(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i] == v2[i])
#         return res
#     def NE(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i] != v2[i])
#         return res
#     def GT(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i] > v2[i])
#         return res
#     def GE(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i] >= v2[i])
#         return res
#     def LT(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i] < v2[i])
#         return res
#     def LE(self, v1, v2):
#         res = []
#         v2 = self.handle_scalar(v2, len(v1))
#         for i in range(len(v1)):
#             res.append(v1[i] <= v2[i])
#         return res
#     # Memory Access
#     ''' 7-10: CVM ... MFCL '''
#     def LV(self, dmem:DMEM, v1, s1):
#         res = []
#         for i in range(len(v1)):
#             res.append(dmem.Read(s1+i))
#         return res
#     def SV(self, dmem:DMEM, v1, s1):
#         for i in range(len(v1)):
#             dmem.Write(s1+i, v1[i])
#         return
    
#     def LVWS(self, dmem:DMEM, v1, s1, s2):
#         res = []
#         for i in range(len(v1)):
#             res.append(dmem.Read(s1+(i*s2)))
#         return res
#     def SVWS(self, dmem:DMEM, v1, s1, s2):
#         for i in range(len(v1)):
#             dmem.Write(s1+(i*s2), v1[i])
#         return
    
#     def LVI(self, dmem:DMEM, v1, s1, v2):
#         res = []
#         for i in range(len(v1)):
#             res.append(dmem.Read(s1+v2[i]))
#         return res
#     def SVI(self, dmem:DMEM, v1, s1, v2):
#         for i in range(len(v1)):
#             dmem.Write(s1+v2[i], v1[i])
#         return
    
#     ''' 17-23: Scalar Operations '''

#     def UNPACKLO(self, v1, v2, v3):
#         for i in range(len(v1)):
#             if i%2 == 0:
#                 v1[i] = v2[i//2]
#             else:
#                 v1[i] = v3[i//2]
#     def UNPACKHI(self, v1, v2, v3):
#         base = len(v1) // 2
#         for i in range(len(v1)):
#             if i%2 == 0:
#                 v1[i] = v2[base+ (i//2)]
#             else:
#                 v1[i] = v3[base+ (i//2)]
#     def PACKLO(self, v1, v2, v3):
#         base = len(v1) // 2
#         for i in range(len(v1)):
#             v1[i//2] = v2[2*(i//2)]
#             v1[base+ (i//2)] = v3[2*(i//2)]
#     def PACKHI(self, v1, v2, v3):
#         base = len(v1) // 2
#         for i in range(len(v1)):
#             v1[i//2] = v2[2*(i//2) + 1]
#             v1[base+ (i//2)] = v3[2*(i//2) + 1]
    
#     ''' HALT '''

# class ScalarCore(object):
#     def LS(self, dmem:DMEM, s1, imm):
#         return dmem.Read(s1+imm)

if __name__ == "__main__":
    #parse arguments for input file location
    parser = argparse.ArgumentParser(description='Vector Core Performance Model')
    parser.add_argument('--iodir', default="", type=str, help='Path to the folder containing the input files - instructions and data.')
    args = parser.parse_args()

    iodir = os.path.abspath(args.iodir)
    print("IO Directory:", iodir)

    # Parse IMEM
    imem = IMEM(iodir)  
    # Parse SMEM
    sdmem = DMEM("SDMEM", iodir, 13) # 32 KB is 2^15 bytes = 2^13 K 32-bit words.
    # Parse VMEM
    vdmem = DMEM("VDMEM", iodir, 17) # 512 KB is 2^19 bytes = 2^17 K 32-bit words. 

    # Create Vector Core
    vcore = Core(imem, sdmem, vdmem)

    # Run Core
    vcore.run()   
    vcore.dumpregs(iodir)

    sdmem.dump()
    vdmem.dump()

    # THE END