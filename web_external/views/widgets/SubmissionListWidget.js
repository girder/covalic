import _ from 'underscore';
import moment from 'moment';
import { AccessType, SORT_DESC } from 'girder/constants';
import LoadingAnimation from 'girder/views/widgets/LoadingAnimation';
import PaginateWidget from 'girder/views/widgets/PaginateWidget';

import View from '../view';
import SubmissionCollection from '../../collections/SubmissionCollection';
import template from '../../templates/widgets/leaderboard.pug';
import '../../stylesheets/widgets/leaderboard.styl';

var SubmissionListWidget = View.extend({
    initialize: function (settings) {
        this.phase = settings.phase;

        new LoadingAnimation({
            el: this.$el,
            parentView: this
        }).render();

        this.collection = new SubmissionCollection();
        this.collection.on('g:changed', function () {
            this.collection.each(function (submission) {
                var score = submission.get('overallScore');
                if (_.contains(['inf', '-inf', 'nan'], score)) {
                    submission.displayScore = score;
                } else {
                    submission.displayScore = (Math.round(score * 1000) / 1000).toFixed(3);
                }
            });
            this.render();
        }, this).fetch({
            phaseId: this.phase.get('_id'),
            sort: 'overallScore',
            sortdir: SORT_DESC
        });
    },

    render: function () {
        this.$el.html(template({
            submissions: this.collection.toArray(),
            start: this.collection.offset - this.collection.length,
            phase: this.phase,
            AccessType,
            moment
        }));

        new PaginateWidget({
            el: this.$('.c-leaderboard-pagination'),
            collection: this.collection,
            parentView: this
        }).render();
        return this;
    }
});

export default SubmissionListWidget;
