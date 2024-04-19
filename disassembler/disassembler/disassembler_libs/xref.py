'''
An object representing a cross-reference in
a disassembled binary.

As an example, consider an intruction that references the
address of a string. The xref would contain:
    base_addr = <relative address of instruction in section>
    section_sec_name = <section name of instruction>
    ref_loc = <location object being referenced>
'''


class Xref(object):
    """An internal representation of an xref in disassembled code"""
    def __init__(self, base_addr, base_sec_name, ref_loc):
        """Initializes an xref object.

        :base_addr: The relative address of the inst doing the referencing
        :base_sec_name: The section name of the inst doing the referencing
        :ref_loc: The location object being referenced to

        """
        self.base_addr = base_addr
        self.base_sec_name = base_sec_name
        self.ref_loc = ref_loc

    def __str__(self):
        """Returns a string representation of this xref.

        :returns: A string rep

        """
        rep = '%s:0x%08x => %s' % (self.base_sec_name,
                                   self.base_addr,
                                   self.ref_loc)
        return rep

