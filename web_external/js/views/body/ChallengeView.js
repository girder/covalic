covalic.views.ChallengeView = covalic.View.extend({
    events: {
        'click a.c-edit-challenge': function () {
            if (!this.editChallengeWidget) {
                this.editChallengeWidget = new covalic.views.EditChallengeWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            }
            this.editChallengeWidget.render();
        },

        'click .c-delete-challenge': function () {
            girder.confirm({
                text: 'Are you sure you want to delete the challenge <b>' +
                      this.model.escape('name') + '</b>?',
                yesText: 'Delete',
                escapedHtml: true,
                confirmCallback: _.bind(function () {
                    this.model.destroy({
                        progress: true
                    }).on('g:deleted', function () {
                        girder.events.trigger('g:alert', {
                            icon: 'ok',
                            text: 'Challenge deleted.',
                            type: 'success',
                            timeout: 4000
                        });
                        covalic.router.navigate('challenges', {trigger: true});
                    });
                }, this)
            });
        }
    },

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');
        if (settings.challenge) {
            this.model = settings.challenge;
            this._initWidgets();
            this.render();
        } else if (settings.id) {
            this.model = new girder.models.ChallengeModel();
            this.model.set('_id', settings.id);

            this.model.on('g:fetched', function () {
                this._initWidgets();
                this.render();
            }, this).fetch();
        }
    },

    _initWidgets: function () {
        this.phasesView = new covalic.views.ChallengePhasesView({
            challenge: this.model,
            parentView: this
        });
    },

    render: function () {
        this.$el.html(covalic.templates.challengePage({
            challenge: this.model,
            humanLink: '#challenge/n/' + encodeURIComponent(this.model.transformNameForUrl()),
            girder: girder
        }));

        girder.renderMarkdown(this.model.get('instructions') || '*No overview provided.*',
                              this.$('.c-challenge-instructions-container'));

        this.phasesView.setElement(this.$('.c-challenge-phase-container')).render();

        return this;
    }
});

covalic.router.route('challenge/:id', 'challenge', function (id) {
    // Fetch the challenge by id, then render the view.
    var challenge = new covalic.models.ChallengeModel();
    challenge.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.ChallengeView, {
            challenge: challenge
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});

covalic.router.route('challenge/n/:name', 'challengeByName', function (name) {
    var challenge = new covalic.models.ChallengeModel();
    challenge.findByName(name).once('c:found', function () {
        girder.events.trigger('g:navigateTo', covalic.views.ChallengeView, {
            challenge: challenge
        });
    }).once('c:notFound', function () {
        covalic.router.navigate('challenges', {trigger: true});
    });
});
