

'use strict';

/*
 * Some cross-browser globals
 */
if (!window.console) {
    var console = {
        log: function () {},
        error: function () {}
    };
}

var covalic = {
    models: {},
    collections: {},
    views: {},
    apiRoot: $('#c-global-info-apiroot').text(),
    staticRoot: $('#c-global-info-staticroot').text(),
    currentUser: null,
    events: _.clone(Backbone.Events)
};


// set girder properties that enable covalic to use girder as a libary
girder.apiRoot = covalic.apiRoot;
girder.staticRoot = covalic.staticRoot;
girder.handleRouting = false;
