if (Meteor.isServer) {
    Exec = {};

    var Fiber = Npm.require('fibers');
    var Process = Npm.require('child_process');

    Exec.run = function (command, args, stdoutHandler, stderrHandler) {
        var proc = Process.spawn(command, args, {
            detached : true,
            stdio : ['ignore', 'pipe', 'pipe']   
        });
        proc.unref();
        
        proc.stdout.on('data', Meteor.bindEnvironment(function (data) {
            stdoutHandler(data.toString());
        }));

        proc.stderr.on('data', Meteor.bindEnvironment(function (data) {
            stderrHandler(data.toString());
        }));
            
        proc.on('close', Meteor.bindEnvironment(function (code) {
            stdoutHandler("Child process exited with code: " + code.toString());
        }));
    };
}
