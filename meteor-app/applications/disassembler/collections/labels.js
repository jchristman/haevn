Labels = new Meteor.Collection('labels');

if (Meteor.isClient) {
    Meteor.subscribe('labels');
}

if (Meteor.isServer) {
    Meteor.publish('labels', function() {
        return Labels.find();
    });
}

/*Chat.allow({
    'insert': function(userId, doc) {
        return true;
    }
});*/
