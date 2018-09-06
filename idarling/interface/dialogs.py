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
from functools import partial
import logging

import ida_loader
import ida_nalt

from PyQt5.QtCore import QRegExp, Qt  # noqa: I202
from PyQt5.QtGui import QIcon, QRegExpValidator
from PyQt5.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .tabs import TabCfgServer, TabCfgGeneral, TabCfgNetwork
from ..shared.commands import (
    GetBranches,
    GetRepositories,
    NewBranch,
    NewRepository,
    UserColorChanged,
    UserRenamed,
)
from ..shared.models import Branch, Repository


class OpenDialog(QDialog):
    """This dialog is shown to user to select which remote database to load."""

    def __init__(self, plugin):
        super(OpenDialog, self).__init__()
        self._plugin = plugin
        self._repos = None
        self._branches = None

        # General setup of the dialog
        self._plugin.logger.debug("Showing the database selection dialog")
        self.setWindowTitle("Open from Remote Server")
        icon_path = self._plugin.plugin_resource("download.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(900, 450)

        # Setup of the layout and widgets
        layout = QVBoxLayout(self)
        main = QWidget(self)
        main_layout = QHBoxLayout(main)
        layout.addWidget(main)

        self._left_side = QWidget(main)
        self._left_layout = QVBoxLayout(self._left_side)
        self._repos_table = QTableWidget(0, 1, self._left_side)
        self._repos_table.setHorizontalHeaderLabels(("Repositories",))
        self._repos_table.horizontalHeader().setSectionsClickable(False)
        self._repos_table.horizontalHeader().setStretchLastSection(True)
        self._repos_table.verticalHeader().setVisible(False)
        self._repos_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._repos_table.setSelectionMode(QTableWidget.SingleSelection)
        self._repos_table.itemSelectionChanged.connect(self._repo_clicked)
        self._left_layout.addWidget(self._repos_table)
        main_layout.addWidget(self._left_side)

        right_side = QWidget(main)
        right_layout = QVBoxLayout(right_side)
        details_group = QGroupBox("Details", right_side)
        details_layout = QGridLayout(details_group)
        self._file_label = QLabel("<b>File:</b>")
        details_layout.addWidget(self._file_label, 0, 0)
        self._hash_label = QLabel("<b>Hash:</b>")
        details_layout.addWidget(self._hash_label, 1, 0)
        details_layout.setColumnStretch(0, 1)
        self._type_label = QLabel("<b>Type:</b>")
        details_layout.addWidget(self._type_label, 0, 1)
        self._date_label = QLabel("<b>Date:</b>")
        details_layout.addWidget(self._date_label, 1, 1)
        details_layout.setColumnStretch(1, 1)
        right_layout.addWidget(details_group)
        main_layout.addWidget(right_side)

        self._branches_group = QGroupBox("Branches", right_side)
        self._branches_layout = QVBoxLayout(self._branches_group)
        self._branches_table = QTableWidget(0, 3, self._branches_group)
        labels = ("Name", "Date", "Ticks")
        self._branches_table.setHorizontalHeaderLabels(labels)
        horizontal_header = self._branches_table.horizontalHeader()
        horizontal_header.setSectionsClickable(False)
        horizontal_header.setSectionResizeMode(0, horizontal_header.Stretch)
        self._branches_table.verticalHeader().setVisible(False)
        self._branches_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._branches_table.setSelectionMode(QTableWidget.SingleSelection)
        self._branches_table.itemSelectionChanged.connect(self._branch_clicked)
        branch_double_clicked = self._branch_double_clicked
        self._branches_table.itemDoubleClicked.connect(branch_double_clicked)
        self._branches_layout.addWidget(self._branches_table)
        right_layout.addWidget(self._branches_group)

        buttons_widget = QWidget(self)
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.addStretch()
        self._accept_button = QPushButton("Open", buttons_widget)
        self._accept_button.setEnabled(False)
        self._accept_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel", buttons_widget)
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(self._accept_button)
        layout.addWidget(buttons_widget)

        # Ask the server for the list of repositories
        d = self._plugin.network.send_packet(GetRepositories.Query())
        d.add_callback(self._repos_received)
        d.add_errback(self._plugin.logger.exception)

    def _repos_received(self, reply):
        """Called when the list of repositories is received."""
        self._repos = reply.repos
        self._refresh_repos()

    def _refresh_repos(self):
        """Refreshes the repositories table."""
        self._repos_table.setRowCount(len(self._repos))
        for i, repo in enumerate(self._repos):
            item = QTableWidgetItem(repo.name)
            item.setData(Qt.UserRole, repo)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            self._repos_table.setItem(i, 0, item)

    def _repo_clicked(self):
        """Called when a repository item is clicked."""
        repo = self._repos_table.selectedItems()[0].data(Qt.UserRole)
        self._file_label.setText("<b>File:</b> %s" % str(repo.file))
        self._hash_label.setText("<b>Hash:</b> %s" % str(repo.hash))
        self._type_label.setText("<b>Type:</b> %s" % str(repo.type))
        self._date_label.setText("<b>Date:</b> %s" % str(repo.date))

        # Ask the server for the list of branches
        d = self._plugin.network.send_packet(GetBranches.Query(repo.name))
        d.add_callback(partial(self._branches_received))
        d.add_errback(self._plugin.logger.exception)

    def _branches_received(self, reply):
        """Called when the list of branches is received."""
        self._branches = reply.branches
        self._refresh_branches()

    def _refresh_branches(self):
        """Refreshes the table of branches."""

        def create_item(text, branch):
            item = QTableWidgetItem(text)
            item.setData(Qt.UserRole, branch)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            if branch.tick == -1:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)
            return item

        self._branches_table.setRowCount(len(self._branches))
        for i, branch in enumerate(self._branches):
            self._branches_table.setItem(
                i, 0, create_item(branch.name, branch)
            )
            self._branches_table.setItem(
                i, 1, create_item(branch.date, branch)
            )
            tick = str(branch.tick) if branch.tick != -1 else "<none>"
            self._branches_table.setItem(i, 2, create_item(tick, branch))

    def _branch_clicked(self):
        self._accept_button.setEnabled(True)

    def _branch_double_clicked(self):
        self.accept()

    def get_result(self):
        """Get the repository and branch selected by the user."""
        repo = self._repos_table.selectedItems()[0].data(Qt.UserRole)
        return repo, self._branches_table.selectedItems()[0].data(Qt.UserRole)


