covalic.views.ScoreDetailWidget = covalic.View.extend({
    initialize: function (settings) {
        this.submission = settings.submission;
        this.score = this.submission.get('score');

        this.metrics = _.map(this.score[0].metrics, function (metric) {
            return metric.name;
        });

        this.datasets = _.map(this.score, function (dataset) {
            return dataset.dataset;
        });
    },

    render: function () {
        this.$el.html(covalic.templates.scoreDetails({
            datasets: this.datasets,
            metrics: this.metrics,
            getScoreForCell: _.bind(this.getScoreForCell, this)
        }));
    },

    getScoreForCell: function (dataset, metric) {
        var score;
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

        if (score < 0.0001) {
            return Number(score).toExponential(2);
        } else {
            return Number(score).toPrecision(4);
        }
    }
});
