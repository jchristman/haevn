'''
A small class for fetching attributes (read, write, exec, append)
'''


class Attributes:
    """A class to describe permissions attributes. """

    def __init__(self, attribute_string):
        """Initializes an Attribute object from an attribute_string

        :attribute_string: A combination of the characters RWXA

        """
        self.read = 'R' in attribute_string.upper()
        self.write = 'W' in attribute_string.upper()
        self.executable = 'X' in attribute_string.upper()
        self.append = 'A' in attribute_string.upper()

    def __str__(self):
        """Returns a string representation of an Attribute object

        :returns: A combination of the characters RWXA as appropriate

        """
        s = ''
        s += 'R' if self.read else ' '
        s += 'W' if self.write else ' '
        s += 'X' if self.executable else ' '
        s += 'A' if self.append else ' '

        return s
