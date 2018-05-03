import View from '../view';
import SubmissionListWidget from './SubmissionListWidget';
import template from '../../templates/widgets/leaderboardWidget.pug';

var LeaderboardWidget = View.extend({
    initialize: function (settings) {
        this.phase = settings.phase;
    },

    render: function () {
        this.$el.html(template());
        new SubmissionListWidget({
            el: this.$('.c-leaderboard-container'),
            phase: this.phase,
            parentView: this
        }).render();
        return this;
    }
});

export default LeaderboardWidget;
