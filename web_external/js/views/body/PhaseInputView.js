covalic.views.PhaseInputView = covalic.View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                covalic.router.navigate('phase/' + this.model.id, {trigger: true});
            }, this).saveAccessList();
        },

        'click .c-save-access': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                girder.events.trigger('g:alert', {
                    text: 'Settings saved.',
                    type: 'success',
                    icon: 'ok',
                    timeout: 3000
                });
            }, this).saveAccessList();
        },

        'click .c-clear-contents': function () {
            girder.confirm({
                text: 'Are you sure you want to delete any existing input ' +
                      'files for this phase? This cannot be undone.',
                yesText: 'Delete',
                confirmCallback: _.bind(function () {
                    this.model.once('c:inputDataDeleted', function () {
                        girder.events.trigger('g:alert', {
                            text: 'Data deleted.',
                            type: 'success',
                            icon: 'ok',
                            timeout: 3000
                        });
                    }, this).cleanInputData();
                }, this)
            });
        }
    },

    _saveAndGoTo: function (route) {
        this.model.once('g:saved', function () {
            covalic.router.navigate(route, {trigger: true});
        }, this).set({

        }).saveAccessList();
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        this.inputFolder = new girder.models.FolderModel({
            _id: this.model.get('testDataFolderId')
        }).once('g:fetched', function () {
            this.uploadWidget = new girder.views.UploadWidget({
                parentView: this,
                modal: false,
                parentType: 'folder',
                title: false,
                parent: this.inputFolder
            }).on('g:uploadFinished', this._uploadFinished, this);

            this.accessWidget = new girder.views.AccessWidget({
                parentView: this,
                modal: false,
                hideRecurseOption: true,
                hideSaveButton: true,
                modelType: 'input data',
                model: this.inputFolder
            });

            this.render();
        }, this).fetch();
    },

    render: function () {
        this.$el.html(covalic.templates.phaseInputData({
            wizard: this.wizard,
            phase: this.model
        }));

        this.uploadWidget.setElement(this.$('.c-upload-container')).render();
        this.accessWidget.setElement(this.$('.c-access-container')).render();

        return this;
    },

    _uploadFinished: function (info) {
        this.uploadWidget.render();
        girder.events.trigger('g:alert', {
            text: 'Added ' + info.files.length + ' ground truth files.',
            type: 'success',
            icon: 'ok',
            timeout: 4000
        });
    }
});

covalic.router.route('phase/:id/input', 'phaseInput', function (id, params) {
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
        girder.events.trigger('g:navigateTo', covalic.views.PhaseInputView, {
            model: phase,
            wizard: wizard
        });
    }, this).on('g:error', function () {
        covalic.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
