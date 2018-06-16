#!/usr/bin/env python2
# Terminator by Chris Jones <cmsj@tenshu.net>
# GPL v2 only
"""searchbar.py - classes necessary to provide a terminal search bar"""

from gi.repository import Gtk, Gdk
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Vte

from translation import _
from config import Config


# Values bellow is currently not mapped by GObject introspection, it is a manual map from:
# https://github.com/luvit/pcre2/blob/a677f5b51bac251082856d35a48a01670e2fd4a7/src/pcre2.h.in#L120
PCRE2_UTF = 0x00080000
PCRE2_NO_UTF_CHECK = 0x40000000
PCRE2_MULTILINE = 0x00000400
PCRE2_CASELESS = 0x00000008

SEARCH_FLAGS = PCRE2_UTF | PCRE2_NO_UTF_CHECK | PCRE2_MULTILINE | PCRE2_CASELESS

# pylint: disable-msg=R0904
class Searchbar(Gtk.HBox):
    """Class implementing the Searchbar widget"""

    __gsignals__ = {
        'end-search': (GObject.SignalFlags.RUN_LAST, None, ()),
    }

    entry = None
    next = None
    prev = None
    wrap = None

    vte = None
    config = None

    searchstring = None
    searchre = None

    def __init__(self):
        """Class initialiser"""
        GObject.GObject.__init__(self)

        self.config = Config()

        self.get_style_context().add_class("terminator-terminal-searchbar")

        # Search text
        self.entry = Gtk.Entry()
        self.entry.set_activates_default(True)
        self.entry.show()
        self.entry.connect('activate', self.do_search)
        self.entry.connect('key-press-event', self.search_keypress)

        # Label
        label = Gtk.Label(label=_('Search:'))
        label.show()

        # Close Button
        close = Gtk.Button()
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.set_focus_on_click(False)
        icon = Gtk.Image()
        icon.set_from_stock(Gtk.STOCK_CLOSE, Gtk.IconSize.MENU)
        close.add(icon)
        close.set_name('terminator-search-close-button')
        if hasattr(close, 'set_tooltip_text'):
            close.set_tooltip_text(_('Close Search bar'))
        close.connect('clicked', self.end_search)
        close.show_all()

        # Next Button
        self.next = Gtk.Button(_('Next'))
        self.next.show()
        self.next.set_sensitive(False)
        self.next.connect('clicked', self.next_search)

        # Previous Button
        self.prev = Gtk.Button(_('Prev'))
        self.prev.show()
        self.prev.set_sensitive(False)
        self.prev.connect('clicked', self.prev_search)

        # Wrap checkbox
        self.wrap = Gtk.CheckButton(_('Wrap'))
        self.wrap.show()
        self.wrap.set_sensitive(True)
        self.wrap.connect('toggled', self.wrap_toggled)

        self.pack_start(label, False, True, 0)
        self.pack_start(self.entry, True, True, 0)
        self.pack_start(self.prev, False, False, 0)
        self.pack_start(self.next, False, False, 0)
        self.pack_start(self.wrap, False, False, 0)
        self.pack_end(close, False, False, 0)

        self.hide()
        self.set_no_show_all(True)

    def wrap_toggled(self, toggled):
        toggled_state = toggled.get_active()
        self.vte.search_set_wrap_around(toggled_state)
        if toggled_state:
            self.prev.set_sensitive(True)
            self.next.set_sensitive(True)

    def get_vte(self):
        """Find our parent widget"""
        parent = self.get_parent()
        if parent:
            self.vte = parent.vte

    # pylint: disable-msg=W0613
    def search_keypress(self, widget, event):
        """Handle keypress events"""
        key = Gdk.keyval_name(event.keyval)
        if key == 'Escape':
            self.end_search()
        else:
            self.prev.set_sensitive(False)
            self.next.set_sensitive(False)

    def start_search(self):
        """Show ourselves"""
        if not self.vte:
            self.get_vte()

        self.show()
        self.entry.grab_focus()

    def do_search(self, widget):
        """Trap and re-emit the clicked signal"""
        searchtext = self.entry.get_text()
        if searchtext == '':
            return

        if searchtext != self.searchstring:
            self.searchstring = searchtext
            self.searchre = Vte.Regex.new_for_search(searchtext, -1, SEARCH_FLAGS)
            self.vte.search_set_regex(self.searchre, 0)

        self.next.set_sensitive(True)
        self.prev.set_sensitive(True)
        self.next_search(None)

    def next_search(self, widget):
        """Search forwards and jump to the next result, if any"""
        found_result = self.vte.search_find_next()
        if not self.wrap.get_active():
            self.next.set_sensitive(found_result)
        else:
            self.next.set_sensitive(True)
        self.prev.set_sensitive(True)
        return

    def prev_search(self, widget):
        """Jump back to the previous search"""
        found_result = self.vte.search_find_previous()
        if not self.wrap.get_active():
            self.prev.set_sensitive(found_result)
        else:
            self.prev.set_sensitive(True)
        self.next.set_sensitive(True)
        return

    def end_search(self, widget=None):
        """Trap and re-emit the end-search signal"""
        self.searchstring = None
        self.searchre = None
        self.vte.search_set_regex(None, 0)
        self.emit('end-search')

    def get_search_term(self):
        """Return the currently set search term"""
        return(self.entry.get_text())

GObject.type_register(Searchbar)
