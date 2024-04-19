import {spawn} from 'child_process';
import {Meteor} from 'meteor/meteor';
import {GDBDB} from '/lib/collections';
import {check} from 'meteor/check';

export default () => {
    Meteor.methods({
        'exec.gdb'(args) {
            gdb = spawn('gdb', ['--args', 'ls', '-la']);

            gdb.stdout.on('data', (data) => {
                console.log(`stdout: ${data}`);
            });

            gdb.stderr.on('data', (data) => {
                console.log(`stderr: ${data}`);
            });

            gdb.on('close', (code) => {
                console.log(`child process exited with code ${code}`);
            });
        }
    });
}