class SaveDialog(OpenDialog):
    """
    This dialog is shown to user to select which remote database to save. We
    extend the save dialog to reuse most of the UI setup code.
    """

    def __init__(self, plugin):
        super(SaveDialog, self).__init__(plugin)
        self._repo = None

        # General setup of the dialog
        self.setWindowTitle("Save to Remote Server")
        icon_path = self._plugin.plugin_resource("upload.png")
        self.setWindowIcon(QIcon(icon_path))

        # Setup the layout and widgets
        self._accept_button.setText("Save")

        # Add a button to create a new repository
        new_repo_button = QPushButton("New Repository", self._left_side)
        new_repo_button.clicked.connect(self._new_repo_clicked)
        self._left_layout.addWidget(new_repo_button)

        # Add a button to create a new branch
        self._new_branch_button = QPushButton(
            "New Branch", self._branches_group
        )
        self._new_branch_button.setEnabled(False)
        self._new_branch_button.clicked.connect(self._new_branch_clicked)
        self._branches_layout.addWidget(self._new_branch_button)

    def _repo_clicked(self):
        super(SaveDialog, self)._repo_clicked()
        self._repo = self._repos_table.selectedItems()[0].data(Qt.UserRole)
        self._new_branch_button.setEnabled(True)

    def _new_repo_clicked(self):
        dialog = NewRepoDialog(self._plugin)
        dialog.accepted.connect(partial(self._new_repo_accepted, dialog))
        dialog.exec_()

    def _new_repo_accepted(self, dialog):
        """Called when the repository creation dialog is accepted."""
        name = dialog.get_result()

        # Ensure we don't already have a repo with that name
        if any(repo.name == name for repo in self._repos):
            failure = QMessageBox()
            failure.setIcon(QMessageBox.Warning)
            failure.setStandardButtons(QMessageBox.Ok)
            failure.setText("A repository with that name already exists!")
            failure.setWindowTitle("New Repository")
            icon_path = self._plugin.plugin_resource("upload.png")
            failure.setWindowIcon(QIcon(icon_path))
            failure.exec_()
            return

        # Get all the information we need and sent it to the server
        hash = ida_nalt.retrieve_input_file_md5().lower()
        file = ida_nalt.get_root_filename()
        type = ida_loader.get_file_type_name()
        date_format = "%Y/%m/%d %H:%M"
        date = datetime.datetime.now().strftime(date_format)
        repo = Repository(name, hash, file, type, date)
        d = self._plugin.network.send_packet(NewRepository.Query(repo))
        d.add_callback(partial(self._new_repo_received, repo))
        d.add_errback(self._plugin.logger.exception)

    def _new_repo_received(self, repo, _):
        """Called when the new repository reply is received."""
        self._repos.append(repo)
        self._refresh_repos()
        row = len(self._repos) - 1
        self._repos_table.selectRow(row)
        self._accept_button.setEnabled(False)

    def _refresh_repos(self):
        super(SaveDialog, self)._refresh_repos()
        hash = ida_nalt.retrieve_input_file_md5().lower()
        for row in range(self._repos_table.rowCount()):
            item = self._repos_table.item(row, 0)
            repo = item.data(Qt.UserRole)
            if repo.hash != hash:
                item.setFlags(item.flags() & ~Qt.ItemIsEnabled)

    def _new_branch_clicked(self):
        """Called when the new branch button is clicked."""
        dialog = NewBranchDialog(self._plugin)
        dialog.accepted.connect(partial(self._new_branch_accepted, dialog))
        dialog.exec_()

    def _new_branch_accepted(self, dialog):
        """Called when the new branch dialog is accepted."""
        name = dialog.get_result()

        # Ensure we don't already have a branch with that name
        if any(br.name == name for br in self._branches):
            failure = QMessageBox()
            failure.setIcon(QMessageBox.Warning)
            failure.setStandardButtons(QMessageBox.Ok)
            failure.setText("A branch with that name already exists!")
            failure.setWindowTitle("New Branch")
            icon_path = self._plugin.plugin_resource("upload.png")
            failure.setWindowIcon(QIcon(icon_path))
            failure.exec_()
            return

        # Get all the information we need and sent it to the server
        date_format = "%Y/%m/%d %H:%M"
        date = datetime.datetime.now().strftime(date_format)
        branch = Branch(self._repo.name, name, date, -1)
        d = self._plugin.network.send_packet(NewBranch.Query(branch))
        d.add_callback(partial(self._new_branch_received, branch))
        d.add_errback(self._plugin.logger.exception)

    def _new_branch_received(self, branch, _):
        """Called when the new branch reply is received."""
        self._branches.append(branch)
        self._refresh_branches()
        row = len(self._branches) - 1
        self._branches_table.selectRow(row)

    def _refresh_branches(self):
        super(SaveDialog, self)._refresh_branches()
        for row in range(self._branches_table.rowCount()):
            for col in range(3):
                item = self._branches_table.item(row, col)
                item.setFlags(item.flags() | Qt.ItemIsEnabled)


