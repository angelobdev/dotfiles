.pragma library

// The retry rule of services/Backoff.qml, here so scripts/tests/tst_backoff.qml can check it.
var LONG_RUN = 60000;
var MAX_FAILURES = 5;
var MAX_WAIT = 60000;

// Quick exits in a row after a run of ranFor milliseconds: one more, or none after a long run.
function failures(previous, ranFor) {
    return ranFor < LONG_RUN ? Math.min(previous + 1, MAX_FAILURES) : 0;
}

// The wait before the next start: base, doubled for each quick exit, up to a minute.
function wait(base, failures) {
    return Math.min(MAX_WAIT, base * Math.pow(2, failures));
}
