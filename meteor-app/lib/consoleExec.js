var valid_commands = ['disassemble']

if (Meteor.isServer) {
    Meteor.methods({
        consoleExecSync : function(cmd, args) {
            if (cmd == 'disassemble') {
                cmd = 'python';
                args = '../../../../../../disassembler/disassembler/disassembler_cli.py -p test -d test -f ' + args.fileLoc;
                Exec.run(cmd, args.split(' '), consoleInsert, consoleInsert);
            } else {
                cmd = cmd.split(' ')
                Exec.run(cmd[0], cmd.slice(1, cmd.length), consoleInsert, consoleInsert);
                consoleInsert(cmd + " is an invalid command. Valid commands are: " + valid_commands.join());
            }
        }
    });

    consoleInsert = function(_data) {
        _data.split('\n').forEach(function(__data) {
            if (__data != "") {
                Console.insert({
                    timestamp : new Date().getTime(),
                    data : __data
                });
            }
        });
    }
}
