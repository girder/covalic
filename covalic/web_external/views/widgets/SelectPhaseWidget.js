import View from '../view';
import PhaseModel from '../../models/PhaseModel';
import template from '../../templates/widgets/selectPhase.pug';
import 'girder/utilities/jquery/girderModal';

var SelectPhaseWidget = View.extend({
    events: {
        'submit #c-phase-select-form': function (e) {
            e.preventDefault();

            this.$('.g-validation-failed-message').empty();

            var id = this.$('#c-phase-id').val(),
                phase = new PhaseModel({_id: id});

            phase.on('g:fetched', function () {
                this.$el.modal('hide');
                this.trigger('c:phaseSelected', phase);
            }, this).on('g:error', function (resp) {
                this.$('.g-validation-failed-message').text(resp.responseJSON.message);
            }, this).fetch();
        }
    },

    initialize: function (settings) {
        this.phase = settings.phase || null;
        this.title = settings.title || 'Select phase';
    },

    render: function () {
        var modal = this.$el.html(template({
            title: this.title
        })).girderModal(this).on('shown.bs.modal', () => {
            this.$('#c-phase-id').focus();
        });

        modal.trigger($.Event('ready.girder.modal', {relatedTarget: modal}));
        this.$('#c-phase-id').focus();

        return this;
    }
});

export default SelectPhaseWidget;
