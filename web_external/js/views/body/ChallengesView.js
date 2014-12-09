covalic.views.ChallengesView = covalic.View.extend({

    events: {
        'click a.c-challenge-link': function (event) {
            var cid = $(event.currentTarget).attr('c-challenge-cid');
            girder.router.navigate('challenge/' + this.collection.get(cid).id, {trigger: true});
        }
    },

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');
        this.collection = new girder.collections.ChallengeCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch();
    },


    render: function() {
        this.$el.html(covalic.templates.challengeList({challenges: this.collection.models}));

        return this;
    }



});

girder.router.route('challenges', 'challenges', function (params) {
    girder.events.trigger('g:navigateTo', covalic.views.ChallengesView, params || {});
    girder.events.trigger('g:highlightItem', 'ChallengesView');
});
