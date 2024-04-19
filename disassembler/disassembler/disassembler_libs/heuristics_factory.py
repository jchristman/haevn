import capstone
import disassembler_libs.heuristics_archs.arm as arm
import disassembler_libs.heuristics_archs.arm64 as arm64
import disassembler_libs.heuristics_archs.mips as mips
import disassembler_libs.heuristics_archs.ppc as ppc
import disassembler_libs.heuristics_archs.x86 as x86

OP_ARCHS = {capstone.CS_ARCH_ARM:   arm.arm,
            capstone.CS_ARCH_ARM64: arm64.arm64,
            capstone.CS_ARCH_MIPS:  mips.mips,
            capstone.CS_ARCH_PPC:   ppc.ppc,
            capstone.CS_ARCH_X86:   x86.x86}


class HeuristicsFactory(object):
    """A factory to construct a heuristics object"""

    def __init__(self, config, arch, mode):
        """Initializes a heuristicsfactory.

        :config: Configuration file to read from
        :arch: Machine architecture heuristics will apply to
        :mode: Mode of that architecture

        """
        self._config = config
        self._arch = arch
        self._mode = mode

    def create_heuristics(self):
        """Creates a heuristics object from the given arch and mode.

        :returns: The applicable heuristics object

        """
        if self._arch in OP_ARCHS:
            return OP_ARCHS[self._arch](self._config, self._arch, self._mode)
