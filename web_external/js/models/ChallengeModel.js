covalic.models.ChallengeModel = girder.AccessControlledModel.extend({
    resourceName: 'challenge',

    getThumbnailUrl: function (size) {
        size = size || 200;
        if (this.get('thumbnailUrl')) {
            return this.get('thumbnailUrl');
        } else {
          return window.location.protocol + '//www.gravatar.com/avatar/' +
              this._fakeHash() + '?d=identicon&s=' + size;
        }
    },

    /**
     * We use gravatar to provide default identicon images for challenges that
     * don't yet have thumbnails, so we require a hash output value. We
     * don't care to actually do an md5 hash, so we fake one that is based on
     * the name of the challenge. Gravatar automatically pads the input if it
     * is too short and truncates it if it's too long, so we just conver the
     * challenge name to a hex string and use that.
     */
    _fakeHash: function () {
        var i, s = '', name = this.name(), len = name.length;

        for (var i = 0; i < len; i += 1) {
            s += name.charCodeAt(i).toString(16);
        }

        return s;
    }
});
