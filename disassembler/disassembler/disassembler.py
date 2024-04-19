'''
A Capstone-Engine based disassembler.
Ultimately, it does 4 things:
    1. Manages metadata for the current disassembly
    2. Determines which type of disassembly to conduct (new or existing)
    3. Launches a disassembly Strategy
    4. Launches each default Parser listed in the 'parsers' directory
'''

from disassembler_libs import binhandler, disassembly
from disassembler_libs.dbmanager import DBManager
from disassembler_libs import logger
from strategies.linear import Linear
from strategies.recursive import Recursive
from predisassemblers import predisassembler
import parsers
import sys
import ntpath


##################################
# Exceptions
##################################

class NoProjectInfo(Exception):
    def __init__(self, message=''):
        Exception.__init__(self, message)


class DisassemblyAlreadyExists(Exception):
    def __init__(self, message=''):
        Exception.__init__(self, message)


class UnknownDisassembler(Exception):
    def __init__(self, message=''):
        Exception.__init__(self, message)


class Disassembler:

    ##################################
    # Initialization
    ##################################

    def __init__(self, host, port, config, project_name,
                 disassembly_name, binpath=None):
        self.host = host
        self.port = port
        self.db_man = DBManager(host, port)
        self.project_name = project_name
        self.bin_path = binpath
        self.binary_name = ntpath.basename(binpath)
        self.disassembly_name = disassembly_name
        self.handler = None
        self.config = config
        self.disassembly = None

        self.log = logger.getLogger(__name__, self.config)

        self.db_man.load_project(self.project_name)

        # If we're given a binary path then this is a new disassembly
        if binpath is not None:
            self.handler = binhandler.BinHandler(binpath=binpath)
            self.disassembly = self.create_disassembly(self.handler)
            good_insert = self.db_man.add_disassembly(self.disassembly)

            # PARSER TESTING - UNCOMMENT THIS LINE
            # self.db_man.set_disassembly(self.disassembly_name)

            # PARSER TESTING - COMMENT THIS CHECK
            if not good_insert:
                raise DisassemblyAlreadyExists(('Failed to insert '
                                                'disassembly - '
                                                'disassembly by that '
                                                'name already exists!'))

        # Otherwise, this is an existing disassembly
        else:
            if not self.db_man.project_exists(self.project_name):
                raise NoProjectInfo('Project %s doesn\'t exist' % project_name)
            h = binhandler.BinHandler(db=self.db_man,
                                      project_name=self.project_name)
            self.handler = h

            self.disassembly = self.create_disassembly(self.handler)

    def create_disassembly(self, handler):
        return disassembly.Disassembly(self.disassembly_name,
                                       self.binary_name,
                                       handler.get_format(),
                                       handler.get_arch(),
                                       handler.get_mode(),
                                       handler.get_md5(),
                                       handler.get_binary_size(),
                                       handler.get_entry_point())

    ##################################
    # Disassembly
    ##################################

    def disassemble_file(self):
        sections = self.handler.get_sections()

        predis = predisassembler.make_predisassembler(self.config,
                                                       self.project_name,
                                                       self.disassembly_name,
                                                       self.handler)
        entry_points = [self.handler.get_entry_point()]
        try:
            ret = predis.run()
            if ret != None:
                for x in ret:
                    entry_points.append(x)
        except Exception as e:
            self.log.error("Predisassembler returned %s" % str(e))
            import traceback
            traceback.print_exc()

        # disassemble the file
        strat_name = self._get_dis_strategy()
        strat = None

        if strat_name == 'linear':
            strat = Linear(self.project_name, self.disassembly_name,
                           self.config, sections,
                           self.handler.get_arch(), self.handler.get_mode(),
                           entry_points)
        elif strat_name == 'recursive':
            strat = Recursive(self.project_name, self.disassembly_name,
                              self.config, sections,
                              self.handler.get_arch(), self.handler.get_mode(),
                              entry_points)
        else:
            raise UnknownDisassembler()

        # PARSER TESTING - COMMENT THIS LINE
        strat.disassemble()

        # do some extra parsing
        disable_parse = self.config.getboolean('Debugging', 'disable_parsers')
        if not disable_parse:
            self.do_parsers()

    def disassemble_string(self, string_val):
        self.log.error('Not Implemented!')
        pass

    def _get_dis_strategy(self):
        return self.config.get('Disassembler', 'strategy')

    ##################################
    # Parsers
    ##################################

    def get_parser_modules(self):
        modules = {}
        for module in parsers.__all__:
            __import__('parsers.' + module)
            modules['parsers.' + module] = sys.modules['parsers.' + module]
        return modules

    def get_parsers(self):
        modules = self.get_parser_modules()
        parsers = []
        for mod in modules:
            parsers.append(modules[mod].make_parser(self.config,
                                                    self.project_name,
                                                    self.disassembly_name))
        return parsers

    def do_parsers(self):
        parsers = self.get_parsers()
        for parser in parsers:
            parser.run()
