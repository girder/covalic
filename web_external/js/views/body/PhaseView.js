covalic.views.PhaseView = covalic.View.extend({

    events: {
        'click #c-submit-phase-dataset': function(event) {
            covalic.router.navigate('phase/' + this.model.get('_id') + '/submit', {trigger: true});
        },
        'click #c-join-phase': function(event) {
            if (!girder.currentUser) {
                girder.events.trigger('g:loginUi');
            } else {
                var path = 'challenge_phase/' + this.model.get('_id') + '/participant';
                var type = 'POST';
                girder.restRequest({
                    path: path,
                    type: type,
                    error: null // TODO what?
                }).done(_.bind(function (resp) {
                    var participantGroupId = this.model.get('participantGroupId');
                    girder.currentUser.addToGroup(participantGroupId);
                    girder.events.trigger('c:joinPhase');
                }, this));
            }
        },
        'click a.c-challenge-link': function(event) {
            var id = $(event.currentTarget).attr('c-challenge-id');
            covalic.router.navigate('challenge/' + id, {trigger: true});
        }
    },

    initialize: function (settings) {
        girder.events.on('c:joinPhase', this.render, this);
        girder.cancelRestRequests('fetch');
        if (settings.phase) {
            this.model = settings.phase;

            if (this.challenge) {
                this.render();
            } else {
                this.challenge = new covalic.models.ChallengeModel();
                this.challenge.set({
                    _id: this.model.get('challengeId')
                }).on('g:fetched', function () {
                    this.render();
                }, this).fetch();
            }
        } else if (settings.id) {
            this.model = new girder.models.PhaseModel();
            this.model.set('_id', settings.id);

            this.model.on('g:fetched', function() {
               this.render();
            }, this).fetch();
        }

    },

    isUserInChallenge: function() {
        if (!girder.currentUser) {
            return false;
        }
        var participantGroupId = this.model.get('participantGroupId');
        var userGroupIds = girder.currentUser.attributes.groups;
        return _.contains(userGroupIds, participantGroupId);
    },

    render: function () {
        this.$el.html(covalic.templates.phasePage({
            phase: this.model,
            userInChallenge: this.isUserInChallenge(),
            challenge: this.challenge
        }));

        return this;
    }
});

covalic.router.route('phase/:id', 'phase', function(id, params) {
    // Fetch the phase by id, then render the view.
    var phase = new covalic.models.PhaseModel();
    phase.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.PhaseView, {
            phase: phase
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
