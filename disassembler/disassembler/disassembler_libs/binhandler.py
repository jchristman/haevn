'''
A utility that manages various file format parsers into a
standardized interface for accessibility.

TODO: break this into subclasses for full OOP design
'''

import capstone
import hashlib
from disassembler_libs import logger

from section import Section
from attributes import Attributes

from elftools.elf.elffile import ELFFile
from elftools.elf.descriptions import describe_sh_flags


class BinHandler:
    """A class to abstract the format of a binary for standardized access. """

    def __init__(self, binpath):
        """Initializes a BinHandler from the path of a binary

        :binpath: A path to the binary to disassemble

        """
        self.binpath = binpath
        self.file_format = None
        self.bin_file = None
        self.parser = None

        self.log = logger.getLogger(__name__)

        self.bin_file = open(binpath, 'rb')
        self.file_format, self.parser = self._find_bin_parser()

    def __del__(self):
        """Closes any open file handles """
        self.bin_file.close()

    def _find_bin_parser(self):
        """Determines which binary parser to use.

        :returns: A handle to an appropriate binary parser

        """
        file_format = ''
        parser = None

        # Try ELF
        try:
            parser = ELFFile(self.bin_file)
            file_format = 'ELF'
        except:
            self.log.error('%s wasn\'t ELF')

        # Try PE
        # PE TRYING THINGS HERE

        self.bin_file.seek(0)

        return file_format, parser

    def get_sections(self):
        """Fetches section objects for every section in the binary

        :returns: A list of Section objects for all of this binary's sections

        """
        ex = self.get_executable_sections()
        nx = self.get_non_executable_sections()
        return ex + nx

    def get_executable_sections(self):
        """Fetches section objects for just executable sections

        :returns: A list of Section objects for all executable sections

        """
        if self.file_format == 'ELF':
            return self._get_sections_elf(executable=True)
        elif self.file_format == 'PE':
            return self._get_sections_pe(executable=True)

    def get_non_executable_sections(self):
        """Fetches section objects for only non-executable sections

        :returns: A list of Section objects for non-executable sections

        """
        if self.file_format == 'ELF':
            return self._get_sections_elf(executable=False)
        elif self.file_format == 'PE':
            return self._get_sections_pe(executable=False)

    def _get_sections_elf(self, executable=False):
        """Fetches section objects for an elf binary

        :executable: Boolean filter - return only executable sections (or not)
        :returns: A list of Section objects

        """
        wants_executable = executable
        ret_secs = []
        for sec in self.parser.iter_sections():
            if sec.is_null():
                continue
            attribs = Attributes(describe_sh_flags(sec.header.sh_flags))
            if attribs.executable == wants_executable:
                ret_secs.append(Section(sec.name,
                                        sec.data(),
                                        attribs,
                                        sec.header.sh_addr,
                                        len(sec.data())))

        return ret_secs

    def _get_sections_pe(self, executable=False):
        """Fetches section objects for a pe binary

        :executable: Boolean filter - return only executable sections (or not)
        :returns: A list of Section objects

        """
        pass

    def get_format(self):
        """Returns the file format of this binary

        :returns: A string of the file's format ('ELF', 'PE', etc)

        """
        return self.file_format

    def get_md5(self):
        """Calculates the binary's md5

        :returns: A uppercase hexdigest of the binary's md5

        """
        h = hashlib.md5()
        h.update(open(self.binpath, 'rb').read())
        return h.hexdigest().upper()

    def get_binary_size(self):
        """Calculates the number of bytes in the binary

        :returns: An integer number of bytes in the binary file

        """
        return len(open(self.binpath, 'rb').read())

    def get_arch(self):
        """Fetches the architecture of this binary

        :returns: The capstone representation of this binary's architecture

        """
        if self.file_format == 'ELF':
            machine = self.parser.header['e_machine']
            if machine == 'EM_386' or machine == 'EM_X86_64':
                return capstone.CS_ARCH_X86
            elif machine == 'EM_AARCH64':
                return capstone.CS_ARCH_ARM64
            elif machine == 'EM_ARM':
                return capstone.CS_ARCH_ARM
            elif machine == 'EM_MIPS':
                return capstone.CS_ARCH_MIPS
            elif machine == 'EM_PPC':
                return capstone.CS_ARCH_PPC
            else:
                return None

        elif self.file_format == 'PE':
            pass

    def get_mode(self):
        """Fetches the mode of this binary

        :returns: The capstone represtatnion of this binary's mode

        """
        if self.file_format == 'ELF':
            machine = self.parser.header['e_machine']
            le = capstone.CS_MODE_LITTLE_ENDIAN
            be = capstone.CS_MODE_BIG_ENDIAN
            endian = le if self.parser.little_endian else be
            if machine == 'EM_386':
                return capstone.CS_MODE_32
            elif machine == 'EM_X86_64':
                return capstone.CS_MODE_64
            elif machine == 'EM_AARCH64':
                return capstone.CS_MODE_64 + capstone.CS_MODE_ARM + endian
            elif machine == 'EM_ARM':
                return capstone.CS_MODE_32 + capstone.CS_MODE_ARM + endian
            elif machine == 'EM_MIPS':
                return capstone.CS_ARCH_MIPS + endian
            elif machine == 'EM_PPC':
                return capstone.CS_ARCH_PPC + endian
            else:
                return None

        elif self.file_format == 'PE':
            pass

    def get_entry_point(self):
        """Reads and returns the entry point of the binary

        :returns: Entrypoint of the bin

        """
        if self.file_format == 'ELF':
            return self.parser.header['e_entry']
        else:
            return None

    def get_debug_info(self):
        """If available, fetches the debug information for this binary

        :returns: TODO: A DebugInfo object for this binary or None

        """
        pass
