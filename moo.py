#!/usr/bin/env python
# encoding: utf-8
#
# Simple buffet provisioning application for the Nokia N900.
# Copyright © 2010, Will Thompson <will@willthompson.co.uk>
# Dedicated to the tolerant residents of barroombar@the cow, cambridge
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

from __future__ import with_statement

import os
import errno

import cPickle

import gtk
import gobject

from malvern import *

# And now, the application

class PeopleWindow(MaybeStackableWindow):
    def __init__(self, store, update_selection_cb):
        super(PeopleWindow, self).__init__("Select people")

        self.store = store
        # Would love to use a signal, but I can't because of
        # <https://bugs.maemo.org/show_bug.cgi?id=10935> :(
        self.update_selection_cb = update_selection_cb

        self.connect('delete-event', gtk.Widget.hide_on_delete)

        new_person = MagicButton(label="New person", icon_name='general_add')
        new_person.connect('clicked', lambda _: self.show_new_person_dialog())

        self.selector = MaybeTouchSelector(store, PeopleStore.COL_MARKUP)
        self.selector.connect('changed', self.selector_changed)

        vbox = gtk.VBox()
        vbox.pack_start(new_person, expand=False)
        vbox.pack_start(self.selector)

        if have_hildon:
            # TouchSelector has its own panning, and gets upset if you put it
            # in a second one. :/
            self.add(vbox)
        else:
            pannable = MaybePannableArea()
            pannable.add_with_viewport(vbox)
            self.add(pannable)

    def get_selected_indices(self):
        if have_hildon:
            paths = self.selector.get_selected_rows(0)
        else:
            _, paths = self.selector.get_selection().get_selected_rows()

        return [index for (index, ) in paths]

    def selector_changed(self, selector, _):
        ixes = self.get_selected_indices()
        self.store.set_current_attendees(ixes)
        self.update_selection_cb(ixes)

    def show_new_person_dialog(self):
        dialog = gtk.Dialog(title="New person", parent=self,
            buttons=(gtk.STOCK_SAVE, gtk.RESPONSE_APPLY))
        table = gtk.Table(rows=3, columns=2)
        table.set_col_spacing(0, 16)

        name_label = gtk.Label("Name")
        name_label.set_alignment(0, 0.5)
        drink_label = gtk.Label("Drink")
        drink_label.set_alignment(0, 0.5)

        name_entry = MagicEntry()
        drink_entry = MagicEntry()
        veg_tickybox = MagicCheckButton("Vegetarian")

        table.attach(name_label, 0, 1, 0, 1, xoptions=gtk.FILL)
        table.attach(name_entry, 1, 2, 0, 1)

        table.attach(drink_label, 0, 1, 1, 2, xoptions=gtk.FILL)
        table.attach(drink_entry, 1, 2, 1, 2)

        table.attach(veg_tickybox, 0, 2, 2, 3)

        table.show_all()

        dialog.vbox.pack_start(table)

        if dialog.run() == gtk.RESPONSE_APPLY:
            self.store.add_person(name_entry.get_text(), drink_entry.get_text(),
                veg_tickybox.get_active())
            self.store.save()

        dialog.destroy()

class MainView(MaybeStackableWindow):
    def __init__(self, store):
        super(MainView, self).__init__("Bovine Buffet")

        self.store = store
        self.pw = PeopleWindow(self.store, self.update_summary)

        select_people = MagicButton(label="Select people",
            icon_name='general_contacts_button')
        select_people.connect('clicked', lambda button: self.pw.show_all())

        self.summary = gtk.Label()
        self.summary.set_properties(wrap=True)
        self.update_summary(self.pw.get_selected_indices())

        vbox = gtk.VBox()
        vbox.pack_start(select_people, expand=False)
        vbox.pack_start(self.summary)

        pannable = MaybePannableArea()
        pannable.add_with_viewport(vbox)
        self.add(pannable)

    def update_summary(self, indices):
        people = len(indices)
        vegetarians = 0
        drinks = {}

        for i in indices:
            x = self.store[i]

            if x[PeopleStore.COL_VEGETARIAN]:
                vegetarians += 1

            drink = x[PeopleStore.COL_DRINK].lower()
            drinks[drink] = drinks.get(drink, 0) + 1

        food_summary = """
<b>Food:</b>
    %u people
    %u vegetarians
""" % (people, vegetarians)

        drink_summary = "<b>Drinks:</b>\n"

        for drink, n in sorted(drinks.iteritems(), key=(lambda pair: pair[1]),
                               reverse=True):
            drink_summary += "    %u %s\n" % (n, drink)

        self.summary.set_markup((food_summary + "\n" + drink_summary).strip())

