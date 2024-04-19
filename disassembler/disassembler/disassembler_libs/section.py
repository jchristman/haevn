'''
An object representing a section in
a disassembled binary.
'''

from label import Label


class Section(Label):
    """An internal representation of a section"""
    def __init__(self, name, data, attribs, base_addr, size):
        """Initializes a section object

        :name: The name of the section, for labelling purposes (can be renamed)
        :data: The raw data (bytes) of the section
        :attribs: The section's attributes
        :base_addr: The base_address that this section begins at
        :size: The size of the section in bytes

        """
        Label.__init__(self, name, 'sec')
        self.data = data
        self.attribs = attribs
        self.base_addr = base_addr
        self.size = size

    def is_executable(self):
        """Returns true if this section is executable

        :returns: True if exec, otherwise False

        """
        return self.attribs.executable

    def contains_addr(self, addr):
        """Returns true if this section contains the given absolute address.

        :returns: True if section contains addr, otherwise False

        """
        return self.base_addr <= addr < self.base_addr + self.size
