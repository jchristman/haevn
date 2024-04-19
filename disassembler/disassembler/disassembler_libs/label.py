'''
An object representing various labelled locations in
a disassembled binary.

Possibilities include - function ('func'), string ('str'),
section ('sec'), or some arbitrary location ('loc') - all
of which are implemented in child classes.
'''


class Label:
    """An internal representation of a labelled location in the disassembly"""
    def __init__(self, name, t):
        """Initializes a label object

        :name: Name of this label
        :t: Type of the label

        """
        self.name = name
        self.type = t
