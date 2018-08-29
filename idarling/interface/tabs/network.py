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
import datetime
import logging
from functools import partial

from PyQt5.QtCore import Qt, QRegExp
from PyQt5.QtGui import QIcon, QRegExpValidator, QColor
from PyQt5.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
                             QWidget, QTableWidget, QTableWidgetItem, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QMessageBox,
                             QCheckBox, QTabWidget, QColorDialog, QComboBox,
                             QFormLayout, QSpinBox, QSpacerItem, QHeaderView)

logger = logging.getLogger('IDArling.Interface.TabCfgNetwork')


class _TabCfgNetwork:
    _instance = None  # Keep instance reference. Singleton.

    def __init__(self, program, parent):
        if _TabCfgNetwork._instance:
            raise ValueError("You should only create TabCfgServer once")
        _TabCfgNetwork._instance = self
        self.program = program
        self.parent = parent

    def get(self):
        parent = self.parent
        program = self.program

        tab = QWidget(parent)
        layout = QFormLayout(tab)

        def update_keep_alive():
            program._plugin.save_config()
            cnt = program._plugin.config["keep"]["cnt"]
            intvl = program._plugin.config["keep"]["intvl"]
            idle = program._plugin.config["keep"]["idle"]
            if program._plugin.network.client:
                program._plugin.network.client.set_keep_alive(cnt, intvl, idle)

        keepCntLabel = QLabel("Keep-Alive Count: ")
        keepCntSpinBox = QSpinBox(keepCntLabel)
        keepCntSpinBox.setRange(0, 86400)
        keepCntSpinBox.setValue(program._plugin.config["keep"]["cnt"])
        keepCntSpinBox.setSuffix(" packets")

        def keepCntSpinBoxChanged(cnt):
            program._plugin.config["keep"]["cnt"] = cnt
            update_keep_alive()

        keepCntSpinBox.valueChanged.connect(keepCntSpinBoxChanged)
        layout.addRow(keepCntLabel, keepCntSpinBox)

        keepIntvlLabel = QLabel("Keep-Alive Interval: ")
        keepIntvlSpinBox = QSpinBox(keepIntvlLabel)
        keepIntvlSpinBox.setRange(0, 86400)
        keepIntvlSpinBox.setValue(program._plugin.config["keep"]["intvl"])
        keepIntvlSpinBox.setSuffix(" seconds")

        def keepIntvlSpinBoxChanged(intvl):
            program._plugin.config["keep"]["intvl"] = intvl
            update_keep_alive()

        keepIntvlSpinBox.valueChanged.connect(keepIntvlSpinBoxChanged)
        layout.addRow(keepIntvlLabel, keepIntvlSpinBox)

        keepIdleLabel = QLabel("Keep-Alive Idle: ")
        keepIdleSpinBox = QSpinBox(keepIdleLabel)
        keepIdleSpinBox.setRange(0, 86400)
        keepIdleSpinBox.setValue(program._plugin.config["keep"]["idle"])
        keepIdleSpinBox.setSuffix(" seconds")

        def keepIdleSpinBoxChanged(idle):
            program._plugin.config["keep"]["idle"] = idle
            update_keep_alive()

        keepIdleSpinBox.valueChanged.connect(keepIdleSpinBoxChanged)
        layout.addRow(keepIdleLabel, keepIdleSpinBox)
        return tab
