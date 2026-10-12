/* Run with: node tests/frontend/connection_one_handler_smoke.js
   Checks the delegated handler does not duplicate Alumni Detail's own actions. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

let ready;
let click;
let calls = 0;
let notices = 0;
const target = { getAttribute: () => '14' };
const document = {
    cookie: 'csrftoken=token',
    querySelector: () => ({ value: 'token' }),
    querySelectorAll: () => [],
    addEventListener: (name, cb) => {
        if (name === 'DOMContentLoaded') ready = cb;
        if (name === 'click') click = cb;
    }
};
const sandbox = {
    document,
    window: {},
    console,
    fetch: () => { calls++; return Promise.resolve({json: () => Promise.resolve({success: true, message: 'Sent'})}); },
    ToastUtils: {showSuccess: () => notices++, showError: () => notices++},
};
vm.runInNewContext(fs.readFileSync('static/js/connections.js', 'utf8'), sandbox);
ready();
function event(isDetail) {
    return {
        preventDefault() {},
        target: {closest(selector) {
            if (selector === '.fe-page--alumni-directory-alumni-detail-html .contact-buttons') return isDetail ? target : null;
            if (selector === '.connect-btn') return target;
            return null;
        }}
    };
}
click(event(true));
assert.equal(calls, 0, 'Detail page should not trigger the global connection request');
click(event(false));
assert.equal(calls, 1, 'Other directory pages should retain the global connection request');
console.log('PASS: Alumni Detail does not duplicate connection POSTs; directory handler remains active.');
