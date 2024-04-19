if (Meteor.isClient) {
    var oldTimestamp = '';

    Template.console.helpers({
        consoleMessages : function() {
            return Console.find();
        }
    });

    Template.console_message.helpers({
        isNewTimestamp : function(timestamp) {
            timestamp = prettifyDate(timestamp);
            if (timestamp == oldTimestamp)
                return false;
            oldTimestamp = timestamp;
            return true;
        }
    });

    Template.console.events = {
        'keypress #consoleMessage' : function(event) {
            if (event.charCode == 13) {
                event.stopPropagation();
                var message = $('#consoleMessage').val();
                Meteor.call('consoleExecSync', message);
                $('#consoleMessage').val('');
            }
        }
    }

    Template.console_message.rendered = function() {
        $('#consoleBox').scrollTop( $('#consoleBoxContent').height() );
    }
}
