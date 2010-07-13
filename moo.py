#!/usr/bin/env python
# encoding: utf-8
#
# FOSDEM 2010 schedule application for the Nokia N900.
# Copyright © 2010, Will Thompson <will.thompson@collabora.co.uk>
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

import xml.dom.minidom as minidom

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
# A bunch of sketchily-defined classes to let this run on my laptop as well as
# on an N900 with hildon.

try:
    import hildon
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
    def __init__(self, store):
        if have_hildon:
            # If I say text=False, add a text column, multi-select doesn't work.
            # Fucking Hildon. So I just tonk the first column's model and it
            # seems to do the job...
            super(MaybeTouchSelector, self).__init__(text=True)
            self.set_model(0, store)
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
            name_col.add_attribute(cell, 'markup', 0)

# And now, the application

class PeopleWindow(MaybeStackableWindow):
    def __init__(self, store):
        super(PeopleWindow, self).__init__("People")

        self.connect('delete-event', gtk.Widget.hide_on_delete)

        new_person = gtk.Button(label="New person")
        new_person.connect('clicked', lambda _: self.show_new_person_dialog())
        new_person.set_sensitive(False)

        tv = MaybeTouchSelector(store)

        vbox = gtk.VBox()
        vbox.pack_start(new_person, expand=False)
        vbox.pack_start(tv)

        if have_hildon:
            # TouchSelector has its own panning, and gets upset if you put it
            # in a second one. :/
            self.add(vbox)
        else:
            pannable = MaybePannableArea()
            pannable.add_with_viewport(vbox)
            self.add(pannable)

class MainView(MaybeStackableWindow):
    def __init__(self, store):
        super(MainView, self).__init__("MooMenu")

        self.store = store

        self.pw = PeopleWindow(store)

        select_people = gtk.Button(label="Select people")
        select_people.connect('clicked', lambda button: self.pw.show_all())

        menu = gtk.Label()
        menu.set_markup(
        """
<b>Food:</b>
    7 people
    2 vegetarians

<b>Drinks:</b>
    4× Coke
    2× orange juice
    1× water blah""")
        menu.set_properties(wrap=True)

        #menu.set_size_request(760 if have_hildon else 380, -1)

        vbox = gtk.VBox()
        vbox.pack_start(select_people, expand=False)
        vbox.pack_start(menu)

        pannable = MaybePannableArea()
        pannable.add_with_viewport(vbox)
        self.add(pannable)

    def show_people_window(self):
        pw = PeopleWindow()
        pw.show_all()

class PeopleStore(gtk.ListStore):
    COL_NAME = 0
    COL_DRINK = 1
    COL_VEGETARIAN = 2

    def __init__(self):
        super(PeopleStore, self).__init__(str, str, bool)
        self.set_sort_column_id(0, gtk.SORT_ASCENDING)

standard_people = [
    ('Simon', 'pomegranite juice', False),
    ('Alban', 'orange juice', False),
    ('Sjoerd', 'orange juice', False),
    ('David', 'orange juice', False),
    ('Will', 'orange juice', True),
    ('Mateu', 'orange juice', False),
    ('Arun', 'orange juice', False),

    ('Marco', 'Coke', False),
    ('Rob', 'Coke', False),
    ('Cosimo', 'Coke', False),
    ('Jonny', 'Coke', False),
    ('Philip', 'Coke', False),
    ('Philippe', 'Coke', False),
    ('Martin', 'Coke', False),
    ('Monty', 'Coke', False),
    ('Gordon', 'Coke', False),
    ('Elliot', 'Coke', False),
    ('Daniel', 'Coke', True),
    ('Kyle', 'Coke', False),

    ('Megan', 'Diet Coke', True),
    ('Christian', 'sparkling water', False),
    ('Vivek', 'water', False),
    ('Helen', 'water', False),
]

class App(object):
    def __init__(self):
        self.store = PeopleStore()
        for person in standard_people:
            self.store.append(person)

        self.mv = MainView(self.store)
        self.mv.connect("delete_event", gtk.main_quit, None)

    def run(self):
        self.mv.show_all()
        gtk.main()

if __name__ == "__main__":
    App().run()

# vim: sts=4 sw=4
