Chat = new Meteor.Collection('chat');

if (Meteor.isClient) {
    Meteor.subscribe('chat');
}

if (Meteor.isServer) {
    Meteor.publish('chat', function() {
        return Chat.find();
    });
}

Chat.allow({
    'insert': function(userId, doc) {
        return true;
    }
});
