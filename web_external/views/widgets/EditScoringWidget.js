/**
 * This widget is used to customize scoring behavior for a phase.
 */
covalic.views.EditScoringWidget = covalic.View.extend({
    events: {
        'submit #c-phase-edit-score-form': function (e) {
            e.preventDefault();

            this.model.once('c:scoringInfoSaved', function () {
                this.$el.modal('hide');
            }, this).off('c:error').on('c:error', function (err) {
                this.$('.g-validation-failed-message').text(err.responseJSON.message);
                this.$('button.c-save-scoring-info').removeClass('disabled');
            }, this).saveScoringInfo({
                dockerImage: this.$('#c-scoring-docker-image').val().trim(),
                dockerArgs: this.$('#c-scoring-docker-args').val().trim()
            });

            this.$('button.c-save-scoring-info').addClass('disabled');
            this.$('.g-validation-failed-message').text('');
        }
    },

    render: function () {
        var modal = this.$el.html(covalic.templates.editScoringWidget({
            phase: this.model
        })).girderModal(this).on('ready.girder.modal', _.bind(function () {
            var scoreTask = this.model.get('scoreTask');
            if (scoreTask) {
                this.$('#c-scoring-docker-image').val(scoreTask.dockerImage);
                if (scoreTask.dockerArgs) {
                    this.$('#c-scoring-docker-args').val(JSON.stringify(scoreTask.dockerArgs));
                }
            }
        }, this));
        modal.trigger($.Event('ready.girder.modal', {relatedTarget: modal}));

        return this;
    }
});
