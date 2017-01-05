import AccessControlledModel from 'girder/models/AccessControlledModel';
import { apiRoot, restRequest } from 'girder/rest';

var ChallengeModel = AccessControlledModel.extend({
    resourceName: 'challenge',
    DEFAULT_THUMB_SIZE: 200,

    getThumbnailUrl: function (opts) {
        opts = opts || {};
        opts.size = opts.size || this.DEFAULT_THUMB_SIZE;
        var ts = new Date().getTime();
        return `${apiRoot}/challenge/${this.id}/thumbnail/download?size=${opts.size}&ts=${ts}`;
    },

    fetchAssetsFolder: function () {
        restRequest({
            path: `${this.resourceName}/${this.id}/assets_folder`,
            type: 'GET'
        }).done((resp) => {
            this.trigger('c:assetsFolderFetched', resp);
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    createThumbnail: function (fileId, size) {
        size = size || this.DEFAULT_THUMB_SIZE;

        restRequest({
            path: `${this.resourceName}/${this.id}/thumbnail`,
            type: 'POST',
            data: {
                fileId: fileId,
                size: size
            },
            error: null
        }).done(() => {
            this.trigger('c:thumbnailCreated');
        }).error((err) => {
            this.trigger('c:error', err);
        });
    },

    /**
     * Transforms a challenge name back and forth between a form suitable for
     * a permalink URL.
     */
    transformNameForUrl: function (name, reverse) {
        name = name || this.name();

        if (reverse) {
            if (name.indexOf(' ') !== -1 && name.indexOf('_') !== -1) {
                // Name has both spaces and underscores, meaning it had underscores originally
                return name;
            } else {
                return name.replace(/_/g, ' ');
            }
        } else {
            if (name.indexOf('_') !== -1) {
                // Name contains underscores, we can't do the trivial space transform
                return name;
            } else {
                // Replace all spaces with underscores
                return name.replace(/ /g, '_');
            }
        }
    },

    /**
     * Lookup a challenge by name. If found, sets the properties of this model
     * to the result, and triggers ``c:found``. If not found, triggers ``c:notFound``.
     *
     * @param name The challenge name to lookup.
     */
    findByName: function (name) {
        restRequest({
            path: this.resourceName,
            type: 'GET',
            data: {
                name: this.transformNameForUrl(name, true)
            }
        }).done((resp) => {
            if (resp.length) {
                this.set(resp[0]);
                this.trigger('c:found');
            } else {
                this.trigger('c:notFound');
            }
        });

        return this;
    }
});

export default ChallengeModel;
