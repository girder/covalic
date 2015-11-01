covalic.views.PhaseInstructionsView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this._saveAndGoTo('phase/' + this.model.id +
                '/groundtruth?wizard&curr=' + (this.wizard.current + 1) +
                '&total=' + this.wizard.total);
        },

        'click .c-save-instructions': function () {
            this._saveAndGoTo('phase/' + this.model.id);
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

        this.phaseFolder = new girder.models.FolderModel({
            _id: this.model.get('folderId')
        });

        this.instructionsEditor = new girder.views.MarkdownWidget({
            parentView: this,
            prefix: 'phase-instructions',
            placeholder: 'Enter phase overview',
            enableUploads: true,
            maxUploadSize: 1024*1024*2,
            allowedExtensions: ['png', 'jpeg', 'jpg'],
            parent: this.phaseFolder,
        });

        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.phaseInstructions({
            wizard: this.wizard,
            markdownLink: 'https://daringfireball.net/projects/markdown/syntax'
        }));

        this.instructionsEditor.setElement(
            this.$('.c-instructions-markdown-editor')).render()
            .val(this.model.get('instructions') || '');

        return this;
    }
});

covalic.router.route('phase/:id/instructions', 'phaseInstructions', function (id, params) {
    var phase = new covalic.models.PhaseModel({_id: id}),
        wizard = false;

    params = girder.parseQueryString(params);

    if (_.has(params, 'wizard')) {
        wizard = {
            total: window.parseInt(params.total),
            current: window.parseInt(params.curr)
        };
    }

    phase.once('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.PhaseInstructionsView, {
            model: phase,
            wizard: wizard
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
