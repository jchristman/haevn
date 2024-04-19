import heuristics

from capstone import x86 as cx86


class x86(heuristics.Heuristics):
    """A class that provides heuristics for the x86 architecture"""
    def process_operands(self, inst):
        """Processes the operands of the given inst.

        :inst: The instruction to process
        :returns: A list of processed operands

        """
        processed_operands = []
        last = len(inst.operands) - 1
        for i, op in enumerate(inst.operands):
            processed_operand = {}
            processed_operand['op_str'] = inst.op_str
            processed_operand['last'] = (i == last)
            if op.type == cx86.X86_OP_FP:
                processed_operand['type'] = 'fp'
                processed_operand['fp'] = {'val': op.value.fp, 'disp': 'dec'}
            elif op.type == cx86.X86_OP_IMM:
                processed_operand['type'] = 'imm'
                processed_operand['imm'] = {'val': op.value.imm, 'disp': 'hex'}
            elif op.type == cx86.X86_OP_INVALID:  # TODO: Is this shift type?
                processed_operand['type'] = 'inv'
            elif op.type == cx86.X86_OP_MEM:
                processed_operand['type'] = 'mem'
                b = op.value.mem.base
                processed_operand['base'] = 0 if b == 0 else inst.reg_name(b)
                i = op.value.mem.index
                processed_operand['index'] = 0 if i == 0 else inst.reg_name(i)
                processed_operand['rel'] = {'val': op.value.mem.disp,
                                            'disp': 'hex'}
                processed_operand['scale'] = {'val': op.value.mem.scale,
                                              'disp': 'dec'}
            elif op.type == cx86.X86_OP_REG:
                processed_operand['type'] = 'reg'
                processed_operand['reg'] = inst.reg_name(op.value.reg)

            processed_operands.append(processed_operand)
        return processed_operands

    """Provides functions to abstract away binary format.

    This class provides a number of functions that can be used to answer
    questions about instructions in any binary format. For example
    "is_function_start(instruction_sequence)" will determine if the
    given sequence of instructions is the start of a function. This is
    helpful for functionality such as recursive disassembly, function
    finding, and xref finding, just to name a few.

    # Common instruction groups - to be consistent across all architectures.
    CS_GRP_INVALID = 0  # uninitialized/invalid group.
    CS_GRP_JUMP    = 1  # all jump instructions (conditional+direct+
                                                 indirect jumps)
    CS_GRP_CALL    = 2  # all call instructions
    CS_GRP_RET     = 3  # all return instructions
    CS_GRP_INT     = 4  # all interrupt instructions (int+syscall)
    CS_GRP_IRET    = 5  # all interrupt return instructions
    """

    def is_ret(self, inst):
        return inst.group(cx86.X86_GRP_RET) or inst.group(cx86.X86_GRP_IRET)

    def is_call(self, inst):
        return inst.group(cx86.X86_GRP_CALL)

    def op_call_get_addr(self, inst):
        for op in inst.operands:
            if op.type == cx86.X86_OP_FP:
                # TODO: I don't think this can happen.
                return None
            elif op.type == cx86.X86_OP_IMM:
                return op.value.imm
            elif op.type == cx86.X86_OP_INVALID:
                return None
            elif op.type == cx86.X86_OP_MEM:
                # TODO: I don't think we can process this.
                # base = op.value.mem.base
                # base = 0 if base == 0 else op.reg_name(b)
                # index = op.value.mem.index
                # index = 0 if index == 0 else op.reg_name(i)
                # rel = op.value.mem.disp
                # scale = op.value.mem.scale
                return None
            elif op.type == cx86.X86_OP_REG:
                return None
        print 5
        return None

    def is_jump(self, inst):
        return inst.group(cx86.X86_INS_JMP) or inst.group(cx86.X86_INS_LJMP)

    def op_jump_get_addr(self, inst):
        return self.op_call_get_addr(inst)

    def is_conditional_jump(self, inst):
        for x in [cx86.X86_INS_JA,
                  cx86.X86_INS_JAE,
                  cx86.X86_INS_JB,
                  cx86.X86_INS_JBE,
                  cx86.X86_INS_JCXZ,
                  cx86.X86_INS_JE,
                  cx86.X86_INS_JECXZ,
                  cx86.X86_INS_JG,
                  cx86.X86_INS_JGE,
                  cx86.X86_INS_JL,
                  cx86.X86_INS_JLE,
                  cx86.X86_INS_JMP,
                  cx86.X86_INS_JNE,
                  cx86.X86_INS_JNO,
                  cx86.X86_INS_JNP,
                  cx86.X86_INS_JNS,
                  cx86.X86_INS_JO,
                  cx86.X86_INS_JP,
                  cx86.X86_INS_JRCXZ,
                  cx86.X86_INS_JS]:
            if inst.id == x:
                return True
        return False

    def op_conditional_jump_option(self, inst):
        return self.op_call_get_addr(inst)