class NewRepoDialog(QDialog):
    """The dialog shown when an user wants to create a new repository."""

    def __init__(self, plugin):
        super(NewRepoDialog, self).__init__()
        self._plugin = plugin

        # General setup of the dialog
        self._plugin.logger.debug("New repo dialog")
        self.setWindowTitle("New Repository")
        icon_path = plugin.plugin_resource("upload.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(100, 100)

        # Set up the layout and widgets
        layout = QVBoxLayout(self)

        self._nameLabel = QLabel("<b>Repository Name</b>")
        layout.addWidget(self._nameLabel)
        self._nameEdit = QLineEdit()
        self._nameEdit.setValidator(QRegExpValidator(QRegExp("[a-zA-Z0-9-]+")))
        layout.addWidget(self._nameEdit)

        buttons = QWidget(self)
        buttons_layout = QHBoxLayout(buttons)
        create_button = QPushButton("Create")
        create_button.clicked.connect(self.accept)
        buttons_layout.addWidget(create_button)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_button)
        layout.addWidget(buttons)

    def get_result(self):
        """Get the name entered by the user."""
        return self._nameEdit.text()


class NewBranchDialog(NewRepoDialog):
    """
    The dialog shown when an user wants to create a new branch. We extend the
    new repository dialog to avoid duplicating the UI setup code.
    """

    def __init__(self, plugin):
        super(NewBranchDialog, self).__init__(plugin)
        self.setWindowTitle("New Branch")
        self._nameLabel.setText("<b>Branch Name</b>")


