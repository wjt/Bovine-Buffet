# encoding: utf-8
#
# Malvern:
#   A bunch of sketchily-defined classes to help write applications that can be
#   developed on a Linux desktop using pygtk, but which target the N900 using
#   Hildon.
# Copyright © 2010, Will Thompson <will@willthompson.co.uk>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import gtk
import gobject

def esc(x):
    return gobject.markup_escape_text(x)

#  _______________________
# ( it's just gtk, right? )
#  -----------------------
#        o   ,__,
#         o  (oo)____
#            (__)    )\
#               ||--|| *
#

try:
    import hildon
    import portrait
    have_hildon = True
except ImportError:
    have_hildon = False

class MaybeStackableWindow(hildon.StackableWindow if have_hildon
                           else gtk.Window):
    def __init__(self, title):
        super(MaybeStackableWindow, self).__init__()

        # Fake a N900-esque size
        if not have_hildon:
            self.set_size_request(400, 240)

        self.set_title(title)

class MaybePannableArea(hildon.PannableArea if have_hildon
                        else gtk.ScrolledWindow):
    def __init__(self):
        super(MaybePannableArea, self).__init__()

        # Hildon doesn't do horizontal scroll bars
        if not have_hildon:
            self.set_policy(gtk.POLICY_NEVER, gtk.POLICY_AUTOMATIC)

class MaybeTouchSelector(hildon.TouchSelector if have_hildon else gtk.TreeView):
    # This matches hildon.TouchSelector's changed signal.
    if not have_hildon:
        __gsignals__ = {
            "changed":
                (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (int,)),
        }

    def __init__(self, store, markup_column_id):
        if have_hildon:
            # If I say text=False, add a text column, multi-select doesn't work.
            # Fucking Hildon. So I just tonk the first column's model and it
            # seems to do the job...
            super(MaybeTouchSelector, self).__init__(text=False)
            cell = gtk.CellRendererText()
            col = self.append_column(store, cell)
            col.add_attribute(cell, 'markup', markup_column_id)
            self.set_column_selection_mode(
                hildon.TOUCH_SELECTOR_SELECTION_MODE_MULTIPLE)
        else:
            super(MaybeTouchSelector, self).__init__(store)
            self.set_headers_visible(False)
            self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)

            name_col = gtk.TreeViewColumn('Name')
            self.append_column(name_col)

            cell = gtk.CellRendererText()
            name_col.pack_start(cell, True)
            name_col.add_attribute(cell, 'markup', markup_column_id)

            self.get_selection().connect('changed', self.selection_changed)

        self.store = store
        self._select(store.get_current_attendees())

    def selection_changed(self, _):
        assert not have_hildon
        self.emit("changed", 0)

    def _select(self, indices):
        if have_hildon:
            self.unselect_all(0)
            for index in indices:
                self.select_iter(0, self.store.get_iter((index,)), False)
        else:
            s = self.get_selection()
            for index in indices:
                s.select_path((index,))


gobject.type_register(MaybeTouchSelector)

class MagicButton(hildon.Button if have_hildon else gtk.Button):
    def __init__(self, label, icon_name):
        if have_hildon:
            super(MagicButton, self).__init__(
                gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT,
                hildon.BUTTON_ARRANGEMENT_HORIZONTAL,
                title=label,
                value=None)
        else:
            super(MagicButton, self).__init__(label=label)

        image = gtk.Image()
        image.set_from_icon_name(icon_name, gtk.ICON_SIZE_BUTTON)
        self.set_image(image)

class MagicEntry(hildon.Entry if have_hildon else gtk.Entry):
    def __init__(self):
        if have_hildon:
            super(MagicEntry, self).__init__(gtk.HILDON_SIZE_AUTO)
        else:
            super(MagicEntry, self).__init__()

class MagicCheckButton(hildon.CheckButton if have_hildon else gtk.CheckButton):
    def __init__(self, label):
        if have_hildon:
            super(MagicCheckButton, self).__init__(
                gtk.HILDON_SIZE_AUTO_WIDTH | gtk.HILDON_SIZE_FINGER_HEIGHT)
        else:
            super(MagicCheckButton, self).__init__()

        self.set_label(label)
