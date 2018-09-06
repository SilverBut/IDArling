# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
import logging

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (QHBoxLayout,
                             QWidget, QLabel,
                             QPushButton, QLineEdit,
                             QCheckBox, QTabWidget, QColorDialog, QComboBox,
                             QFormLayout)

logger = logging.getLogger('IDArling.Interface.TabCfgGeneral')


class _TabCfgGeneral:
    _instance = None  # Keep instance reference

    def __init__(self, program, parent):
        """
        Initialize General Settings in the Settings dialog

        Use "get" method to get after initialized

        :param: parent: Parent QTabWidget
        :param: program: current program
        :return: a QWidget containing general settings
        """
        if _TabCfgGeneral._instance:
            raise ValueError("You should only create TabCfgServer once")
        _TabCfgGeneral._instance = self
        self.program = program
        self.parent = parent

    def get(self):
        parent = self.parent
        program = self.program
        # TODO: code cleaning
        assert (type(parent) == QTabWidget)

        tab = QWidget(parent)
        # Set general layout
        layout = QFormLayout(tab)
        layout.setFormAlignment(Qt.AlignVCenter)

        # Add widgets and restore settings
        userWidget = QWidget(tab)
        userLayout = QHBoxLayout(userWidget)
        layout.addRow(userWidget)

        # User info settings: Color
        program._colorButton = QPushButton("")
        program._colorButton.setFixedSize(50, 30)

        # Add a handler on clicking color button
        def colorButtonActivated(_):
            program._set_color(qt_color = QColorDialog.getColor().rgb())
        program._color = program._plugin.config["user"]["color"]
        program._set_color(ida_color = program._color)
        program._colorButton.clicked.connect(colorButtonActivated)
        userLayout.addWidget(program._colorButton)

        # User info settings: Name
        program._nameLineEdit = QLineEdit()
        name = program._plugin.config["user"]["name"]
        program._nameLineEdit.setText(name)
        userLayout.addWidget(program._nameLineEdit)

        # User info settings: Notifications and Cursors
        text = "Show other users in the navigation bar"
        program._navbarColorizerCheckbox = QCheckBox(text)
        layout.addRow(program._navbarColorizerCheckbox)
        checked = program._plugin.config["user"]["navbar_colorizer"]
        program._navbarColorizerCheckbox.setChecked(checked)

        text = "Allow other users to send notifications"
        program._notificationsCheckbox = QCheckBox(text)
        layout.addRow(program._notificationsCheckbox)
        checked = program._plugin.config["user"]["notifications"]
        program._notificationsCheckbox.setChecked(checked)

        # User info settings: Debug Level
        debugLevelLabel = QLabel("Log Level: ")
        program._debugLevelComboBox = QComboBox()
        program._debugLevelComboBox.addItem("CRITICAL", logging.CRITICAL)
        program._debugLevelComboBox.addItem("ERROR", logging.ERROR)
        program._debugLevelComboBox.addItem("WARNING", logging.WARNING)
        program._debugLevelComboBox.addItem("INFO", logging.INFO)
        program._debugLevelComboBox.addItem("DEBUG", logging.DEBUG)
        program._debugLevelComboBox.addItem("TRACE", logging.TRACE)
        level = program._plugin.config["level"]
        index = program._debugLevelComboBox.findData(level)
        program._debugLevelComboBox.setCurrentIndex(index)
        layout.addRow(debugLevelLabel, program._debugLevelComboBox)

        return tab