class SettingsDialog(QDialog):
    """
    The dialog allowing an user to configure the plugin. It has multiple tabs
    used to group the settings by category (general, network, etc.).
    """

    def __init__(self, plugin):
        super(SettingsDialog, self).__init__()
        self._plugin = plugin

        # General setup of the dialog
        self._plugin.logger.debug("Showing settings dialog")
        self.setWindowTitle("Settings")
        icon_path = self._plugin.plugin_resource("settings.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowCloseButtonHint)

        windowWidget = QWidget(self)
        windowLayout = QVBoxLayout(windowWidget)

        # Settings Tabs Container
        tabs = QTabWidget(windowWidget)
        windowLayout.addWidget(tabs)

        # General Settings tab
        tab_general = TabCfgGeneral(self, tabs)
        tabs.addTab(tab_general, "General Settings")

        # Server Settings tab
        tab_servers = TabCfgServer(self, tabs)
        tabs.addTab(tab_servers, "Server Settings")

        # Network Settings tab
        tab_network = TabCfgNetwork(self, tabs)
        tabs.addTab(tab_network, "Network Settings")

        # Action Buttons Container
        actionsWidget = QWidget(windowWidget)
        actionsLayout = QHBoxLayout(actionsWidget)
        windowLayout.addWidget(actionsWidget)

        # Save button
        def save(_):
            self._commit()
            self.accept()
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(save)
        actionsLayout.addWidget(saveButton)

        # Reset button
        resetButton = QPushButton("Reset to Default")
        resetButton.clicked.connect(self._reset)
        actionsLayout.addWidget(resetButton)

        # Cancel button
        def cancel(_):
            self.reject()
        cancelButton = QPushButton("Cancel")
        cancelButton.clicked.connect(cancel)
        actionsLayout.addWidget(cancelButton)

        self.setFixedSize(
            windowWidget.sizeHint().width(),
            windowWidget.sizeHint().height()
        )

    # Here we would like to provide some public methods
    # So methods of widgets do not need to be exported for each tab

    def _set_color(self, ida_color=None, qt_color=None):
        """Sets the color of the user color button."""
        # IDA represents colors as 0xBBGGRR
        if ida_color is not None:
            r = ida_color & 255
            g = (ida_color >> 8) & 255
            b = (ida_color >> 16) & 255

        # Qt represents colors as 0xRRGGBB
        if qt_color is not None:
            r = (qt_color >> 16) & 255
            g = (qt_color >> 8) & 255
            b = qt_color & 255

        ida_color = r | g << 8 | b << 16
        qt_color = r << 16 | g << 8 | b

        # Set the stylesheet of the button
        css = "QPushButton {background-color: #%06x; color: #%06x;}"
        self._color_button.setStyleSheet(css % (qt_color, qt_color))
        self._color = ida_color

    def _server_clicked(self, _):
        self._edit_button.setEnabled(True)
        self._delete_button.setEnabled(True)

    def _server_double_clicked(self, _):
        item = self._servers_table.selectedItems()[0]
        server = item.data(Qt.UserRole)
        # If not the current server, connect to it
        if (
            not self._plugin.network.connected
            or self._plugin.network.server != server
        ):
            self._plugin.network.stop_server()
            self._plugin.network.connect(server)
        self.accept()

    def _add_button_clicked(self, _):
        dialog = ServerInfoDialog(self._plugin, "Add server")
        dialog.accepted.connect(partial(self._add_dialog_accepted, dialog))
        dialog.exec_()

    def _edit_button_clicked(self, _):
        item = self._servers_table.selectedItems()[0]
        server = item.data(Qt.UserRole)
        dialog = ServerInfoDialog(self._plugin, "Edit server", server)
        dialog.accepted.connect(partial(self._edit_dialog_accepted, dialog))
        dialog.exec_()

    def _delete_button_clicked(self, _):
        item = self._servers_table.selectedItems()[0]
        server = item.data(Qt.UserRole)
        self._servers.remove(server)
        self._plugin.save_config()
        self._servers_table.removeRow(item.row())
        self.update()

    def _add_dialog_accepted(self, dialog):
        """Called when the dialog to add a server is accepted."""
        server = dialog.get_result()
        self._servers.append(server)
        row_count = self._servers_table.rowCount()
        self._servers_table.insertRow(row_count)

        new_server = QTableWidgetItem(
            "%s:%d" % (server["host"], server["port"])
        )
        new_server.setData(Qt.UserRole, server)
        new_server.setFlags(new_server.flags() & ~Qt.ItemIsEditable)
        self._servers_table.setItem(row_count, 0, new_server)

        new_checkbox = QTableWidgetItem()
        state = Qt.Unchecked if server["no_ssl"] else Qt.Checked
        new_checkbox.setCheckState(state)
        new_checkbox.setFlags((new_checkbox.flags() & ~Qt.ItemIsEditable))
        new_checkbox.setFlags(new_checkbox.flags() & ~Qt.ItemIsUserCheckable)
        self._servers_table.setItem(row_count, 1, new_checkbox)
        self.update()

    def _edit_dialog_accepted(self, dialog):
        """Called when the dialog to edit a server is accepted."""
        server = dialog.get_result()
        item = self._servers_table.selectedItems()[0]
        self._servers[item.row()] = server

        item.set_text("%s:%d" % (server["host"], server["port"]))
        item.setData(Qt.UserRole, server)
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)

        checkbox = self._servers_table.item(item.row(), 1)
        state = Qt.Unchecked if server["no_ssl"] else Qt.Checked
        checkbox.setCheckState(state)
        self.update()

    def _reset(self, _):
        """Resets all the form elements to their default value."""
        config = self._plugin.default_config()

        self._name_line_edit.setText(config["user"]["name"])
        self._set_color(ida_color=config["user"]["color"])

        checked = config["user"]["navbar_colorizer"]
        self._navbar_colorizer_checkbox.setChecked(checked)
        checked = config["user"]["notifications"]
        self._notifications_checkbox.setChecked(checked)

        index = self._debug_level_combo_box.findData(config["level"])
        self._debug_level_combo_box.setCurrentIndex(index)

        del self._servers[:]
        self._servers_table.clearContents()
        self._keep_cnt_spin_box.setValue(config["keep"]["cnt"])
        self._keep_intvl_spin_box.setValue(config["keep"]["intvl"])
        self._keep_idle_spin_box.setValue(config["keep"]["idle"])

    def _commit(self):
        """Commits all the changes made to the form elements."""
        name = self._name_line_edit.text()
        if self._plugin.config["user"]["name"] != name:
            old_name = self._plugin.config["user"]["name"]
            self._plugin.network.send_packet(UserRenamed(old_name, name))
            self._plugin.config["user"]["name"] = name

        if self._plugin.config["user"]["color"] != self._color:
            name = self._plugin.config["user"]["name"]
            old_color = self._plugin.config["user"]["color"]
            packet = UserColorChanged(name, old_color, self._color)
            self._plugin.network.send_packet(packet)
            self._plugin.config["user"]["color"] = self._color
            self._plugin.interface.widget.refresh()

        checked = self._navbar_colorizer_checkbox.isChecked()
        self._plugin.config["user"]["navbar_colorizer"] = checked
        checked = self._notifications_checkbox.isChecked()
        self._plugin.config["user"]["notifications"] = checked

        index = self._debug_level_combo_box.currentIndex()
        level = self._debug_level_combo_box.itemData(index)
        self._plugin.logger.setLevel(level)
        self._plugin.config["level"] = level

        self._plugin.config["servers"] = self._servers
        cnt = self._keep_cnt_spin_box.value()
        self._plugin.config["keep"]["cnt"] = cnt
        intvl = self._keep_intvl_spin_box.value()
        self._plugin.config["keep"]["intvl"] = intvl
        idle = self._keep_idle_spin_box.value()
        self._plugin.config["keep"]["idle"] = idle
        if self._plugin.network.client:
            self._plugin.network.client.set_keep_alive(cnt, intvl, idle)

        self._plugin.save_config()


