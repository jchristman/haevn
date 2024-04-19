'''
An object representing a string location in
a disassembled binary.
'''

from label import Label


class String(Label):
    """An internal representation of a string in disassembled code"""
    def __init__(self, name, r_addr, sec_name):
        """Initializes a string object.

        :name: Name of the string for labelling purposes
        :r_addr: Relative address of the start of the string
        :sec_name: Name of the section this string belongs to

        """
        Label.__init__(self, name, 'str')
        self.r_addr = r_addr
        self.sec_name = sec_name
