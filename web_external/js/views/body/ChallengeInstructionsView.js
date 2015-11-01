covalic.views.ChallengeInstructionsView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this._saveAndGoTo('challenge/' + this.model.id +
                '/thumbnail?wizard&curr=' + (this.wizard.current + 1) +
                '&total=' + this.wizard.total);
        },

        'click .c-save-instructions': function () {
            this._saveAndGoTo('challenge/' + this.model.id);
        }
    },

    _saveAndGoTo: function (route) {
        this.model.once('g:saved', function () {
            covalic.router.navigate(route, {trigger: true});
        }, this).set({
            instructions: this.instructionsEditor.val()
        }).save();
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;

        this.model.once('c:assetsFolderFetched', function (resp) {
            this.assetsFolder = new girder.models.FolderModel(resp);

            this.instructionsEditor = new girder.views.MarkdownWidget({
                parentView: this,
                prefix: 'challenge-instructions',
                placeholder: 'Enter challenge overview',
                enableUploads: true,
                maxUploadSize: 1024 * 1024 * 2,
                allowedExtensions: ['png', 'jpeg', 'jpg'],
                parent: this.assetsFolder
            });

            this.render();
        }, this).fetchAssetsFolder();
    },

    render: function () {
        this.$el.html(covalic.templates.challengeInstructions({
            challenge: this.model,
            wizard: this.wizard,
            markdownLink: 'https://daringfireball.net/projects/markdown/syntax'
        }));

        this.instructionsEditor.setElement(
            this.$('.c-instructions-markdown-editor')).render()
            .val(this.model.get('instructions') || '');

        return this;
    }
});

covalic.router.route('challenge/:id/instructions', 'challengeAccess', function (id, params) {
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
        girder.events.trigger('g:navigateTo', covalic.views.ChallengeInstructionsView, {
            model: challenge,
            wizard: wizard
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
