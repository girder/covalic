/**
 * Page where users upload a submission.
 */
covalic.views.SubmitView = covalic.View.extend({
    initialize: function (settings) {
        this.phase = settings.phase;
        this.render();
    },

    render: function () {
        this.$el.html(covalic.templates.submitPage({
            phase: this.phase
        }));

        this.uploadWidget = new girder.views.UploadWidget({
            el: this.$('.c-submit-uploader-container'),
            modal: false,
            noParent: true,
            title: null,
            overrideStart: true
        }).render();

        this.listenTo(this.uploadWidget, 'g:filesChanged', this.filesSelected);
        this.listenTo(this.uploadWidget, 'g:uploadStarted', this.uploadStarted);
        this.listenTo(this.uploadWidget, 'g:uploadFinished', this.uploadFinished);
    },


    filesSelected: function (files) {
       // TODO validate the files
    },

    /**
     * When "start upload" is clicked, we want to make a folder in the user's
     * personal space for the submission contents, so we do that and then proceed
     * uploading into it.
     */
    uploadStarted: function () {
        this.folder = new girder.models.FolderModel({
            name: 'submission_' + this.phase.get('_id') + '_' + Date.now(),
            parentType: 'user',
            parentId: girder.currentUser.get('_id'),
            description: 'Challenge submission'
        });

        this.folder.on('g:saved', function () {
            this.uploadWidget.parentType = 'folder';
            this.uploadWidget.parent = this.folder;
            this.uploadWidget.uploadNextFile();
        }, this).on('g:error', function (err) {
            girder.events.trigger('g:alert', {
                icon: 'cancel',
                text: 'Could not create submission folder.',
                type: 'error',
                timeout: 4000
            });
        }, this).save();
    },

    uploadFinished: function () {
        this.phase.off('c:submissionPosted').on('c:submissionPosted', function (submission) {
            console.log(submission);
        }, this).postSubmission(this.folder.get('_id'))
    }
});

covalic.router.route('phase/:id/submit', 'phase_submit', function (id, params) {
    var phase = new covalic.models.PhaseModel();
    phase.set({
        _id: id
    }).on('g:fetched', function () {
        girder.events.trigger('g:navigateTo', covalic.views.SubmitView, {
            phase: phase
        });
    }, this).on('g:error', function () {
        girder.router.navigate('challenges', {trigger: true});
    }, this).fetch();
});
