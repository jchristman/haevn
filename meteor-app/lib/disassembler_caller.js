if (Meteor.isServer) {
    Meteor.methods({
        disassemble : function(fsFile) {
            var loc = '../../../cfs/files/MeteorOS_FS/MeteorOS_FS-' + fsFile._id + '-' + fsFile.original.name;
            Meteor.call('consoleExecSync', 'disassemble', { fileLoc : loc });
        }
    });
}
