"""
A parent class for disassembler strategies.
"""


from bson.binary import Binary
from collections import namedtuple
from disassembler_libs.instruction import Instruction
from disassembler_libs.dbmanager import generate_db_manager
from disassembler_libs import logger
import multiprocessing
from disassembler_libs.heuristics_factory import HeuristicsFactory

# Used to shovel data among functions internally
MyCsInsn = namedtuple('MyCsInsn', 'address bytes mnemonic')


def dis_nx_sec(strat, config, proj_name, dis_name, sec):
    """Disassemble a non-executable section.

    :strat: An initialization of the strategy to use
    :config: A configuration file to read
    :proj_name: The name of the project
    :dis_name: The name of the disassembly
    :sec: The section to disassemble
    :returns: None

    """
    db_man = generate_db_manager(config, proj_name, dis_name)
    strat.disassemble_non_executable_section(db_man, sec)


class Strategy(object):
    """A disassembly strategy - to be extended by children. """

    def __init__(self, project_name, dis_name,
                 config, sections, arch, mode, entry_points):
        """ Initializes a strategy object.

        :project_name: The name of the project
        :dis_name: The name of the disassembly
        :config: A configuration file to read
        :sections: A list of sections to disassemble
        :arch: The machine architecture of the disassembly
        :mode: The mode of the arch
        :entry_point: The address of the original entry point in the bin

        """
        self.proj_name = project_name
        self.dis_name = dis_name
        self.config = config
        self.sections = sections
        self.arch = arch
        self.mode = mode
        self.entry_points = entry_points
        fact = HeuristicsFactory(config, arch, mode)
        self.heuristics = fact.create_heuristics()

    def disassemble(self):
        """Begins the disassembly of each section.

        :returns: None

        """
        db_man = generate_db_manager(self.config,
                                     self.proj_name,
                                     self.dis_name)

        for sec in self.sections:
            db_man.add_section(sec)

        ex = [s for s in self.sections if s.is_executable()]
        nx = [s for s in self.sections if not s.is_executable()]

        self.dis_executable_sections(ex)
        self.dis_non_executable_sections(nx)

    def get_instruction(self, inst):
        """Turns a MyCsInsn or real CsInsn into our instruction object.

        :inst: The MyCsInsn or capstone CsInsn to convert
        :returns: An instruction object

        """
        is_text = inst.mnemonic != '.byte'

        disp = None if is_text else 'bytes'

        operands = self.heuristics.process_operands(inst) if is_text else None

        inst_ob = Instruction(inst.address,  # relative address
                              is_text,  # text or data
                              Binary(str(inst.bytes)),  # my_bytes
                              inst.mnemonic,  # mnemonic
                              operands,  # operands
                              disp)  # how data should be displayed

        return inst_ob

    def disassemble_non_executable_section(self, db_man, sec):
        """Disassemble a non-executable section.

        :db_man: The database manager to use
        :sec: The section to disassemble
        :returns: None

        """

        log = logger.getLogger(__name__, self.config)
        log.info(('Disassembling non_executable section: '
                  '%s -- Length: %d' % (sec.name, sec.size)))

        # Batch instruction insertion greatly speeds up query time
        inst_buff = []
        count = 0
        n = 200
        for byte_counter, byte in enumerate(sec.data):
            # XXX: Real CsInsn are hard to make, so we're using a named
            # tuple here. Update as needed.
            tuple_inst = MyCsInsn(sec.base_addr + byte_counter,
                                       Binary(str(byte)),
                                       '.byte')
            instruction = self.get_instruction(tuple_inst)
            inst_buff.append(instruction)
            count += 1
            if count % n == 0:
                db_man.batch_add_instructions(sec.name, inst_buff)
                inst_buff = []

        if len(inst_buff) > 0:
            db_man.batch_add_instructions(sec.name, inst_buff)

    def dis_non_executable_sections(self, sections):
        """Disassemble a list of non-executable sections.

        :sections: The list of sections to disassemble
        :returns: None

        """
        disable_multi = self.config.getboolean('Debugging',
                                               'disable_multiprocessing')
        if disable_multi:
            for sec in sections:
                dis_nx_sec(self, self.config, self.proj_name,
                           self.dis_name, sec)
        else:
            p = multiprocessing.Pool(self.config.getint('General',
                                                        'num_procs'))

            # Setting self.sections is a Hack to prevent us
            # from pickling every section when
            # we do apply_async
            saved = self.sections
            for sec in sections:
                self.sections = [sec]
                p.apply_async(dis_nx_sec,
                              args=(self, self.config, self.proj_name,
                                    self.dis_name, sec))

            p.close()
            p.join()
            self.sections = saved
