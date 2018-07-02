import $ from 'jquery';

import App from './app.js';
import events from './events';

import * as covalic from '.';

window.covalic = covalic;

$(function () {
    events.trigger('g:appload.before');
    var app = new App({
        el: 'body',
        parentView: null
    });
    events.trigger('g:appload.after', app);
});
