# main.py
#
# Copyright 2024 mirkobrombin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundationat version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GnomeDesktop", "4.0")
gi.require_version("GWeather", "4.0")
gi.require_version("Vte", "3.91")
gi.require_version("NM", "1.0")
gi.require_version("NMA4", "1.0")

import logging
import sys
from gettext import gettext as _
import os

from gi.repository import Adw, Gio

from lingmo_installer.windows.main_window import LingmoWindow
from lingmo_installer.windows.window_unsupported import LingmoUnsupportedWindow
from lingmo_installer.windows.window_ram import LingmoRamWindow
from lingmo_installer.windows.window_cpu import LingmoCpuWindow
from lingmo_installer.core.system import Systeminfo


logging.basicConfig(level=logging.INFO)


class LingmoInstaller(Adw.Application):
    """The main application singleton class."""

    def __init__(self):
        super().__init__(
            application_id="org.lingmoos.Installer",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.create_action("quit", self.close, ["<primary>q"])

    def do_activate(self):
        """
        Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.

        """

        win = self.props.active_window
        if not win:
            if not Systeminfo.is_ram_enough() and "IGNORE_RAM" not in os.environ:
                win = LingmoRamWindow(application=self)  # Not enough RAM
            elif not Systeminfo.is_cpu_enough() and "IGNORE_CPU" not in os.environ:
                win = LingmoCpuWindow(application=self)  # Not enough CPU
            elif not Systeminfo.is_uefi():
                win = LingmoUnsupportedWindow(application=self)  # Not UEFI
            else:
                win = LingmoWindow(application=self)  # All good
        win.present()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

    def close(self, *args):
        """Close the application."""
        self.quit()


def main(version):
    """The application's entry point."""
    app = LingmoInstaller()
    return app.run(sys.argv)
