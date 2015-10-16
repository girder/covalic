covalic.views.NewChallenge = covalic.View.extend({
    events: {
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.newChallengePage({
            wizard: this.wizard
        }));
        return this;
    }
});

covalic.router.route('challenge/new', 'newChallenge', function () {
    girder.events.trigger('g:navigateTo', covalic.views.NewChallenge, {
        wizard: {
            total: 4
        }
    });
});
