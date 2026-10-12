.pragma library

// StyledText accepts only this small subset; drop attributes and image/link tags.
function styled(body) {
    return String(body || "").replace(/<[^>]*>/g, function(tag) {
        const match = /^<\s*(\/?)\s*(b|i|u|s|strong|em|br)\s*\/?\s*>$/i.exec(tag);
        if (!match) return "";
        const name = ({strong: "b", em: "i"})[match[2].toLowerCase()] || match[2].toLowerCase();
        return name === "br" ? "<br>" : "<" + match[1] + name + ">";
    });
}
