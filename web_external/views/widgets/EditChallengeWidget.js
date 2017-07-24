import $ from 'jquery';
import { handleClose, handleOpen } from 'girder/dialog';
import DateTimeRangeWidget from 'girder/views/widgets/DateTimeRangeWidget';
import 'girder/utilities/jquery/girderModal';

import View from '../view';
import ChallengeModel from '../../models/ChallengeModel';
import template from '../../templates/widgets/editChallenge.pug';

var EditChallengeWidget = View.extend({
    events: {
        'submit #c-challenge-edit-form': function (e) {
            e.preventDefault();

            var fields = {
                name: this.$('#c-challenge-name').val(),
                description: this.$('#c-challenge-description').val(),
                organizers: this.$('#c-challenge-organizers').val(),
                startDate: this.dateTimeRangeWidget.fromDateString(),
                endDate: this.dateTimeRangeWidget.toDateString()
            };

            if (this.model) {
                this.updateChallenge(fields);
            } else {
                this.createChallenge(fields);
            }

            this.$('button.c-save-challenge').addClass('disabled');
            this.$('.g-validation-failed-message').text('');
        }
    },

    initialize: function (settings) {
        this.model = settings.model || null;

        this.dateTimeRangeWidget = new DateTimeRangeWidget({
            parentView: this
        });
    },

    render: function () {
        var modal = this.$el.html(template({
            challenge: this.model
        })).girderModal(this).on('shown.bs.modal', () => {
            this.$('#c-challenge-name').focus();
        }).on('hidden.bs.modal', () => {
            if (this.create) {
                handleClose('create');
            } else {
                handleClose('edit');
            }
        }).on('ready.girder.modal', () => {
            if (this.model) {
                this.$('#c-challenge-name').val(this.model.get('name'));
                this.$('#c-challenge-description').val(this.model.get('description'));
                this.$('#c-challenge-organizers').val(this.model.get('organizers'));

                this.dateTimeRangeWidget.setElement(this.$('#c-challenge-timeframe')).render();
                this.dateTimeRangeWidget.setFromDate(this.model.get('startDate'));
                this.dateTimeRangeWidget.setToDate(this.model.get('endDate'));

                this.create = false;
            } else {
                this.create = true;
            }
        });
        modal.trigger($.Event('ready.girder.modal', {relatedTarget: modal}));
        this.$('#c-challenge-name').focus();

        if (this.model) {
            handleOpen('edit');
        } else {
            handleOpen('create');
        }

        return this;
    },

    createChallenge: function (fields) {
        var challenge = ChallengeModel();
        challenge.set(fields);
        challenge.on('g:saved', function () {
            this.$el.on('hidden.bs.modal', () => {
                this.trigger('g:saved', challenge);
            }).modal('hide');
        }, this).off('g:error').on('g:error', function (err) {
            this.$('.g-validation-failed-message').text(err.responseJSON.message);
            this.$('button.c-save-challenge').removeClass('disabled');
            this.$('#c-challenge-' + err.responseJSON.field).focus();
        }, this).save();
    },

    updateChallenge: function (fields) {
        this.model.set(fields);
        this.model.on('g:saved', function () {
            this.$el.on('hidden.bs.modal', () => {
                this.trigger('g:saved', this.model);
            }).modal('hide');
        }, this).off('g:error').on('g:error', function (err) {
            this.$('.g-validation-failed-message').text(err.responseJSON.message);
            this.$('button.c-save-challenge').removeClass('disabled');
            this.$('#c-challenge-' + err.responseJSON.field).focus();
        }, this).save();
    }
});

export default EditChallengeWidget;
