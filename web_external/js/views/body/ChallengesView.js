covalic.views.ChallengesView = covalic.View.extend({

    events: {
        'click a.c-challenge-link': function (event) {
            var cid = $(event.currentTarget).attr('c-challenge-cid');
            covalic.router.navigate('challenge/' + this.collection.get(cid).id, {trigger: true});
        },

        'click .c-challenge-create-button': 'createDialog'
    },

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');

        this.collection = new covalic.collections.ChallengeCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch();

        this.paginateWidget = new girder.views.PaginateWidget({
            collection: this.collection,
            parentView: this
        });

        this.searchWidget = new girder.views.SearchFieldWidget({
            placeholder: 'Search challenges...',
            types: ['challenge_challenge'],
            parentView: this
        }).on('g:resultClicked', this._gotoCollection, this);
    },

    render: function () {
        this.$el.html(covalic.templates.challengeList({
            challenges: this.collection.models,
            admin: !!(girder.currentUser && girder.currentUser.get('admin'))
        }));

        this.paginateWidget.setElement(this.$('.c-challenge-pagination')).render();
        this.searchWidget.setElement(this.$('.c-challenges-search-container')).render();

        return this;
    },

    createDialog: function () {
        new covalic.views.EditChallengeWidget({
            el: $('#g-dialog-container'),
            parentView: this
        }).on('g:saved', function (challenge) {
            girder.router.navigate('challenge/' + challenge.get('_id'), {
                trigger: true
            });
    }, this).render();
    }
});

covalic.router.route('challenges', 'challenges', function (params) {
    girder.events.trigger('g:navigateTo', covalic.views.ChallengesView);
    girder.events.trigger('g:highlightItem', 'ChallengesView');
});
