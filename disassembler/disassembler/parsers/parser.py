'''
A parser is some extra functionality that runs after a binary
has been disassembled. This adds more detail to the disassembly
such as string finding, xref finding, function finding, etc.
'''
import multiprocessing


class Parser(object):
    """An object that implements additional parsing of a disassembly. """

    def __init__(self, config, project_name, disassembly_name):
        """Initializes a parser object.

        :config: A configuration file to read
        :project_name: The name of the project
        :disassembly_name: The name of the disassembly

        """
        self.config = config
        self.project_name = project_name
        self.disassembly_name = disassembly_name
        p = multiprocessing.Pool
        self.m_pool = p(config.getint('General', 'num_procs'))

    def run(self):
        """Run the given parser. This should be implemented by all children."""
        raise NotImplementedError


def make_parser(config, project_name, disassembly_name):
    """Acts as a factory and creates an instance of the parser.
    This should be implemented by all children.

    :config: A configuration file to read
    :project_name: The name of the project
    :disassembly_name: The name of the disassembly

    """
    raise NotImplementedError
