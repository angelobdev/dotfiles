.pragma library

// The slots of every monitor from Quickshell's Hyprland objects (the bar, the assist workspace buttons).
function fromHyprland(hyprland, minimum) {
  return build(
    hyprland.workspaces.values.map((w) => ({
      id: w.id,
      monitor: w.monitor?.name,
      count: w.toplevels.values.length,
      urgent: w.urgent,
    })),
    hyprland.monitors.values.map((m) => ({
      name: m.name,
      activeId: m.activeWorkspace?.id,
    })),
    minimum,
  );
}

function build(workspaces, monitors, minimum) {
  const result = {};
  const used = new Set(workspaces.filter((w) => w.id > 0).map((w) => w.id));
  const names = monitors.map((m) => m.name).sort();
  for (const name of names) {
    const activeId = monitors.find((m) => m.name === name)?.activeId;
    result[name] = workspaces
      .filter(
        (w) =>
          w.id > 0 && w.monitor === name && (w.id === activeId || w.count > 0),
      )
      .map((w) => ({ id: w.id, count: w.count, urgent: w.urgent }));
    let next = 1;
    while (result[name].length < Math.max(2, Math.min(10, minimum))) {
      while (used.has(next)) ++next;
      result[name].push({ id: next, count: 0, urgent: false });
      used.add(next);
    }
    result[name].sort((a, b) => a.id - b.id);
  }
  return result;
}

// The id of a workspace created past the last slot of a monitor: above that slot, so its pill lands at the
// end of the strip, and free on every monitor, placeholders included.
function newId(slots, name) {
  const own = slots[name] || [];
  const taken = new Set();
  for (const monitor in slots) for (const w of slots[monitor]) taken.add(w.id);
  let id = own.length ? own[own.length - 1].id + 1 : 1;
  while (taken.has(id)) ++id;
  return id;
}

// Where moving `steps` slots from the active one lands (positive towards the end), -1 to stay. Past the last
// slot a new workspace opens, unless that slot is empty: Hyprland drops an empty workspace once it is left,
// so a new one would only replace it.
function scrollTarget(slots, activeId, steps, createId) {
  const current = slots.findIndex((w) => w.id === activeId);
  if (current < 0) return -1;
  const last = slots.length - 1;
  if (current === last && steps > 0) return slots[last].count > 0 ? createId : -1;
  const next = Math.max(0, Math.min(last, current + steps));
  return next === current ? -1 : slots[next].id;
}
