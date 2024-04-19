'''
Searches through the disassembly to identify and add all c-style strings
to the database.
'''

from parser import Parser
from disassembler_libs.instruction import Instruction
from disassembler_libs.string import String
from disassembler_libs.dbmanager import generate_db_manager
from disassembler_libs import logger
from collections import namedtuple
from bson.binary import Binary
import re

# Used to shovel data between functions internally here
StringFormat = namedtuple('StringFormat', 'addr name contents')


def add_strings(config, project_name, disassembly_name, sec_name, strings):
    """A standalone function that will add a list of string objects to the db.

    :config: A configuration file to read
    :project_name: The name of the project
    :disassembly_name: The name of the disassembly
    :sec_name: The name of the section these strings belong to
    :strings: A list of string objects to add
    :returns: None

    """
    #log = logger.getLogger(__name__, config)
    db_man = generate_db_manager(config, project_name, disassembly_name)

    #log.debug('Found strings: %s' % strings)

    # TODO: Make this check for existing multi-byte sequences that
    #      might overlap and fix them appropriately.
    #      This will currently only work correctly if we're
    #      deleting 1-byte instructions
    ranges = [[s.addr, s.addr + len(s.contents)] for s in strings]

    # First remove everything taking up these addreses
    db_man.batch_delete_insts_in_addr_ranges(sec_name, ranges)

    # Add instructions with appropriate length and disp='str'
    insts = [parse_string_instruction(s) for s in strings]
    db_man.batch_add_instructions(sec_name, insts)

    # Add new string labels
    #TODO: Make this batch as well. It's a lot of labels to add
    for s in strings:
        str_label = String(s.name, s.addr, sec_name)
        db_man.add_string(str_label)


def parse_string_instruction(string):
    """Creates an instruction object from a StringFormat.

    :string: A StringFormat object to parse through.

    """
    return Instruction(string.addr,  # r_addr
                       False,  # is_text
                       Binary(str(string.contents)),  # my_bytes
                       '.db',  # mnemonic
                       None,  # operands
                       'str')  # disp


class StringParser(Parser):
    """Finds all c-strings in nx sections of the disassembly. """
    def __init__(self, config, project_name, disassembly_name):
        """Initializes a StringParser object.

        :config: A configuration file to read
        :project_name: The name of the project
        :disassembly_name: The name of the disassembly

        """
        Parser.__init__(self, config, project_name, disassembly_name)
        self.log = logger.getLogger(__name__, config)

    def get_min_length(self):
        """Returns the minimum length of a string to search for.

        :returns: Min length of a string to find

        """
        return self.config.getint('StringParser', 'min_string_length')

    def run(self):
        """Run the stringparser.

        :returns: None

        """
        self.log.info('StringParser is running.')

        # If there are already some string labels for this disassembly then
        # do nothing.
        # TODO: support looking for strings multiple times
        db_man = generate_db_manager(self.config, self.project_name,
                                     self.disassembly_name)
        strings = db_man.get_strings()
        if len(strings) != 0:
            self.log.error(('Strings already exist for '
                            'this disassembly! Exiting.'))
            return

        self.log.debug('Retrieving non-executable sections')
        non_exec_sections = db_man.get_non_exec_sections()

        for sec in non_exec_sections:
            self.find_and_add_strings(sec)

        multi_disabled = self.config.getboolean('Debugging',
                                                'disable_multiprocessing')
        if not multi_disabled:
            self.m_pool.close()
            self.m_pool.join()

    def find_and_add_strings(self, sec):
        """Given a section, finds all strings in it and adds them to the db.

        :sec: A section object
        :returns: None

        """
        self.log.debug('Finding strings for: %s' % sec.name)

        # log.debug('sec data is: %s' % sec.data)
        # Find strings in the data of this section
        min_length = self.get_min_length()
        strings = self.find_strings(sec.data, length=min_length)

        multi_disabled = self.config.getboolean('Debugging',
                                                'disable_multiprocessing')

        # Spawn a new process to add n strings at a time
        n = 30
        for i in xrange(0, len(strings), n):
            if multi_disabled:
                add_strings(self.config, self.project_name,
                            self.disassembly_name, sec.name,
                            strings[i:i+n])
            else:
                self.m_pool.apply_async(add_strings,
                                        args=(self.config,
                                              self.project_name,
                                              self.disassembly_name,
                                              sec.name,
                                              strings[i:i+n]))

    def find_strings(self, data, length=5):
        """Given a blob of data, find all c-strings in it.

        :data: A string of raw bytes
        :length: The minimum string length to look for
        :returns: A list of StringFormats

        """
        pattern = re.compile(r"[\x20-\x7e]{%d,}\x00" % (length-1))
        # This is inefficient here but allows us
        # to do multiprocessing separation well
        result = []
        for x in pattern.finditer(data):
            contents = bytearray(x.group())
            name = x.group()[:-1]  # set name to its contents (minus \x00)
            addr = x.start()
            result.append(StringFormat(addr, name, contents))
        return result


def make_parser(config, project_name, disassembly_name):
    """Create a StringParser object.

    :config: A configuration file to read
    :project_name: The name of the project
    :disassembly_name: The name of the disassembly
    :returns: A stringparser object

    """
    return StringParser(config, project_name, disassembly_name)
