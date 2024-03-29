# builder.py
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

import logging
import os
import subprocess
import sys
from gettext import gettext as _

from lingmo_installer.defaults.conn_check import LingmoDefaultConnCheck
from lingmo_installer.defaults.disk import LingmoDefaultDisk
from lingmo_installer.defaults.encryption import LingmoDefaultEncryption
from lingmo_installer.defaults.keyboard import LingmoDefaultKeyboard
from lingmo_installer.defaults.language import LingmoDefaultLanguage
from lingmo_installer.defaults.network import LingmoDefaultNetwork
from lingmo_installer.defaults.nvidia import LingmoDefaultNvidia
from lingmo_installer.defaults.vm import LingmoDefaultVm
from lingmo_installer.defaults.timezone import LingmoDefaultTimezone
from lingmo_installer.defaults.welcome import LingmoDefaultWelcome
from lingmo_installer.layouts.preferences import LingmoLayoutPreferences
from lingmo_installer.layouts.yes_no import LingmoLayoutYesNo
from lingmo_installer.utils.recipe import RecipeLoader

logger = logging.getLogger("Installer::Builder")


templates = {
    "network": LingmoDefaultNetwork,
    "conn-check": LingmoDefaultConnCheck,
    "welcome": LingmoDefaultWelcome,
    "language": LingmoDefaultLanguage,
    "keyboard": LingmoDefaultKeyboard,
    "timezone": LingmoDefaultTimezone,
    "preferences": LingmoLayoutPreferences,
    "disk": LingmoDefaultDisk,
    "encryption": LingmoDefaultEncryption,
    "nvidia": LingmoDefaultNvidia,
    "vm": LingmoDefaultVm,
    "yes-no": LingmoLayoutYesNo,
}


class Builder:
    def __init__(self, window):
        self.__window = window
        self.__recipe = RecipeLoader()
        self.__register_widgets = []
        self.__register_finals = []
        self.__load()

    def __load(self):
        if "VANILLA_FAKE" in os.environ:
            logger.info("VANILLA_FAKE is set, skipping the installation process.")

        self.__window.recipe = self.recipe

        # here we create a temporary file to store the output of the commands
        # the log path is defined in the recipe
        if "log_file" not in self.__recipe.raw:
            logger.critical(_("Missing 'log_file' in the recipe."))
            sys.exit(1)

        log_path = self.__recipe.raw["log_file"]

        if not os.path.exists(log_path):
            try:
                open(log_path, "a").close()
            except OSError:
                logger.warning(_("failed to create log file: %s") % log_path)
                logging.warning(_("No log will be stored."))

        for i, (key, step) in enumerate(self.__recipe.raw["steps"].items()):
            if step.get("display-conditions"):
                _condition_met = False
                for command in step["display-conditions"]:
                    try:
                        logger.info(_("Performing display-condition: %s") % command)
                        output = subprocess.check_output(
                            command, shell=True, stderr=subprocess.STDOUT
                        )
                        if (
                            output.decode("utf-8") == ""
                            or output.decode("utf-8") == "1"
                        ):
                            logger.info(
                                _("Step %s skipped due to display-conditions") % key
                            )
                            break
                    except subprocess.CalledProcessError:
                        logger.info(
                            _("Step %s skipped due to display-conditions") % key
                        )
                        break
                else:
                    _condition_met = True

                if not _condition_met:
                    continue

            if step["template"] in templates:
                step["num"] = i
                _widget = templates[step["template"]](
                    self.__window, self.distro_info, key, step
                )
                self.__register_widgets.append(_widget)

    def get_finals(self):
        self.__register_finals = []

        for widget in self.__register_widgets:
            self.__register_finals.append(widget.get_finals())

        return self.__register_finals

    @property
    def widgets(self):
        return self.__register_widgets

    @property
    def recipe(self):
        return self.__recipe.raw

    @property
    def distro_info(self):
        return {
            "name": self.__recipe.raw["distro_name"],
            "logo": self.__recipe.raw["distro_logo"],
        }
