import _ from 'underscore';
import { renderMarkdown } from 'girder/misc';

import View from '../view';
import template from '../../templates/widgets/scoreDetails.pug';
import metricInfoTemplate from '../../templates/widgets/metricInfo.pug';

var ScoreDetailWidget = View.extend({
    initialize: function (settings) {
        this.submission = settings.submission;
        this.phase = settings.phase;
        this.score = this.submission.get('score');

        var metricsInfo = this.phase.get('metrics') || {};
        this.metrics = _.map(this.score[0].metrics, function (metric) {
            var metricInfo = metricsInfo[metric.name] || {};
            var title = metricInfo.title;
            var result = {
                name: metric.name
            };
            if (title) {
                result.title = title;
            }
            return result;
        });
        this.datasets = _.pluck(this.score, 'dataset');
    },

    render: function () {
        this.$el.html(template({
            datasets: this.datasets,
            metrics: this.metrics,
            getScoreForCell: _.bind(this.getScoreForCell, this)
        }));

        var scoreTable = this.$('.c-submission-score-table');

        var metricsInfo = this.phase.get('metrics') || {};
        _.each(this.$('.c-metric-heading'), function (heading) {
            var el = $(heading),
                metricId = el.attr('metric'),
                metricInfo = metricsInfo[metricId] || {},
                title = metricInfo.title || metricId,
                description = metricInfo.description
                    ? renderMarkdown(metricInfo.description)
                    : null,
                weight = metricInfo.weight || 0;

            el.popover({
                title,
                container: this.$el,
                viewport: scoreTable,
                trigger: 'focus',
                placement: 'auto',
                content: metricInfoTemplate({
                    description,
                    weight
                }),
                html: true
            });
        }, this);
        return this;
    },

    getScoreForCell: function (dataset, metric) {
        var score = null;

        _.every(this.score, function (d) {
            if (d.dataset === dataset) {
                _.every(d.metrics, function (m) {
                    if (m.name === metric) {
                        score = m.value;
                        return false;
                    }
                    return true;
                });
                return false;
            }
            return true;
        });

        if (score === null) {
            return '';
        }
        if (_.contains(['inf', '-inf', 'nan'], score)) {
            return score;
        }
        if (score < 0.0001) {
            return Number(score).toExponential(2);
        } else {
            return Number(score).toFixed(3);
        }
    }
});

export default ScoreDetailWidget;
