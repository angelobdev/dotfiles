.pragma library

// Longer bodies are cut: one pasted log or a whole e-mail would make a card taller than the screen.
var MAX_LENGTH = 4000;

// StyledText accepts only this small subset; drop attributes and image/link tags. A < or > that starts no tag
// (plain-text bodies: "a < b", "<3", "->") is shown as written instead of swallowing the text between them.
// So is an & that starts no entity ("Q&A", "?a=1&b=2"): StyledText would drop the text after it.
function styled(body) {
  var text = String(body || "");
  if (text.length > MAX_LENGTH) text = text.slice(0, MAX_LENGTH) + "…";
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