class PeopleStore(gtk.ListStore):
    COL_NAME = 0
    COL_DRINK = 1
    COL_VEGETARIAN = 2
    COL_MARKUP = 3

    def __init__(self):
        super(PeopleStore, self).__init__(str, str, bool, str)
        self.current_attendees = []

        if not self.load():
            # Pre-seed with Collaborans
            for person in sorted(standard_people):
                self.add_person(*person)

            for i in range(len(self)):
                if self[i][PeopleStore.COL_NAME] in regulars:
                    self.current_attendees.append(i)
            self.save()

        self.set_sort_column_id(0, gtk.SORT_ASCENDING)

    def add_person(self, name, drink, vegetarian):
        vegetarian_markup = ", vegetarian" if vegetarian else ""
        markup = """%s
<span size=\"small\" color=\"gray\">%s%s</span>""" % (
            esc(name), esc(drink), vegetarian_markup)

        self.append((name, drink, vegetarian, markup))

    def get_current_attendees(self):
        return self.current_attendees

    def set_current_attendees(self, attendees):
        self.current_attendees = attendees
        self.save()

    def _config_dir(self):
        return os.environ['HOME'] + '/.config/bovine-buffet'

    def _config_file(self):
        return self._config_dir() + '/default'

    def load(self):
        try:
            with open(self._config_file(), 'r') as f:
                people = cPickle.load(f)

                for i, person in zip(range(len(people)), sorted(people)):
                    self.add_person(*person[0:3])
                    if person[3]:
                        self.current_attendees.append(i)

            return True
        except IOError, e:
            if e.errno == errno.ENOENT:
                return False

            raise
        except TypeError, e:
            print "database corrupted! :'("
            return False

    def save(self):
        try:
            os.makedirs(self._config_dir())
        except OSError, e:
            if e.errno != errno.EEXIST:
                raise

        with open(self._config_file(), 'w') as f:
            data = []

            for (row, i) in zip(self, range(len(self))):
                data.append((row[PeopleStore.COL_NAME],
                    row[PeopleStore.COL_DRINK], row[PeopleStore.COL_VEGETARIAN],
                    i in self.current_attendees))

            cPickle.dump(data, f)

regulars = [ 'Alban', 'Christian', 'Cosimo', 'Daniel', 'David', 'Elliot',
             'Jonny', 'Marco', 'Philip', 'Rob', 'Simon', 'Sjoerd', 'Will',
           ]
standard_people = [
    ('Alban', 'orange juice', False),
    ('Arun', 'orange juice', False),
    ('Christian', 'sparkling water', False),
    ('Cosimo', 'Coke', False),
    ('Daniel', 'Coke', True),
    ('David', 'orange juice', False),
    ('Elliot', 'Coke', False),
    ('Gordon', 'Coke', False),
    ('Helen', 'water', False),
    ('Jonny', 'Coke', False),
    ('Kyle', 'Coke', False),
    ('Marco', 'cOKe', False),
    ('Martin', 'Coke', False),
    ('Mateu', 'orange juice', False),
    ('Megan', 'Diet Coke', True),
    ('Monty', 'Coke', False),
    ('Philip', 'Coke', False),
    ('Philippe', 'Coke', False),
    ('Rob', 'Coke', False),
    ('Simon', 'pomegranite juice', False),
    ('Sjoerd', 'oRANge juice', False),
    ('Vivek', 'water', False),
    ('Will', 'orange juice', True),
]

class App(object):
    def __init__(self):
        self.store = PeopleStore()

        self.mv = MainView(self.store)
        self.mv.connect("delete_event", gtk.main_quit, None)

        if have_hildon:
            portrait.FremantleRotation("bovine-buffet", self.mv, version='0.1')

    def run(self):
        self.mv.show_all()
        gtk.main()

if __name__ == "__main__":
    App().run()

# vim: sts=4 sw=4
