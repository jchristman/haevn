'''
Identifies references from one part of the disassembly to another.

This will take an existing disassembly from the database and parse each
instruction looking at its operands to see if any of them could be
references to another part of the disassembly.

'''

from parser import Parser
from disassembler_libs import logger
from disassembler_libs.xref import Xref
from disassembler_libs.dbmanager import generate_db_manager
from disassembler_libs.location import Location


def find_xref_loc(op, sections):
    """Generates an xref on an operand

    :op: The operand to check for an xref
    :sections: A list of section objects (used to check addr ranges)
    :returns: None or a Location object being referenced

    """
    if 'xref' in op:
        # If there's already an xref on this operand then ignore it
        return None

    val = 0

    if op['type'] == 'fp':
        # self.log.debug('fp: 0x%08x' % op['fp']['val'])
        val = op['fp']['val']
    elif op['type'] == 'imm':
        # self.log.debug('imm: 0x%08x' % op['imm']['val'])
        val = op['imm']['val']
    elif op['type'] == 'inv':
        # self.log.debug('inv')
        pass
    elif op['type'] == 'mem':
        # Either indexed (uses a register as index) or relative (uses imm)
        indexed = op['index'] != 0
        if indexed:
            # self.log.debug('mem-indexed')
            pass
        else:
            # self.log.debug('mem-rel: 0x%08x' % op['rel']['val'])
            pass

    if val != 0:
        # TODO: Figure out a clean way to exclude some sections -
        #       like .comment and .shstrtab
        if val < 0x10000:
            return None
        # TODO: Some case where val is neg(?). Need to know sizeof(long)
        for s in sections:
            if s.contains_addr(val):
                label_name = 'loc_%08x' % val
                # TODO: Expand this to match 64-bit addrs
                loc = Location(label_name, val-s.base_addr, s.name)
                # self.log.debug('Found location: %s' % str(loc))
                return loc
    return None


def add_xrefs(config, project_name, disassembly_name, sec_name, sections):
    """Creates xref objects and adds them to the db.

    :config: A configuration file to read
    :project_name: The name of the project
    :disassembly_name: The name of the disassembly
    :sec_name: Name of the section we're looking through
    :sections: A list of section objects (used to check addr ranges)
    :returns: None

    """
    log = logger.getLogger(__name__, config)
    db_man = generate_db_manager(config, project_name, disassembly_name)

    log.debug('Finding xrefs for: %s' % sec_name)
    for inst in db_man.get_instructions(sec_name):
        if not inst.is_text:
            # Only look through executable instructions
            continue

        # A list for (possibly) modifed operands
        operands = []
        # For each operand in the instruction
        for op in inst.operands:
            loc = find_xref_loc(op, sections)
            new_op = op
            if loc is not None:
                # if it has a new xref, then edit the op to have it
                xref = Xref(inst.r_addr, sec_name, loc)
                log.debug('Adding xref: %s' % xref)
                db_man.add_xref(xref)  # TODO: bulk insert?

                # If the reference isn't alread a loc, insert in db
                db_man.add_location(loc)

                new_op['xref'] = loc
            operands.append(new_op)
        if operands != inst.operands:
            inst.operands = operands
            db_man.add_instruction(sec_name, inst, update=True)


class XrefParser(Parser):
    """Finds all c-strings in nx sections of the disassembly. """
    def __init__(self, config, project_name, disassembly_name):
        """Initializes a StringParser object.

        :config: A configuration file to read
        :project_name: The name of the project
        :disassembly_name: The name of the disassembly

        """
        Parser.__init__(self, config, project_name, disassembly_name)
        self.log = logger.getLogger(__name__, config)

    def run(self):
        """Run the xrefparser.

        :returns: None

        """
        self.log.info('XrefParser is running.')

        db_man = generate_db_manager(self.config, self.project_name,
                                     self.disassembly_name)

        sections = [x for x in db_man.get_sections()]

        for sec in sections:
            self.log.debug('Section ranges: %s - [0x%08x-0x%08x]' %
                           (sec.name, sec.base_addr, sec.base_addr+sec.size))

        multi_disabled = self.config.getboolean('Debugging',
                                                'disable_multiprocessing')

        for sec in [x for x in sections if x.is_executable()]:
            if multi_disabled:
                add_xrefs(self.config, self.project_name,
                          self.disassembly_name, sec.name,
                          sections)
            else:
                self.m_pool.apply_async(add_xrefs,
                                        args=(self.config,
                                              self.project_name,
                                              self.disassembly_name,
                                              sec.name,
                                              sections))

        if not multi_disabled:
            self.m_pool.close()
            self.m_pool.join()


def make_parser(db_man, disassembler, config):
    '''
    Factory for XrefParser
    '''
    return XrefParser(db_man, disassembler, config)
