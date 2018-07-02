import ItemCollection from 'girder/collections/ItemCollection';
import AccessControlledModel from 'girder/models/AccessControlledModel';
import { restRequest } from 'girder/rest';

var PhaseModel = AccessControlledModel.extend({
    resourceName: 'challenge_phase',

    fetchGroundtruthItems: function () {
        restRequest({
            path: `${this.resourceName}/${this.id}/groundtruth/item`,
            type: 'GET'
        }).done((resp) => {
            this.set('groundtruthItems', resp);
            this.trigger('c:groundtruthItemsFetched', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    fetchTestDataItems: function (params) {
        var items = new ItemCollection();
        items.altUrl = `${this.resourceName}/${this.id}/test_data/item`;
        items.once('g:changed', function () {
            this.trigger('c:testDataItemsFetched', items);
        }, this).fetch(params);

        return items;
    },

    saveMetrics: function () {
        restRequest({
            path: `${this.resourceName}/${this.id}/metrics`,
            type: 'PUT',
            data: JSON.stringify(this.get('metrics') || {}),
            processData: false,
            contentType: 'application/json'
        }).done((resp) => {
            this.trigger('c:metricsSaved', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    saveScoringInfo: function (args) {
        restRequest({
            path: `${this.resourceName}/${this.id}/scoring_info`,
            type: 'PUT',
            data: args,
            error: null
        }).done((resp) => {
            this.set(resp);
            this.trigger('c:scoringInfoSaved', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    initMetrics: function () {
        restRequest({
            path: `${this.resourceName}/{this.id}/metrics/init`,
            type: 'POST'
        }).done((resp) => {
            this.trigger('c:metricsInitialized', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    cleanGroundTruthData: function () {
        restRequest({
            path: `folder/${this.get('groundTruthFolderId')}/contents`,
            progress: true,
            type: 'DELETE'
        }).done((resp) => {
            this.trigger('c:groundTruthDeleted', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    cleanInputData: function () {
        restRequest({
            path: `folder/${this.get('testDataFolderId')}/contents`,
            progress: true,
            type: 'DELETE'
        }).done((resp) => {
            this.trigger('c:inputDataDeleted', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    enableOrganization: function () {
        return this.get('enableOrganization');
    },

    requireOrganization: function () {
        return !this.has('requireOrganization') || this.get('requireOrganization');
    },

    enableOrganizationUrl: function () {
        return this.get('enableOrganizationUrl');
    },

    requireOrganizationUrl: function () {
        return !this.has('requireOrganizationUrl') || this.get('requireOrganizationUrl');
    },

    enableDocumentationUrl: function () {
        return this.get('enableDocumentationUrl');
    },

    requireDocumentationUrl: function () {
        return !this.has('requireDocumentationUrl') || this.get('requireDocumentationUrl');
    }
});

export default PhaseModel;
