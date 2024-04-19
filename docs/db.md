Database
=========

Haevn uses an instance of mongodb. This document should be kept up-to-date with the current state of the architecture of the db.

Architecture
=============

Database name: Haevn|Meteor

Collections:

* ~~project\_information~~
    * ~~project_name     : str~~
    * ~~\_id              : bson\_objectid~~
    * ~~disassembly\_ids  : [bson\_objectid]    // Foreign key (disassemblies)~~

* disassemblies:
    * dis\_name         : str
    * \_id              : bson\_objectid
    * binary\_name      : str
    * binary\_format    : str
    * architecture     : int          //Corresponding to CS_ARCH
    * mode             : int          //Corresponding to CS_MODE 
    * md5              : hex\_str 
    * size             : int

* {BIN\_HASH}\_disassembly (is\_text=true )
    * ~~project\_id       : bson\_objectid  //Foreign key (project\_information)~~
    * ~~dis\_id           : bson\_objectid  //Foreign key (disassemblies)~~
    * ~~r\_addr           : int            //Relative address~~
    * __addr             : int            // Absolute address to save time client-side. Don't want to look up base addr__
    * is\_text          : bool
    * my\_bytes         : byte\_str       // Maybe not publish to clients?
    * ~~sec\_id           : bson\_objectid  //Foreign key (labels)~~
    * __sec\_name         : str            // Can be used to look up the section if need be and saves a lookup every line of dis__
    * mnemonic         : str
    * operands         : [{ operand : str
                          type    : mem|reg|imm|loc|var
                          (if imm, also have - disp : hex|dec|oct|bin|str)
                        }]

* {BIN\_HASH}\_disassembly (is\_text=false )
    * ~~project\_id       : bson\_objectid  //Foreign key (project_information)~~
    * ~~dis\_id           : bson\_objectid  //Foreign key (disassemblies)~~
    * ~~r\_addr           : int            //Relative address~~
    * __addr             : int            // Absolute address to save time client-side. Don't want to look up base addr__
    * is\_text          : bool
    * my\_bytes         : byte\_str       // Maybe not publish to clients?
    * disp             : bytes|str
    * ~~sec\_id           : bson\_objectid  //Foreign key (labels)~~
    * __sec\_name         : str            // Can be used to look up the section if need be and saves a lookup every line of dis__
    * mnemonic         : str

* {BIN\_HASH}\_disassembly\_funcs
    * ~~project\_id       : bson\_objectid      //Foreign key (project_information)~~
    * ~~dis\_id           : bson\_objectid      //Foreign key (disassemblies)~~
    * ~~sec\_id           : bson\_objectid      //Foreign key (labels)~~
    * __sec\_name         : str            // Can be used to look up the section if need be and saves a lookup every line of dis__
    * ~~type             : func|str|sec|loc~~
    * name             : str
    * ~~r\_start\_addr     : int           //Relative start address~~
    * ~~r\_end\_addr       : int           //Relative end address~~
    * __start\_addr       : int           //Absolute start address__
    * __end\_addr         : int           //Absolute end address__
    * l\_vars           : [name : str]  //Local variables

* {BIN\_HASH}\_disassembly\_strs
    * ~~project\_id       : bson\_objectid      //Foreign key (project_information)~~
    * ~~dis\_id           : bson\_objectid      //Foreign key (disassemblies)~~
    * ~~sec\_id           : bson\_objectid      //Foreign key (labels)~~
    * __sec\_name         : str            // Can be used to look up the section if need be and saves a lookup every line of dis__
    * ~~type             : func|str|sec|loc~~
    * name             : str
    * ~~r\_addr           : int~~
    * __addr             : int__
    * __data             : str         // Theoretically different than the label name? like str_abc = 'abc'__

* {BIN\_HASH}\_disassembly\_secs
    * ~~project\_id       : bson\_objectid      //Foreign key (project_information)~~
    * ~~dis\_id           : bson\_objectid      //Foreign key (disassemblies)~~
    * ~~type             : func|str|sec|loc~~
    * name             : str
    * base\_addr        : int
    * size             : int
    * attribs          : str

* {BIN\_HASH}\_disassembly\_locs
    * ~~project\_id       : bson\_objectid      //Foreign key (project_information)~~
    * ~~dis\_id           : bson\_objectid      //Foreign key (disassemblies)~~
    * ~~sec\_id           : bson\_objectid      //Foreign key (labels)~~
    * __sec\_name         : str            // Can be used to look up the section if need be and saves a lookup every line of dis__
    * ~~type             : func|str|sec|loc~~
    * name             : str
    * ~~r\_addr         : int~~
    * __addr             : int__

I think that xrefs is unnecessary. The only non-foreign key is the base_addr? We should
probably just build xrefs directly into the individual instructions.

* ~~xrefs~~
    * ~~project\_id       : bson\_objectid     //Foreign key (project_information)~~
    * ~~dis\_id           : bson\_objectid     //Foreign key (disassemblies)~~
    * ~~base\_addr        : int               //Relative address of the instruction doing the referencing~~
    * ~~base\_sec_id      : bson\_objectid     //Foreign key (labels)~~
    * ~~label\_id         : bson\_objectid     //Foreign key (labels)~~
