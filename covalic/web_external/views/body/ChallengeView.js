import { AccessType } from 'girder/constants';
import { confirm } from 'girder/dialog';
import events from 'girder/events';
import { renderMarkdown } from 'girder/misc';
import { cancelRestRequests } from 'girder/rest';

import router from '../../router';
import View from '../view';
import ChallengeModel from '../../models/ChallengeModel';
import ChallengePhasesWidget from '../widgets/ChallengePhasesWidget';
import ChallengeTimelineWidget from '../widgets/ChallengeTimelineWidget';
import EditChallengeWidget from '../widgets/EditChallengeWidget';
import template from '../../templates/body/challengePage.pug';
import '../../stylesheets/body/challengePage.styl';

var ChallengeView = View.extend({
    events: {
        'click a.c-edit-challenge': function () {
            if (!this.editChallengeWidget) {
                this.editChallengeWidget = new EditChallengeWidget({
                    el: $('#g-dialog-container'),
                    model: this.model,
                    parentView: this
                }).on('g:saved', function () {
                    this.render();
                }, this);
            }
            this.editChallengeWidget.render();
        },

        'click .c-delete-challenge': function () {
            confirm({
                text: 'Are you sure you want to delete the challenge <b>' +
                      this.model.escape('name') + '</b>?',
                yesText: 'Delete',
                escapedHtml: true,
                confirmCallback: () => {
                    this.model.once('g:deleted', function () {
                        events.trigger('g:alert', {
                            icon: 'ok',
                            text: 'Challenge deleted.',
                            type: 'success',
                            timeout: 4000
                        });
                        router.navigate('challenges', {trigger: true});
                    }).destroy({
                        progress: true
                    });
                }
            });
        }
    },

    initialize: function (settings) {
        cancelRestRequests('fetch');
        if (settings.challenge) {
            this.model = settings.challenge;
            this._initWidgets();
            this.render();
        } else if (settings.id) {
            this.model = new ChallengeModel({
                _id: settings.id
            });

            this.model.on('g:fetched', function () {
                this._initWidgets();
                this.render();
            }, this).fetch();
        }
    },

    _initWidgets: function () {
        this.timelineView = new ChallengeTimelineWidget({
            challenge: this.model,
            parentView: this
        });

        this.phasesView = new ChallengePhasesWidget({
            challenge: this.model,
            parentView: this
        });
    },

    render: function () {
        this.$el.html(template({
            challenge: this.model,
            humanLink: '#challenge/n/' + encodeURIComponent(this.model.transformNameForUrl()),
            AccessType
        }));

        this.timelineView.setElement(this.$('.c-challenge-timeline-container')).render();

        renderMarkdown(this.model.get('instructions') || '*No overview provided.*',
            this.$('.c-challenge-instructions-container'));

        this.phasesView.setElement(this.$('.c-challenge-phase-container')).render();

        return this;
    }
});

export default ChallengeView;
