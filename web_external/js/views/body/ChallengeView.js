covalic.views.ChallengeView = covalic.View.extend({
    events: {
        'click a.c-edit-challenge': function () {
            new covalic.views.EditChallengeWidget({
                el: $('#g-dialog-container'),
                model: this.model,
                parentView: this
            }).on('g:saved', function (challenge) {
                this.render();
            }, this).render();
        },

        'click .c-challenge-access-control': function () {
            if (!this.accessWidget) {
                this.accessWidget = new girder.views.AccessWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    modelType: 'challenge',
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            } else {
                this.accessWidget.render();
            }
        }
    },

    initialize: function (settings) {
        girder.cancelRestRequests('fetch');
        if (settings.challenge) {
            this.model = settings.challenge;
            this.render();
        } else if (settings.id) {
            this.model = new girder.models.ChallengeModel();
            this.model.set('_id', settings.id);

            this.model.on('g:fetched', function() {
               this.render();
            }, this).fetch();
        }
    },

    render: function () {
        this.$el.html(covalic.templates.challengePage({
            challenge: this.model,
            girder: girder
        }));

        var instructionsContainer = this.$('.c-challenge-instructions-container');
        if (this.model.get('instructions')) {
            girder.renderMarkdown(this.model.get('instructions'),
                                  instructionsContainer);
            instructionsContainer.show();
        } else {
            instructionsContainer.hide();
        }

        new covalic.views.ChallengePhasesView({
            el: this.$('.c-challenge-phase-container'),
            challenge: this.model,
            parentView: this
        }).render();

        return this;
    }
});

covalic.router.route('challenge/:id', 'challenge', function(id, params) {
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
