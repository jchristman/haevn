'''
An object representing a function in
a disassembled binary.
'''

from label import Label


class Function(Label):
    """An internal representation of an assembly function"""
    def __init__(self, name, r_start_addr, r_end_addr, sec_name, l_vars=None):
        """Initializes a function object

        :name: Name given to the function for labelling purposes
        :r_start_addr: Relative start address of the func
        :r_end_addr: Relative end address of the func
        :sec_name: Name of the section the func belongs to
        :l_vars: Local variables belonging to the func

        """
        Label.__init__(self, name, 'func')
        self.r_start_addr = r_start_addr
        self.r_end_addr = r_end_addr
        self.l_vars = l_vars
        self.sec_name = sec_name
