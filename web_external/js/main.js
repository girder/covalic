$(function () {
    covalic.events.trigger('g:appload.before');
    var app = new covalic.App({});
    covalic.events.trigger('g:appload.after');
});
