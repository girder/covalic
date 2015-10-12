$(function () {
    covalic.events.trigger('g:appload.before');
    covalic.mainApp = new covalic.App({
        el: 'body',
        parentView: null
    });
    covalic.events.trigger('g:appload.after');
});
