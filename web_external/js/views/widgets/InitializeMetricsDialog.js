covalic.views.InitializeMetricsDialog = covalic.View.extend({
    events: {
        'change .c-confirm-checkbox': function (e) {
            if ($(e.currentTarget).is(':checked')) {
                this.$('.c-begin-metric-initialization').removeClass('disabled');
            } else {
                this.$('.c-begin-metric-initialization').addClass('disabled');
            }
        },

        'click .c-begin-metric-initialization': function () {
            this.model.once('g:metricsInitialized', function () {

            }, this).initMetrics()
        }
    },

    render: function () {
        this.$el.html(covalic.templates.initializeMetricsDialog()).girderModal(this);
    }
});
