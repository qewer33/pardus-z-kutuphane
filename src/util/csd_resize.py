# csd_resize.py
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Manual edge/corner resizing for undecorated X11 toplevels.

On X11 we call ``Gtk.Window.set_decorated(False)`` to drop the server-side
title bar (so our custom in-header window buttons don't get doubled up by the
window manager). The side effect is that the WM also stops providing the resize
border, and GTK only draws its own resize grips when the window is client-side
decorated via ``set_titlebar()`` -- which the X11 path deliberately avoids.

The result is a window that cannot be resized. To restore it we watch for
presses inside a thin hot-zone along each edge and kick off the standard EWMH
``_NET_WM_MOVERESIZE`` request through ``GdkToplevel.begin_resize``. Both Mutter
(Pardus etap) and xfwm4 (XFCE) honour that request even for undecorated windows,
so the WM performs the resize for us.

Only needed for undecorated X11 windows; Wayland and CSD windows already get
resize grips from GTK/the compositor.
"""

from gi.repository import Gdk, Gtk

# width of the hot-zone along each window edge, in px
_EDGE_MARGIN = 8

# edge -> cursor name, for hover feedback so users can tell the border grabs
_CURSORS = {
    Gdk.SurfaceEdge.NORTH: "n-resize",
    Gdk.SurfaceEdge.SOUTH: "s-resize",
    Gdk.SurfaceEdge.EAST: "e-resize",
    Gdk.SurfaceEdge.WEST: "w-resize",
    Gdk.SurfaceEdge.NORTH_WEST: "nw-resize",
    Gdk.SurfaceEdge.NORTH_EAST: "ne-resize",
    Gdk.SurfaceEdge.SOUTH_WEST: "sw-resize",
    Gdk.SurfaceEdge.SOUTH_EAST: "se-resize",
}


def _edge_at(x: float, y: float, width: int, height: int):
    """Return the GdkSurfaceEdge for a point near an edge/corner, or None."""
    left = x <= _EDGE_MARGIN
    right = x >= width - _EDGE_MARGIN
    top = y <= _EDGE_MARGIN
    bottom = y >= height - _EDGE_MARGIN

    if top and left:
        return Gdk.SurfaceEdge.NORTH_WEST
    if top and right:
        return Gdk.SurfaceEdge.NORTH_EAST
    if bottom and left:
        return Gdk.SurfaceEdge.SOUTH_WEST
    if bottom and right:
        return Gdk.SurfaceEdge.SOUTH_EAST
    if left:
        return Gdk.SurfaceEdge.WEST
    if right:
        return Gdk.SurfaceEdge.EAST
    if top:
        return Gdk.SurfaceEdge.NORTH
    if bottom:
        return Gdk.SurfaceEdge.SOUTH
    return None


def _press_lands_on_control(window: Gtk.Window, x: float, y: float) -> bool:
    """True if the point is over an interactive control (e.g. a header button).

    The top edge/corners overlap our custom window buttons, so guard against
    hijacking a button click for a resize.
    """
    widget = window.pick(x, y, Gtk.PickFlags.DEFAULT)
    while widget is not None and widget is not window:
        if isinstance(widget, (Gtk.Button, Gtk.Entry, Gtk.Editable)):
            return True
        widget = widget.get_parent()
    return False


def enable_edge_resize(window: Gtk.Window) -> None:
    """Give an undecorated X11 window WM-driven edge/corner resizing."""

    def _on_pressed(gesture, _n_press, x, y):
        width = window.get_width()
        height = window.get_height()
        edge = _edge_at(x, y, width, height)
        if edge is None or _press_lands_on_control(window, x, y):
            return  # not on a border, or on a button: leave the event alone

        surface = window.get_surface()
        if surface is None or not hasattr(surface, "begin_resize"):
            return

        # NB: read the timestamp via the controller, not get_current_event():
        # older PyGObject (GTK 4.8 on Pardus etap) can't translate the raw
        # GdkButtonEvent and raises TypeError.
        timestamp = gesture.get_current_event_time()
        # claim the sequence so children don't also react to this press
        gesture.set_state(Gtk.EventSequenceState.CLAIMED)
        surface.begin_resize(
            edge,
            gesture.get_current_event_device(),
            gesture.get_current_button(),
            x,
            y,
            timestamp,
        )

    click = Gtk.GestureClick()
    click.set_button(1)  # left button only
    # capture phase so the border grab is seen before child widgets; when the
    # press isn't on a border we simply don't claim it and it propagates on.
    click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    click.connect("pressed", _on_pressed)
    window.add_controller(click)

    # hover feedback: swap the cursor to a resize arrow over the edges. Track
    # the last name so we only touch the cursor when the zone actually changes.
    last = {"name": None}

    def _on_motion(_ctrl, x, y):
        edge = _edge_at(x, y, window.get_width(), window.get_height())
        name = _CURSORS.get(edge) if edge is not None else None
        if name == last["name"]:
            return
        last["name"] = name
        window.set_cursor(Gdk.Cursor.new_from_name(name, None) if name else None)

    motion = Gtk.EventControllerMotion.new()
    motion.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
    motion.connect("motion", _on_motion)
    window.add_controller(motion)
