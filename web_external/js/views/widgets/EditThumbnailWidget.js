covalic.views.EditThumbnailWidget = covalic.View.extend({
    events: {

    },

    initialize: function () {
        
    }
});

covalic.router.route('challenge/:id/thumbnail', 'challengeThumbnail', function (id) {
    // Fetch the phase by id, then render the view.
    var challenge = new covalic.models.ChallengeModel();
    challenge.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.EditThumbnailWidget, {
            challenge: challenge
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
