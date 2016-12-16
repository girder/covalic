covalic.views.ChallengeThumbnailView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            covalic.router.navigate('challenge/' + this.model.id, {trigger: true});
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        if (this.wizard && !_.has(this.wizard, 'current')) {
            this.wizard.current = 0;
        }

        this.editThumbnailWidget = new covalic.views.EditThumbnailWidget({
            parentView: this,
            model: this.model
        });

        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.challengeThumbnailPage({
            challenge: this.model,
            wizard: this.wizard
        }));

        this.editThumbnailWidget.setElement(this.$('.c-thumbnail-widget-container')).render();

        return this;
    }
});

covalic.router.route('challenge/:id/thumbnail', 'challengeThumbnail', function (id, params) {
    var challenge = new covalic.models.ChallengeModel({_id: id}),
        wizard = false;

    params = girder.parseQueryString(params);

    if (_.has(params, 'wizard')) {
        wizard = {
            total: window.parseInt(params.total),
            current: window.parseInt(params.curr)
        };
    }

    challenge.on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.ChallengeThumbnailView, {
            model: challenge,
            wizard: wizard
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
