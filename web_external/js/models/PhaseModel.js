covalic.models.PhaseModel = girder.AccessControlledModel.extend({
    resourceName: 'challenge_phase',

    fetchGroundtruthItems: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.get('_id') + '/groundtruth/item',
            type: 'GET'
        }).done(_.bind(function (resp) {
            this.set('groundtruthItems', resp);
            this.trigger('c:groundtruthItemsFetched', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    },

    fetchTestDataItems: function (params) {
        var items = new girder.collections.ItemCollection();
        items.altUrl = this.resourceName + '/' + this.get('_id') + '/test_data/item';
        items.once('g:changed', function () {
            this.trigger('c:testDataItemsFetched', items);
        }, this).fetch(params);

        return items;
    },

    saveMetrics: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.get('_id') + '/metrics',
            type: 'PUT',
            data: JSON.stringify(this.get('metrics') || {}),
            processData: false,
            contentType: 'application/json'
        }).done(_.bind(function (resp) {
            this.trigger('c:metricsSaved', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    },

    saveScoringInfo: function (args) {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/scoring_info',
            type: 'PUT',
            data: args,
            error: null
        }).done(_.bind(function (resp) {
            this.set(resp);
            this.trigger('c:scoringInfoSaved', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    },

    initMetrics: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.get('_id') + '/metrics/init',
            type: 'POST'
        }).done(_.bind(function (resp) {
            this.trigger('c:metricsInitialized', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    },

    cleanGroundTruthData: function () {
        girder.restRequest({
            path: 'folder/' + this.get('groundTruthFolderId') + '/contents',
            progress: true,
            type: 'DELETE'
        }).done(_.bind(function (resp) {
            this.trigger('c:groundTruthDeleted', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    },

    cleanInputData: function () {
        girder.restRequest({
            path: 'folder/' + this.get('testDataFolderId') + '/contents',
            progress: true,
            type: 'DELETE'
        }).done(_.bind(function (resp) {
            this.trigger('c:inputDataDeleted', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    }
});
