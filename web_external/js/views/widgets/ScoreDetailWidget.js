covalic.views.ScoreDetailWidget = covalic.View.extend({
    initialize: function (settings) {
        this.submission = settings.submission;
        this.score = this.submission.get('score');

        this.metrics = _.map(this.score, function (col) {
            return col.metric;
        });

        this.averages = _.map(this.score, function (col) {
            return Math.round(col._avg * 1000) / 1000;
        });

        this.datasets = _.map(this.score[0].datasets, function (dataset) {
            return dataset.name;
        });
    },

    render: function () {
        this.$el.html(covalic.templates.scoreDetails({
            averages: this.averages,
            datasets: this.datasets,
            metrics: this.metrics,
            getScoreForCell: _.bind(this.getScoreForCell, this)
        }));
    },

    getScoreForCell: function (metric, dataset) {
        var score;
        _.every(this.score, function (m) {
            if (m.metric === metric) {
                _.every(m.datasets, function (d) {
                    if (d.name === dataset) {
                        score = d.value;
                        return false;
                    }
                    return true;
                });
                return false;
            }
            return true;
        });
        return Math.round(score * 1000) / 1000;
    }
});
