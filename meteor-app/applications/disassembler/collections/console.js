Console = new Meteor.Collection('console');

if (Meteor.isClient) {
    Meteor.subscribe('console');
}

if (Meteor.isServer) {
    Meteor.publish('console', function() {
        return Console.find();
    });
}

/*Chat.allow({
    'insert': function(userId, doc) {
        return true;
    }
});*/
