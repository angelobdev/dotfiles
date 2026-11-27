.pragma library

// Longer bodies are cut: one pasted log or a whole e-mail would make a card taller than the screen.
var MAX_LENGTH = 4000;

// Links: only http, https and mailto, in a narrow ASCII grammar (QML has no URL parser), never decoded and judged
// again. Anything else (javascript:, file:, an address with a user name or a numeric host, escapes of control
// characters) is no link and stays plain text.
var MAX_URL = 2048;

function hostname(raw) {
  var host = String(raw).toLowerCase().replace(/\.$/, "");
  if (host.length > 253 || !/^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$/.test(host))
    return "";
  // A numeric last label is an IPv4 address to a browser (0x7f.1 is 127.0.0.1): no names that hide one.
  return /^(?:0x[0-9a-f]*|[0-9]+)$/.test(host.split(".").pop()) ? "" : host;
}

// The URL to open, or "" when it is no link this shell opens.
function safeUrl(raw) {
  var text = String(raw || "");
  if (text.length > MAX_URL || /[\x00-\x20\x7f-\x9f\\<>"'`]/.test(text) || /%(?:[01][0-9a-f]|7f|25|5c)/i.test(text))
    return "";
  var mail = /^mailto:([a-z0-9.!#$&*+\/=?^_{|}~-]{1,64})@([^?\/#]+)$/i.exec(text);
  if (mail) {
    var mailHost = hostname(mail[2]);
    return mailHost ? "mailto:" + mail[1] + "@" + mailHost : "";
  }
  var web = /^(https?):\/\/([^\/?#]+)(.*)$/i.exec(text);
  if (!web || web[2].indexOf("@") >= 0)
    return "";
  var authority = /^([^:]+)(?::([0-9]{1,5}))?$/.exec(web[2]);
  var host = authority ? hostname(authority[1]) : "";
  if (!host || (authority[2] && (+authority[2] < 1 || +authority[2] > 65535)) || /%(?![0-9a-f]{2})/i.test(web[3]))
    return "";
  return web[1].toLowerCase() + "://" + host + (authority[2] ? ":" + (+authority[2]) : "") + (web[3] || "/");
}

// Where a link goes, as shown beside its text: the host of a web address, the address of a mailto.
function destination(url) {
  var web = /^https?:\/\/([^\/:?#]+)/.exec(url);
  return web ? web[1] : url.replace(/^mailto:/, "");
}

function escape(text) {
  return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// A link as StyledText draws it. Its text says where it goes when the sender's words do not: "Open (example.com)".
function link(url, text) {
  var label = String(text || "").trim();
  var shown = label === "" || label === url || label === destination(url) ? escape(label || url) : escape(label) + " (" + escape(destination(url)) + ")";
  return '<a href="' + escape(url) + '">' + shown + "</a>";
}

// StyledText accepts only this small subset; drop attributes and image tags. A link (<a href>, or an address
// written out) is kept when safeUrl takes it. A < or > that starts no tag (plain-text bodies: "a < b", "<3",
// "->") is shown as written instead of swallowing the text between them. So is an & that starts no entity
// ("Q&A", "?a=1&b=2"): StyledText would drop the text after it.
function styled(body) {
  var text = String(body || "").replace(/[\x01\x02]/g, "");
  if (text.length > MAX_LENGTH) text = text.slice(0, MAX_LENGTH) + "…";
  var links = [];
  // Links are set aside before the rest is cleaned, then put back where they were.
  text = text.replace(/<a\s[^>]*?href\s*=\s*(["'])([^"']*)\1[^>]*>([\s\S]*?)<\/a\s*>/gi, function (whole, quote, href, inner) {
    var label = inner.replace(/<[^>]*>/g, "").replace(/&amp;/g, "&").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&quot;/g, '"');
    var url = safeUrl(href.replace(/&amp;/g, "&"));
    if (!url)
      return label;
    links.push(link(url, label));
    return "\x01" + (links.length - 1) + "\x02";
  });
  text = text.replace(/\bhttps?:\/\/[^\s<>"']+|\bmailto:[^\s<>"']+/gi, function (written) {
    // The dot or bracket that ends a sentence is no part of the address.
    var trailing = /[.,;:!?)\]]+$/.exec(written);
    var address = trailing ? written.slice(0, -trailing[0].length) : written;
    var url = safeUrl(address.replace(/&amp;/g, "&"));
    if (!url)
      return written;
    links.push(link(url, address));
    return "\x01" + (links.length - 1) + "\x02" + (trailing ? trailing[0] : "");
  });
  return clean(text).replace(/\x01([0-9]+)\x02/g, function (whole, index) {
    return links[+index];
  });
}

function clean(text) {
  return text.replace(/<\/?[A-Za-z][^<>]*>|[<>]|&(?![A-Za-z][A-Za-z0-9]*;|#[0-9]+;|#x[0-9A-Fa-f]+;)/g, function (part) {
    if (part === "<") return "&lt;";
    if (part === ">") return "&gt;";
    if (part === "&") return "&amp;";
    const match = /^<\s*(\/?)\s*(b|i|u|s|strong|em|br)\s*\/?\s*>$/i.exec(part);
    if (!match) return "";
    const name =
      { strong: "b", em: "i" }[match[2].toLowerCase()] ||
      match[2].toLowerCase();
    return name === "br" ? "<br>" : "<" + match[1] + name + ">";
  });
}

// The app line is left out when it only repeats the title ("Updates" / "Updates").
function repeatsTitle(app, summary) {
  var title = String(summary || "").trim().toLowerCase();
  return title !== "" && String(app || "").trim().toLowerCase() === title;
}

// How long ago a notification arrived, as a unit and a count: "now" under a minute, then minutes, hours
// while it is still the same day, "yesterday", and a "date" before that. Unknown times give null.
function age(then, now) {
  if (typeof then !== "number" || !isFinite(then)) return null;
  var minutes = Math.floor(Math.max(0, now - then) / 60000);
  if (minutes < 1) return { unit: "now", count: 0 };
  if (minutes < 60) return { unit: "minutes", count: minutes };
  var day = new Date(now);
  day.setHours(0, 0, 0, 0);
  if (then >= day.getTime()) return { unit: "hours", count: Math.floor(minutes / 60) };
  day.setDate(day.getDate() - 1);
  if (then >= day.getTime()) return { unit: "yesterday", count: 0 };
  return { unit: "date", count: 0 };
}
