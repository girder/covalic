import _ from 'underscore';
import { cancelRestRequests } from 'girder/rest';
import UserCollection from 'girder/collections/UserCollection';
import PaginateWidget from 'girder/views/widgets/PaginateWidget';

import View from '../view';
import UserSubmissionsView from './UserSubmissionsView';
import template from '../../templates/body/phaseSubmissionsPage.pug';
import '../../stylesheets/body/phaseSubmissionsPage.styl';

var PhaseSubmissionsView = View.extend({
    initialize: function (settings) {
        cancelRestRequests('fetch');

        var participantLimit = 5;
        if (!_.isNull(settings.participantLimit)) {
            participantLimit = Math.max(1, parseInt(settings.participantLimit, 10));
        }

        this.views = [];

        if (settings.phase) {
            this.phase = settings.phase;

            this.participants = new UserCollection();
            this.participants.altUrl = `group/${this.phase.get('participantGroupId')}/member`;
            this.participants.pageLimit = participantLimit;
            this.participants.on('g:changed', function () {
                this.views = [];
                this.participants.each((user) => {
                    this.views.push(new UserSubmissionsView({
                        phase: this.phase,
                        user,
                        submissionLimit: settings.submissionLimit,
                        parentView: this
                    }));
                });
                this.render();
            }, this).fetch();

            this.paginateWidget = new PaginateWidget({
                collection: this.participants,
                parentView: this
            });
        }
    },

    render: function () {
        this.$el.html(template({
            phase: this.phase
        }));

        var container = $('.c-user-submissions-container');

        _.each(this.views, function (view) {
            container.append(view.render().el);
        });

        this.paginateWidget.setElement(this.$('.c-phase-participants-pagination')).render();

        return this;
    }
});

export default PhaseSubmissionsView;
