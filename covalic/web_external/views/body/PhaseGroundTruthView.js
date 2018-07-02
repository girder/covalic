import { confirm } from 'girder/dialog';
import events from 'girder/events';
import AccessWidget from 'girder/views/widgets/AccessWidget';
import UploadWidget from 'girder/views/widgets/UploadWidget';
import FolderModel from 'girder/models/FolderModel';

import router from '../../router';
import View from '../view';
import template from '../../templates/body/phaseGroundTruth.pug';
import '../../stylesheets/body/phaseGroundTruth.styl';

var PhaseGroundTruthView = View.extend({
    events: {
        'click .c-wizard-next-button': function () {
            this.accessWidget.once('g:accessListSaved', function () {
                this._saveAndGoTo('phase/' + this.model.id +
                  '/configure_submissions?wizard&curr=' + (this.wizard.current + 1) +
                  '&total=' + this.wizard.total);
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
                text: 'Are you sure you want to delete any existing ground ' +
                      'truth files for this phase? This cannot be undone.',
                yesText: 'Delete',
                confirmCallback: () => {
                    this.model.once('c:groundTruthDeleted', function () {
                        events.trigger('g:alert', {
                            text: 'Data deleted.',
                            type: 'success',
                            icon: 'ok',
                            timeout: 3000
                        });
                    }, this).cleanGroundTruthData();
                }
            });
        },

        'click .c-expose-to-group': function () {
            this.accessWidget.addEntry({
                type: 'group',
                id: this.model.get('participantGroupId')
            });
        }
    },

    initialize: function (settings) {
        this.wizard = settings.wizard || false;
        this.groundTruthFolder = new FolderModel({
            _id: this.model.get('groundTruthFolderId')
        }).once('g:fetched', function () {
            this.uploadWidget = new UploadWidget({
                parentView: this,
                modal: false,
                parentType: 'folder',
                title: false,
                parent: this.groundTruthFolder
            }).on('g:uploadFinished', this._uploadFinished, this);

            this.accessWidget = new AccessWidget({
                parentView: this,
                modal: false,
                hideRecurseOption: true,
                hideSaveButton: true,
                modelType: 'ground truth data',
                model: this.groundTruthFolder
            });

            this.render();
        }, this);
        this.groundTruthFolder.fetch();
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

        }).save();
    },

    _uploadFinished: function (info) {
        this.uploadWidget.render();
        events.trigger('g:alert', {
            text: `Added ${info.files.length} ground truth files.`,
            type: 'success',
            icon: 'ok',
            timeout: 4000
        });
    }
});

export default PhaseGroundTruthView;
