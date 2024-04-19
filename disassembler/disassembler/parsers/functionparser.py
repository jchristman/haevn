'''
Uses heuristics to identify any missed functions in
the disassembly and adds them to the database.
'''

from parser import Parser
from disassembler_libs import logger


class FunctionParser(Parser):
    """Uses heuristics to find any missed functions in the disassembly."""

    def __init__(self, config, project_name, disassembly_name):
        """Initializes a FunctionParser object.

        :config: A configuration file to read
        :project_name: The name of the project
        :disassembly_name: The name of the disassembly

        """
        Parser.__init__(self, config, project_name, disassembly_name)
        self.log = logger.getLogger(__name__)

    def run(self):
        '''
        Some basic thoughts for this parser:
        I think that both this class and the 'recursive' strategy should
        have a handle to another class that actually does the heurstics
        depending on arch and mode types.

        I think this class should work by:
        1. Retrieve all of the text instructions from the db
            (that functionality still needs to be added to the dbmanager)
        2. Iterate through them all and ask the other hueristics class
           something like:
            hueristics.looks_like_func_start(instruction)
           and
            heuristics.looks_like_func_end(instruction)
        3. Add a Function label to the db if it doesn't already exist (I think
           I already wrote that functionality, but you should double check)

        That way, both this and the 'recursive' strategy should be able to use
        the hueristics class.

        '''
        pass


def make_parser(config, project_name, disassembly_name):
    '''
    Factory for FuctionParser
    '''
    return FunctionParser(config, project_name, disassembly_name)
