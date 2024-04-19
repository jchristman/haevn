'''
An object representing an arbitary location
(such as the start of a basic block) in
a disassembled binary.
'''

from label import Label


class Location(Label):
    """An internal representation of a location in disassembled code"""
    def __init__(self, name, r_addr, sec_name):
        """Initializes a location object

        :name: Name of this location for labelling purposes
        :r_addr: Relative address belonging to the location
        :sec_name: Name of the section this belongs to

        """
        Label.__init__(self, name, 'loc')
        self.r_addr = r_addr
        self.sec_name = sec_name

    def __str__(self):
        """Returns a string representation of this location.

        :returns: A string rep of this location
        """
        rep = '%s:0x%08x' % (self.sec_name,
                             self.r_addr)
        return rep
