if (Meteor.isClient) {
    Template.chat.helpers({
        chatMessages : function() {
            return Chat.find();
        }
    });

    Template.chat.events = {
        'keypress #chatMessage' : function(event) {
            if (event.keyCode == 13) {
                event.stopPropagation();
                var message = $('#chatMessage').val();
                var username = Meteor.user().username;
                
                Chat.insert({
                    username: username,
                    message: message,
                    timestamp: Date.now()
                }, function(err, id) {
                    $('#chatMessage').val('');
                });
            }
        }
    }

    Template.chat.rendered = function() {
        
    }
}
