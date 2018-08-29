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
from PyQt5.QtWidgets import (QVBoxLayout, QWidget, QTableWidget, QHBoxLayout,
                             QTableWidgetItem, QPushButton, QTabWidget,
                             QHeaderView)

logger = logging.getLogger('IDArling.Interface.TabCfgServer')


class _TabCfgServer:
    _instance = None  # Keep instance reference

    def __init__(self, program, parent):
        """
        Initialize server settings in the Settings dialog

        Use "get" method to get after initialized

        :param: parent: Parent QTabWidget
        :param: program: current program
        :return: a QWidget containing server settings
        """
        if _TabCfgServer._instance:
            raise ValueError("You should only create TabCfgServer once")
        _TabCfgServer._instance = self
        self.program = program
        self.parent = parent

    def get(self):
        parent = self.parent
        program = self.program

        assert (type(parent) == QTabWidget)

        # TODO: code cleaning
        tab = QWidget(parent)
        layout = QVBoxLayout(tab)

        servers = program._plugin.config["servers"]
        program._serversTable = QTableWidget(len(servers), 2, program)
        program._serversTable.setHorizontalHeaderLabels(("Servers", ""))
        for i, server in enumerate(servers):
            item = QTableWidgetItem('%s:%d' % (server["host"], server["port"]))
            item.setData(Qt.UserRole, server)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if program._plugin.network.server == server:
                item.setFlags((item.flags() & ~Qt.ItemIsSelectable))
            program._serversTable.setItem(i, 0, item)

            checkbox = QTableWidgetItem()
            state = Qt.Unchecked if server["no_ssl"] else Qt.Checked
            checkbox.setCheckState(state)
            checkbox.setFlags((checkbox.flags() & ~Qt.ItemIsEditable))
            checkbox.setFlags((checkbox.flags() & ~Qt.ItemIsUserCheckable))
            if program._plugin.network.server == server:
                checkbox.setFlags((checkbox.flags() & ~Qt.ItemIsSelectable))
            program._serversTable.setItem(i, 1, checkbox)

        horizontalHeader = program._serversTable.horizontalHeader()
        horizontalHeader.setSectionsClickable(False)
        horizontalHeader.setSectionResizeMode(0, QHeaderView.Stretch)
        horizontalHeader.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        program._serversTable.verticalHeader().setVisible(False)
        program._serversTable.setSelectionBehavior(QTableWidget.SelectRows)
        program._serversTable.setSelectionMode(QTableWidget.SingleSelection)
        program._serversTable.itemClicked.connect(program._server_clicked)
        program._serversTable.itemDoubleClicked.connect(
            program._server_double_clicked)
        minSZ = program._serversTable.minimumSize()
        program._serversTable.setMinimumSize(300, minSZ.height())
        layout.addWidget(program._serversTable)

        buttonsWidget = QWidget(program)
        buttonsLayout = QHBoxLayout(buttonsWidget)

        # Add server button
        program._addButton = QPushButton("Add Server")
        program._addButton.clicked.connect(program._add_button_clicked)
        buttonsLayout.addWidget(program._addButton)

        # Edit server button
        program._editButton = QPushButton("Edit Server")
        program._editButton.setEnabled(False)
        program._editButton.clicked.connect(program._edit_button_clicked)
        buttonsLayout.addWidget(program._editButton)

        # Delete server button
        program._deleteButton = QPushButton("Delete Server")
        program._deleteButton.setEnabled(False)
        program._deleteButton.clicked.connect(program._delete_button_clicked)
        buttonsLayout.addWidget(program._deleteButton)

        layout.addWidget(buttonsWidget)

        return tab
