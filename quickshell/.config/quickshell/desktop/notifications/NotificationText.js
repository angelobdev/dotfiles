.pragma library

// Longer bodies are cut: one pasted log or a whole e-mail would make a card taller than the screen.
var MAX_LENGTH = 4000;

// StyledText accepts only this small subset; drop attributes and image/link tags. A < or > that starts no tag
// (plain-text bodies: "a < b", "<3", "->") is shown as written instead of swallowing the text between them.
function styled(body) {
  var text = String(body || "");
  if (text.length > MAX_LENGTH) text = text.slice(0, MAX_LENGTH) + "…";
  return text.replace(/<\/?[A-Za-z][^<>]*>|[<>]/g, function (part) {
    if (part === "<") return "&lt;";
    if (part === ">") return "&gt;";
    const match = /^<\s*(\/?)\s*(b|i|u|s|strong|em|br)\s*\/?\s*>$/i.exec(part);
    if (!match) return "";
    const name =
      { strong: "b", em: "i" }[match[2].toLowerCase()] ||
      match[2].toLowerCase();
    return name === "br" ? "<br>" : "<" + match[1] + name + ">";
  });
}
