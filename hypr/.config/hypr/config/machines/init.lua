-- Machine profiles: what a model needs beyond the generic modules (its panel's scale, touch devices, tablet
-- switch, keys), chosen by the DMI product name. ~/.config/desktop/hypr.lua comes after them and can change
-- any of it. A model with no profile gets the generic setup: the internal display is found by its name.
local MODELS = {
    ["HP OmniBook Ultra Flip Laptop 14-fh0xxx"] = "omnibook_ultra_flip",
}

local file = io.open("/sys/class/dmi/id/product_name")
local product = ""
if file then
    product = file:read("l") or ""
    file:close()
end
if MODELS[product] then
    require("config.machines." .. MODELS[product])
end
