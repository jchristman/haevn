'''
An object representing the disassembly of a binary.
'''


class Disassembly():
    """An internal representation of a disassembly target """
    def __init__(self, dis_name, binary_name, binary_format,
                 architecture, mode, md5, size, entry_point):
        """Initialize a disassembly object.

        :dis_name: Name for the disassembly
        :binary_name: Name of the binary te disassembly represents
        :binary_format: File format of the bin (ELF, PE, etc.)
        :architecture: Machine architecture being used
        :mode: Mode of that arch (x86-64, THUMB, etc.)
        :md5: MD5 of the binary
        :size: File size of the binary
        :entry_point: Original entry point for execution in the bin

        """
        self.dis_name = dis_name
        self.binary_name = binary_name
        self.binary_format = binary_format
        self.architecture = architecture
        self.mode = mode
        self.md5 = md5
        self.size = size
        self.entry_point = entry_point
