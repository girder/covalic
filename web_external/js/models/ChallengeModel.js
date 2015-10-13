covalic.models.ChallengeModel = girder.AccessControlledModel.extend({
    resourceName: 'challenge',

    getThumbnailUrl: function (size) {
        size = size || 200;

        return girder.apiRoot + '/challenge/' + this.id +
            '/thumbnail/download?size=' + size;
    }
});
