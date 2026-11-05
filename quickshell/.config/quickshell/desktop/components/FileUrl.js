.pragma library

// A file:// URL for a local path, each part escaped, so names with spaces, # or % load as written.
function of(path) {
    return "file://" + path.split("/").map(encodeURIComponent).join("/");
}
