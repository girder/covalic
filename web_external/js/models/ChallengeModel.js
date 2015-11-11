covalic.models.ChallengeModel = girder.AccessControlledModel.extend({
    resourceName: 'challenge',
    DEFAULT_THUMB_SIZE: 200,

    getThumbnailUrl: function (opts) {
        opts = opts || {};
        opts.size = opts.size || this.DEFAULT_THUMB_SIZE;

        return girder.apiRoot + '/challenge/' + this.id +
            '/thumbnail/download?size=' + opts.size + '&ts=' +
            new Date().getTime();
    },

    fetchAssetsFolder: function () {
        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/assets_folder',
            type: 'GET'
        }).done(_.bind(function (resp) {
            this.trigger('c:assetsFolderFetched', resp);
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    },

    createThumbnail: function (fileId, size) {
        size = size || this.DEFAULT_THUMB_SIZE;

        girder.restRequest({
            path: this.resourceName + '/' + this.id + '/thumbnail',
            type: 'POST',
            data: {
                fileId: fileId,
                size: size
            },
            error: null
        }).done(_.bind(function () {
            this.trigger('c:thumbnailCreated');
        }, this)).error(_.bind(function (err) {
            this.trigger('c:error', err);
        }, this));
    }
});
