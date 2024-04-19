'''
A predisassembler is something to pre-seed the entry points to a 
executable disassembler. This is needed because:
    - ELFs have __libc_start_main, which has &main passed as an argument
    - PEs have something
    - Mach-O???
'''
from disassembler_libs.dbmanager import generate_db_manager
from disassembler_libs.heuristics_factory import HeuristicsFactory
from bson.binary import Binary
from disassembler_libs.instruction import Instruction


class Predisassembler(object):
    """An object that implements pre-parsing a disassembly's
    executable sections.
    """

    def __init__(self, config, project_name, disassembly_name, handler):
        """Initializes a predisassembler object.

        :config: A configuration file to read
        :project_name: The name of the project
        :disassembly_name: The name of the disassembly

        """
        self.config = config
        self.project_name = project_name
        self.disassembly_name = disassembly_name
        self.handler = handler
        fact = HeuristicsFactory(config, self.handler.get_arch(),
                self.handler.get_mode())
        self.heuristics = fact.create_heuristics()

    def run(self):
        """Run the given parser. This should be implemented by all children.
        It MUST return a list of addresses to start disassembly with."""
        #return []
        raise NotImplementedError
    
    def get_instruction(self, inst):
        """Turns a MyCsInsn into our internal instruction object.

        :inst: The MyCsInsn to convert
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


def make_predisassembler(config, project_name, disassembly_name, handler):
    """Acts as a factory and creates an instance of the parser.
    This should be implemented by all children.

    :config: A configuration file to read
    :project_name: The name of the project
    :disassembly_name: The name of the disassembly

    """
    db_man = generate_db_manager(config, project_name, disassembly_name)
    dis = db_man.get_disassembly_record_current()
    if dis['binary_format'] == "PE":
        return Predisassembler(config, project_name, disassembly_name, handler)
    elif dis['binary_format'] == "ELF":
        import elf
        return elf.ELFPredisassembler(config, project_name, disassembly_name, handler)
    elif dis['binary_format'] == "MACHO":
        return Predisassembler(config, project_name, disassembly_name, handler)
    else:
        return Predisassembler(config, project_name, disassembly_name, handler)

