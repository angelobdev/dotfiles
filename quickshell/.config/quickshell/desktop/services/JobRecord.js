.pragma library

// Whether a record read back is still the run before the one just asked for: a background job writes its record
// once it holds its lock, so until then the file holds the previous run. A record that started more than 5 s
// before the request is that one, unless the request is 30 s old (the new run never started). Times in seconds;
// a request of 0 means nothing was asked for.
function stale(record, requested, now) {
    return requested > 0 && ((record && record.started) || 0) < requested - 5 && now - requested < 30;
}
