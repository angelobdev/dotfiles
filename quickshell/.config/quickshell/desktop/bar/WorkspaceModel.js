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
