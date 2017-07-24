import FolderModel from 'girder/models/FolderModel';
import LoadingAnimation from 'girder/views/widgets/LoadingAnimation';
import UploadWidget from 'girder/views/widgets/UploadWidget';

import View from '../view';
import template from '../../templates/widgets/editThumbnail.pug';
import '../../stylesheets/widgets/editThumbnail.styl';

var EditThumbnailWidget = View.extend({
    initialize: function () {
        this.render();

        this.uploadWidget = new UploadWidget({
            parentView: this,
            modal: false,
            title: false,
            noParent: true
        }).on('g:filesChanged', function (files) {
            this.uploadWidget.$('.g-validation-failed-message').empty();

            if (files.length === 1) {
                this.uploadWidget.startUpload();
                this.uploadWidget.$('.g-progress-overall').hide();
            } else {
                this.uploadWidget.$('.g-validation-failed-message').text(
                    'Please select only one file.');
            }
        }, this).on('g:uploadFinished', function () {
            new LoadingAnimation({
                parentView: this,
                el: this.$('.c-current-thumbnail')
            }).render();

            this.model.once('c:thumbnailCreated', function () {
                this.$('.c-current-thumbnail').empty().append(
                    $('<img />', {
                        src: this.model.getThumbnailUrl()
                    }));
                this._renderUploadWidget();
            }, this).once('c:error', function (err) {
                this.uploadWidget.$('.g-validation-failed-message').text(
                    err.responseJSON.message);
                this.uploadWidget.$('.g-drop-zone').removeClass('hide');
            }, this).createThumbnail(this.uploadWidget.currentFile.id);
        }, this);

        this.model.once('c:assetsFolderFetched', function (resp) {
            this.assetsFolder = new FolderModel(resp);
            this.uploadWidget.parent = this.assetsFolder;
            this.ready = true;
            this.render();
        }, this).fetchAssetsFolder();
    },

    render: function () {
        if (!this.ready) {
            new LoadingAnimation({
                el: this.$el,
                parentView: this
            }).render();
            return this;
        }

        this.$el.html(template({
            challenge: this.model
        }));
        this._renderUploadWidget();

        return this;
    },

    _renderUploadWidget: function () {
        this.uploadWidget.setElement(this.$('.c-thumbnail-upload-widget')).render();
        this.uploadWidget.$('.g-start-upload,.g-overall-progress-message').hide();
        this.uploadWidget.$('.g-drop-zone').text('Browse or drop a file...');
    }
});

export default EditThumbnailWidget;
