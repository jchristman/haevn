"""
This module holds the heuristics class, which provides
arbitrary abstractions for binary formats.
"""


class Heuristics(object):

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

    def __init__(self, config, arch, mode):
        """Initializes a Heuristics object for abstract binary queries.

        :arch: The desired architecture to perform queries on.
        :mode: The desired mode to perform queries on

        Both correspond to Capstone ARCH and MODE fields.
        """
        self.config = config
        self.arch = arch
        self.mode = mode

    def process_operands(self, inst):
        """Processes the operands of the given inst. Should be implemented by children.

        :inst: The instruction to process
        :returns: A list of processed operands

        """
        raise NotImplementedError()

    def is_branch(self, inst):
        """Determines if the given instruction is a branch or not.

        :returns: True if type of branch, otherwise False

        """
        # Call or branch
        return self.is_call(inst) or self.is_jump(inst)

    def is_ret(self, inst):
        raise NotImplementedError()

    def is_call(self, inst):
        """Determines if the given instruction is a call or not.
        Should be implemented by children.

        :returns: True if call, otherwise False

        """
        raise NotImplementedError()

    def op_call_get_addr(self, inst):
        raise NotImplementedError()
    
    def is_jump(self, inst):
        """Determines if the given instruction is a jump or not.
        Should be implemented by children.

        :returns: True if call, otherwise False

        """
        raise NotImplementedError()
    
    def op_jump_get_addr(self, inst):
        raise NotImplementedError()
    
    def is_conditional_jump(self, inst):
        raise NotImplementedError()

    def op_conditional_jump_option(self, inst):
        raise NotImplementedError()

