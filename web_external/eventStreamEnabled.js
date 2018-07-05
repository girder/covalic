import eventStream from 'girder/utilities/EventStream';

let status = false;
eventStream.on('g:eventStream.start', () => {
    status = true;
}).on('g:eventStream.disable', () => {
    status = false;
}).on('g:eventStream.close', () => {
    status = false;
});

/**
 * Get the current status of the event stream.
 * true: enabled
 * false: disabled
 */
export default function () {
    return status;
}
