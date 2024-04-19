'''
An object representing a disassembled instruction.
Variations depend on the is_text field - which determines
if this instruction is text (executable) or data (non-executable)
'''


class Instruction:
    """An internal representation of an assembly function"""
    def __init__(self, r_address, is_text, my_bytes, mnemonic,
                 operands=None, disp=None):
        """Initializes an instruction object

        :r_address: Relative address of the start of the instruction
        :is_text: If this instruction is executable or not
        :my_bytes: A string of the bytes for this instruction
        :mnemonic: Mnemonic of the instruction
        :operands: A list of operands and their various fields
        :disp: Method of displaying an instruction's data

        """
        self.r_addr = r_address
        self.is_text = is_text
        self.my_bytes = my_bytes
        # Stupid hack until capstone's skipdata_setup works properly
        self.mnemonic = 'db' if mnemonic == '.byte' else mnemonic
        if self.is_text:
            self.operands = operands
        else:
            self.disp = disp

    def __str__(self):
        """Retrieve a string representation of the instruction

        :returns: A string

        """
        s = 'Instruction('
        s += 'r_addr:%d, ' % self.r_addr
        s += 'is_text:' + str(self.is_text) + ', '
        s += 'bytes:' + self.my_bytes.encode('hex') + ', '
        s += 'mnemonic:' + self.mnemonic + ', '
        if self.is_text:
            s += 'operands:' + ''.join(str(x) for x in self.operands)
        else:
            s += 'disp:' + self.disp
        s += ')'
        return s

