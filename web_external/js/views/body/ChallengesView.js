covalic.views.ChallengesView = covalic.View.extend({
    events: {
        'change .c-challenges-filter': 'challengeFilterChanged'
    },

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');

        this.timeframe = settings.timeframe || 'all';

        var params = { timeframe: this.timeframe };

        this.collection = new covalic.collections.ChallengeCollection();
        this.collection.on('g:changed', function () {
            this.render();
        }, this).fetch(params);

        this.paginateWidget = new girder.views.PaginateWidget({
            collection: this.collection,
            parentView: this
        });

        this.searchWidget = new girder.views.SearchFieldWidget({
            placeholder: 'Search challenges...',
            types: ['challenge.challenge'],
            getInfoCallback: function (type, obj) {
                if (type === 'challenge.challenge') {
                    return {
                        text: obj.name,
                        icon: 'flag-checkered'
                    };
                }
            },
            parentView: this
        }).on('g:resultClicked', this._gotoChallenge, this);
    },

    render: function () {
        this.$el.html(covalic.templates.challengeList({
            challenges: this.collection.models,
            admin: !!(girder.currentUser && girder.currentUser.get('admin')),
            girder: girder,
            timeframe: this.timeframe
        }));

        this.paginateWidget.setElement(this.$('.c-challenge-pagination')).render();
        this.searchWidget.setElement(this.$('.c-challenges-search-container')).render();

        this.$('.c-tooltip').tooltip({
            delay: 100,
            container: this.$el,
            placement: function (tip, el) {
                return $(el).attr('placement') || 'top';
            }
        });

        return this;
    },

    createDialog: function () {
        new covalic.views.EditChallengeWidget({
            el: $('#g-dialog-container'),
            parentView: this
        }).on('g:saved', function (challenge) {
            covalic.router.navigate('challenge/' + challenge.get('_id'), {
                trigger: true
            });
        }, this).render();
    },

    _gotoChallenge: function (challenge) {
        covalic.router.navigate('challenge/' + challenge.id, {trigger: true});
    },

    challengeFilterChanged: function (e) {
        var select = e.currentTarget;
        this.timeframe = select.value;
        covalic.router.navigate('challenges?timeframe=' + this.timeframe, {
            replace: true});

        var params = { timeframe: this.timeframe };
        // FIXME fetch() ignores params when reset is true
        // Workaround: set params explicitly
        // this.collection.fetch(params, true);
        this.collection.params = params;
        this.collection.fetch(null, true);
    }
});

covalic.router.route('challenges', 'challenges', function (params) {
    params = girder.parseQueryString(params);

    var timeframe = null;
    if (_.has(params, 'timeframe')) {
        timeframe = params.timeframe;
    }

    girder.events.trigger('g:navigateTo', covalic.views.ChallengesView, {
        timeframe: timeframe
    });
});