class ServerInfoDialog(QDialog):
    """The dialog shown when an user creates or edits a server."""

    def __init__(self, plugin, title, server=None):
        super(ServerInfoDialog, self).__init__()
        self._plugin = plugin

        # General setup of the dialog
        self._plugin.logger.debug("Showing server info dialog")
        self.setWindowTitle(title)
        icon_path = plugin.plugin_resource("settings.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(100, 100)

        # Setup the layout and widgets
        layout = QVBoxLayout(self)

        self._server_name_label = QLabel("<b>Server Host</b>")
        layout.addWidget(self._server_name_label)
        self._server_name = QLineEdit()
        self._server_name.setPlaceholderText("127.0.0.1")
        layout.addWidget(self._server_name)

        self._server_name_label = QLabel("<b>Server Port</b>")
        layout.addWidget(self._server_name_label)
        self._server_port = QLineEdit()
        self._server_port.setPlaceholderText("31013")
        layout.addWidget(self._server_port)

        self._no_ssl_checkbox = QCheckBox("Disable SSL")
        layout.addWidget(self._no_ssl_checkbox)

        # Set the form elements values if we have a base
        if server is not None:
            self._server_name.setText(server["host"])
            self._server_port.setText(str(server["port"]))
            self._no_ssl_checkbox.setChecked(server["no_ssl"])

        down_side = QWidget(self)
        buttons_layout = QHBoxLayout(down_side)
        self._add_button = QPushButton("OK")
        self._add_button.clicked.connect(self.accept)
        buttons_layout.addWidget(self._add_button)
        self._cancel_button = QPushButton("Cancel")
        self._cancel_button.clicked.connect(self.reject)
        buttons_layout.addWidget(self._cancel_button)
        layout.addWidget(down_side)

    def get_result(self):
        """Get the server resulting from the form elements values."""
        return {
            "host": self._server_name.text() or "127.0.0.1",
            "port": int(self._server_port.text() or "31013"),
            "no_ssl": self._no_ssl_checkbox.isChecked(),
        }
