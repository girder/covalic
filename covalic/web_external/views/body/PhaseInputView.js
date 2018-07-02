import { confirm } from 'girder/dialog';
import events from 'girder/events';
import AccessWidget from 'girder/views/widgets/AccessWidget';
import UploadWidget from 'girder/views/widgets/UploadWidget';
import FolderModel from 'girder/models/FolderModel';

import router from '../../router';
import View from '../view';
import template from '../../templates/body/phaseInputData.pug';
import '../../stylesheets/body/phaseGroundTruth.styl';

var PhaseInputView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                router.navigate('phase/' + this.model.id +
                    '/groundtruth?wizard&curr=' + (this.wizard.current + 1) + '&total=' +
                    this.wizard.total, {trigger: true});
            }, this).saveAccessList();
        },

        'click .c-save-access': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                events.trigger('g:alert', {
                    text: 'Settings saved.',
                    type: 'success',
                    icon: 'ok',
                    timeout: 3000
                });
            }, this).saveAccessList();
        },

        'click .c-clear-contents': function () {
            confirm({
                text: 'Are you sure you want to delete any existing input ' +
                      'files for this phase? This cannot be undone.',
                yesText: 'Delete',
                confirmCallback: () => {
                    this.model.once('c:inputDataDeleted', function () {
                        events.trigger('g:alert', {
                            text: 'Data deleted.',
                            type: 'success',
                            icon: 'ok',
                            timeout: 3000
                        });
                    }, this).cleanInputData();
                }
            });
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        this.inputFolder = new FolderModel({
            _id: this.model.get('testDataFolderId')
        }).once('g:fetched', function () {
            this.uploadWidget = new UploadWidget({
                parentView: this,
                modal: false,
                parentType: 'folder',
                title: false,
                parent: this.inputFolder
            }).on('g:uploadFinished', this._uploadFinished, this);

            this.accessWidget = new AccessWidget({
                parentView: this,
                modal: false,
                hideRecurseOption: true,
                hideSaveButton: true,
                modelType: 'input data',
                model: this.inputFolder
            });

            this.render();
        }, this);
        this.inputFolder.fetch();
    },

    render: function () {
        this.$el.html(template({
            wizard: this.wizard,
            phase: this.model
        }));

        this.uploadWidget.setElement(this.$('.c-upload-container')).render();
        this.accessWidget.setElement(this.$('.c-access-container')).render();

        return this;
    },

    _saveAndGoTo: function (route) {
        this.model.once('g:saved', function () {
            router.navigate(route, {trigger: true});
        }, this).set({

        }).saveAccessList();
    },

    _uploadFinished: function (info) {
        this.uploadWidget.render();
        events.trigger('g:alert', {
            text: `Added ${info.files.length} input files.`,
            type: 'success',
            icon: 'ok',
            timeout: 4000
        });
    }
});

export default PhaseInputView;
