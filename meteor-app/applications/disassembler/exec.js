if (Meteor.isServer) {
    Meteor.methods({
        disassembleFile : function(fileId) {
            binary = Binaries.findOne({_id : fileId});
            cmd = 'python';
            args = '../../../../../disassembler/disassembler_cli.py -dh localhost -dp 3001 ' + 
                '-proj "Test_Project_1" -d "CSAW_CTF_Bin_100" ' +
                '-f ../../../cfs/files/binaries/binaries-' + binary._id + '-' + binary.original.name;
            Exec.run(cmd, args.split(' '), consoleInsert, consoleInsert);
        }
    });
}
