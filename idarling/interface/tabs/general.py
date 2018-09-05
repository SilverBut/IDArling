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

        # NavbarColorizer Checkbox
        display = "Enable users display in the navigation bar"
        navbarColorizerCheckbox = QCheckBox(display)
        layout.addRow(navbarColorizerCheckbox)

        def navbarColorizerActionTriggered():
            program._plugin["user"]["navbar_colorizer"] = \
                navbarColorizerCheckbox.isChecked()
            program._plugin.save_config()

        checkbox = navbarColorizerCheckbox
        checkbox.toggled.connect(navbarColorizerActionTriggered)
        checked = program._plugin.config["user"]["navbarColorizer"]
        navbarColorizerCheckbox.setChecked(checked)

        # Notifications Checkbox
        display = "Enable notifications"
        notificationsCheckbox = QCheckBox(display)
        layout.addRow(notificationsCheckbox)

        def notificationsActionToggled():
            program._plugin.config["user"]["notifications"] = \
                notificationsCheckbox.isChecked()
            program._plugin.save_config()

        notificationsCheckbox.toggled.connect(notificationsActionToggled)
        checked = program._plugin.config["user"]["notifications"]
        notificationsCheckbox.setChecked(checked)

        # Color settings
        color_settings = self.__tab_general_color_settings(tab)
        layout.addWidget(color_settings)

        # Debug Level settings
        debugLevelLabel = QLabel("Log Level: ")
        debugLevelComboBox = QComboBox()
        debugLevelComboBox.addItem("CRITICAL", logging.CRITICAL)
        debugLevelComboBox.addItem("ERROR", logging.ERROR)
        debugLevelComboBox.addItem("WARNING", logging.WARNING)
        debugLevelComboBox.addItem("INFO", logging.INFO)
        debugLevelComboBox.addItem("DEBUG", logging.DEBUG)
        debugLevelComboBox.addItem("TRACE", logging.TRACE)

        def debugLevelInitialized():
            from idarling.plugin import logger

            index = debugLevelComboBox.findData(logger.getEffectiveLevel())
            debugLevelComboBox.setCurrentIndex(index)

        debugLevelInitialized()

        def debugLevelActivated(index):
            from idarling.plugin import logger

            level = debugLevelComboBox.itemData(index)
            logger.setLevel(level)
            program._plugin.config["level"] = level
            program._plugin.save_config()

        debugLevelComboBox.activated.connect(debugLevelActivated)
        layout.addRow(debugLevelLabel, debugLevelComboBox)

        return tab

    def __tab_general_color_settings(self, parent):
        """
        Initialize color settings in the General Settings tab
        :param parent: Parent QWidget
        :return:
        """
        program = self.program
        # Add User Color settings
        colorWidget = QWidget(parent)
        colorLayout = QHBoxLayout(colorWidget)

        colorButton = QPushButton("")
        colorButton.setFixedSize(50, 30)

        def setColor(color):
            """
            Sets the color (if valid) as user's color

            :param color: the color
            """
            if color.isValid():
                r, g, b, _ = color.getRgb()
                # IDA represents color as 0xBBGGRR
                rgb_color_ida = b << 16 | g << 8 | r
                # Qt represents color as 0xRRGGBB
                rgb_color_qt = r << 16 | g << 8 | b
                css = 'QPushButton {background-color: #%06x; color: #%06x;}' \
                    % (rgb_color_qt, rgb_color_qt)
                colorButton.setStyleSheet(css)
                program.color = rgb_color_ida

        # Add a handler on clicking color button
        def colorButtonActivated(_):
            color = QColorDialog.getColor()
            setColor(color)

        color = QColor(program._plugin.config["user"]["color"])
        setColor(color)
        colorButton.clicked.connect(colorButtonActivated)
        colorLayout.addWidget(colorButton)

        # User name
        program.usernameLine = QLineEdit()
        program.usernameLine.setText(program._plugin.config["user"]["name"])
        colorLayout.addWidget(program.usernameLine)
        return colorWidget
