'''
Uses heuristics to identify any missed functions in
the disassembly and adds them to the database.
'''
from predisassembler import Predisassembler
import capstone
from disassembler_libs import logger

class ELFPredisassembler(Predisassembler):
    """Uses heuristicsish techniques to find the address of main."""

    def __init__(self, config, project_name, disassembly_name, handler):
        """Initializes a FunctionParser object.

        :config: A configuration file to read
        :project_name: The name of the project
        :disassembly_name: The name of the disassembly

        """
        Predisassembler.__init__(self, config, project_name, disassembly_name, handler)
        self.log = logger.getLogger(__name__)

    def run(self):
        '''
        This predisassembler will start disassembling linearly from the
        entry point until the first or second call.

        Non-PIE'd _start:
        0000000000400440 <_start>:
        400440:  31 ed                  xor    ebp,ebp
        400442:  49 89 d1               mov    r9,rdx
        400445:  5e                     pop    rsi
        400446:  48 89 e2               mov    rdx,rsp
        400449:  48 83 e4 f0            and    rsp,0xfffffffffffffff0
        40044d:  50                     push   rax
        40044e:  54                     push   rsp
        40044f:  49 c7 c0 c0 05 40 00   mov    r8,0x4005c0
        400456:  48 c7 c1 50 05 40 00   mov    rcx,0x400550

                                            WE WANT THIS ADDRESS
                                                      |
                                                      V
        40045d:  48 c7 c7 2d 05 40 00   mov    rdi,0x40052d   
        400464:  e8 b7 ff ff ff         call   400420 <__libc_start_main@plt>
        400469:  f4                     hlt
        40046a:  66 0f 1f 44 00 00      nop    WORD PTR [rax+rax*1+0x0]

        PIC'd _start:
        660:  31 ed                 xor   ebp,ebp
        662:  49 89 d1              mov   r9,rdx
        665:  5e                    pop   rsi
        666:  48 89 e2              mov   rdx,rsp
        669:  48 83 e4 f0           and   rsp,0xfffffffffffffff0
        66d:  50                    push  rax
        66e:  54                    push  rsp
        66f:  4c 8d 05 9a 01 00 00  lea   r8,[rip+0x19a]        # 810 <__libc_csu_fini>
        676:  48 8d 0d 23 01 00 00  lea   rcx,[rip+0x123]        # 7a0 <__libc_csu_init>
                                        WE WANT THIS ADDRESS
                                                  |
                                                  V
        67d:  48 8d 3d f1 00 00 00  lea   rdi,[rip+0xf1]        # 775 <main>
        684:  e8 a7 ff ff ff        call  630 <__libc_start_main@plt>

        32-bit PIC:
        000004a0 <_start>:
         4a0:   31 ed                   xor    ebp,ebp
         4a2:   5e                      pop    esi
         4a3:   89 e1                   mov    ecx,esp
         4a5:   83 e4 f0                and    esp,0xfffffff0
         4a8:   50                      push   eax
         4a9:   54                      push   esp
         4aa:   52                      push   edx
         4ab:   e8 22 00 00 00          call   4d2 <_start+0x32>
                                        WE WANT THIS ADDRESS (eip + 1b50)
                                                  |
                                                  V
         4b0:   81 c3 50 1b 00 00       add    ebx,0x1b50
         4b6:   8d 83 b0 e6 ff ff       lea    eax,[ebx-0x1950]
         4bc:   50                      push   eax
         4bd:   8d 83 40 e6 ff ff       lea    eax,[ebx-0x19c0]
         4c3:   50                      push   eax
         4c4:   51                      push   ecx
         4c5:   56                      push   esi
         4c6:   ff b3 f4 ff ff ff       push   DWORD PTR [ebx-0xc]
         4cc:   e8 bf ff ff ff          call   490 <__libc_start_main@plt>
         4d1:   f4                      hlt
         4d2:   8b 1c 24                mov    ebx,DWORD PTR [esp]
         4d5:   c3                      ret
        '''
        self.log.info('Predisassembling the ELF')
        md = capstone.Cs(self.handler.get_arch(), self.handler.get_mode())
        md.detail = True
        # Doesn't work for now
        # md.skipdata_setup = ('db', None, None)
        md.skipdata = True

        addr_counter = self.handler.get_entry_point()

        exe_sections = self.handler.get_executable_sections()
        section = None
        for sec in exe_sections:
            if sec.contains_addr(addr_counter):
                section = sec
        if not section:
            return None
        del sec

        abs_addr = addr_counter
        addr_counter = abs_addr - section.base_addr

        dis_gen = md.disasm(section.data[addr_counter:], abs_addr)

        inst_buff = []
        count = 0
        n = 200
        while True:
            inst = None
            try:
                # if detail mode is on and the instruction isn't
                # disassemble-able then this will throw a ValueError
                # for NULL dereferencing the .detail field.
                inst = dis_gen.next()
                addr_counter += len(inst.bytes)
                abs_addr += len(inst.bytes)
                if md.detail is False:
                    md.detail = True
                    # Generator needs to be reseeded when we change detail
                    # setting - might be a bug in capstone's skipdata
                    dis_gen = md.disasm(section.data[addr_counter:], abs_addr)
            except ValueError:
                md.detail = False
                dis_gen = md.disasm(section.data[addr_counter:], abs_addr)
                continue
            except StopIteration:
                break

            instruction = self.get_instruction(inst)  # Parent class method

            #print hex(abs_addr-len(instruction.my_bytes)), instruction.mnemonic, '\t', str(instruction.operands)

            if self.heuristics.is_call(inst):
                # we have a call, so look back one instruction and grab that relative addr
                # look back one instruction
                inst = inst_buff[-1]

                machine = self.handler.parser.header['e_machine']
                if machine == 'EM_386':
                    pass
                    #if len(inst.operands) == 1:
                    #    operand = inst.operands[0]
                    #    if operand['type'] == 'imm':
                    #        return [operand['imm']['val']]

                elif (machine == 'EM_X86_64' or 
                        self.handler.get_arch() == capstone.CS_ARCH_ARM64):
                    if len(inst.operands) == 2:
                        operand = inst.operands[1]
                        if operand['type'] == 'imm':
                            return [operand['imm']['val']]

            """
            0x00400f78: 31ed                        xor     ebp, ebp
            0x00400f7a: 4989d1                      mov     r9, rdx
            0x00400f7d: 5e                          pop     rsi
            0x00400f7e: 4889e2                      mov     rdx, rsp
            0x00400f81: 4883e4f0                    and     rsp, 0x-10
            0x00400f85: 50                          push    rax
            0x00400f86: 54                          push    rsp
            0x00400f87: 49c7c070174000              mov     r8, 0x401770
            0x00400f8e: 48c7c1e0164000              mov     rcx, 0x4016e0
            0x00400f95: 48c7c790104000              mov     rdi, 0x401090
            0x00400f9c: e83f010000                  call    0x4010e0
            """

            inst_buff.append(instruction)
            count += 1

            # if we haven't found anything in n instructions, break
            if count == n:
                break
        return None

