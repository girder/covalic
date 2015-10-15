covalic.views.NewChallenge = covalic.View.extend({

});

covalic.router.route('challenge/new', 'newChallenge', function () {
    girder.events.trigger('g:navigateTo', covalic.views.NewChallenge);
});
