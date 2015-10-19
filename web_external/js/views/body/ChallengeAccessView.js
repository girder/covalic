covalic.views.ChallengeAccessView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                covalic.router.navigate('challenge/' + this.model.id +
                    '/thumbnail?wizard&curr=' + (this.wizard.current + 1) + '&total=' +
                    this.wizard.total, {trigger: true});
            }, this).saveAccessList();
        },

        'click .c-save-access-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                girder.events.trigger('g:alert', {
                    text: 'Settings saved.',
                    type: 'success',
                    icon: 'ok',
                    timeout: 3000
                });
            }, this).saveAccessList();
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.accessWidget = new girder.views.AccessWidget({
            parentView: this,
            modelType: 'challenge',
            modal: false,
            model: this.model,
            hideRecurseOption: true,
            hideSaveButton: true
        });

        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.challengeAccessPage({
            wizard: this.wizard
        }));

        this.accessWidget.setElement(this.$('.c-access-list-container')).render();


        return this;
    }
});

covalic.router.route('challenge/:id/access', 'challengeAccess', function (id, params) {
    var challenge = new covalic.models.ChallengeModel({_id: id}),
        wizard = false;

    params = girder.parseQueryString(params);

    if (_.has(params, 'wizard')) {
        wizard = {
            total: window.parseInt(params.total),
            current: window.parseInt(params.curr)
        };
    }

    challenge.once('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.ChallengeAccessView, {
            model: challenge,
            wizard: wizard
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
