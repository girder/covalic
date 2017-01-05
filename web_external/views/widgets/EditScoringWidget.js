import View from '../view';
import template from '../../templates/widgets/editScoringWidget.pug';
import 'girder/utilities/jquery/girderModal';

var EditScoringWidget = View.extend({
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
        var modal = this.$el.html(template({
            phase: this.model
        })).girderModal(this).on('ready.girder.modal', () => {
            var scoreTask = this.model.get('scoreTask');
            if (scoreTask) {
                this.$('#c-scoring-docker-image').val(scoreTask.dockerImage);
                if (scoreTask.dockerArgs) {
                    this.$('#c-scoring-docker-args').val(JSON.stringify(scoreTask.dockerArgs));
                }
            }
        });
        modal.trigger($.Event('ready.girder.modal', {relatedTarget: modal}));

        return this;
    }
});

export default EditScoringWidget;
