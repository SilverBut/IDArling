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

from functools import partial
from PyQt5.QtCore import Qt, QSize, QPoint, QRect
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QRegion
from PyQt5.QtWidgets import QWidget, QLabel, QMenu, QAction, QActionGroup

from .dialogs import SettingsDialog
from ..shared.commands import RenamedUser

logger = logging.getLogger('IDArling.Interface')


class StatusWidget(QWidget):
    """
    The widget that displays the status of the connection to the server.
    """
    # Network States
    STATE_DISCONNECTED = 0
    STATE_CONNECTING = 1
    STATE_CONNECTED = 2

    def __init__(self, plugin):
        """
        Initialize the status widget.

        :param plugin: the plugin instance
        """
        super(StatusWidget, self).__init__()
        self._plugin = plugin

        self._state = self.STATE_DISCONNECTED
        self._server = None

        # Create the sub-widgets
        self._textWidget = QLabel()
        self._textWidget.setAutoFillBackground(False)
        self._textWidget.setAttribute(Qt.WA_PaintOnScreen)
        self._textWidget.setAttribute(Qt.WA_TranslucentBackground)

        self._iconWidget = QLabel()
        self._iconWidget.setAutoFillBackground(False)
        self._iconWidget.setAttribute(Qt.WA_PaintOnScreen)
        self._iconWidget.setAttribute(Qt.WA_TranslucentBackground)

        # Set a custom context menu policy
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._context_menu)
        self.update_widget()

    def update_widget(self):
        """
        Called to update the widget when its state has changed.
        """
        logger.debug("Updating widget state")

        # Get color, text and icon from state
        if self._state == StatusWidget.STATE_DISCONNECTED:
            color, text, icon = 'red', 'Disconnected', 'disconnected.png'
        elif self._state == StatusWidget.STATE_CONNECTING:
            color, text, icon = 'orange', 'Connecting', 'connecting.png'
        elif self._state == StatusWidget.STATE_CONNECTED:
            color, text, icon = 'green', 'Connected', 'connected.png'
        else:
            logger.warning('Invalid server state')
            return

        # Update the text of the widget
        if self._server is None:
            server = '&lt;no server&gt;'
        else:
            server = '%s:%d' % (self._server["host"], self._server["port"])
        textFormat = '%s | %s -- <span style="color: %s;">%s</span>'
        self._textWidget.setText(textFormat % (self._plugin.description(),
                                               server, color, text))
        self._textWidget.adjustSize()

        # Update the icon of the widget
        pixmap = QPixmap(self._plugin.resource(icon))
        pixmapHeight = self._textWidget.sizeHint().height()
        self._iconWidget.setPixmap(pixmap.scaled(pixmapHeight, pixmapHeight,
                                                 Qt.KeepAspectRatio,
                                                 Qt.SmoothTransformation))

        # Update the size of the widget
        self.updateGeometry()

    def sizeHint(self):
        """
        Called when the widget size is determined.

        :return: the size hint
        """
        width = self._textWidget.sizeHint().width()
        width += 6
        width += self._iconWidget.sizeHint().width()
        return QSize(width, self._textWidget.sizeHint().height())

    def _context_menu(self, point):
        """
        Called when the widget is right-clicked to display the context menu.

        :param point: the location where the click happened
        """
        logger.debug("Opening widget context menu")
        menu = QMenu(self)

        # Add the settings
        settings = QAction('Settings...', menu)
        iconPath = self._plugin.resource('settings.png')
        settings.setIcon(QIcon(iconPath))

        def _settings_accepted(dialog):
            name, color, notifications, navbarColorizer = dialog.get_result()
            painter = self._plugin.interface.painter
            if painter.name != name:
                self._plugin.network.send_packet(RenamedUser(painter.name,
                                                             name))
                painter.name = name
            self._plugin.interface.painter.name = name

        # Add a handler on the action
        def settingsActionTriggered():
            dialog = SettingsDialog(self._plugin)
            dialog.accepted.connect(partial(_settings_accepted, dialog))
            dialog.exec_()

        settings.triggered.connect(settingsActionTriggered)
        menu.addAction(settings)

        menu.addSeparator()
        integrated = QAction('Integrated Server', menu)
        integrated.setCheckable(True)

        def integratedActionTriggered():
            if integrated.isChecked():
                self._plugin.network.start_server()
            else:
                self._plugin.network.stop_server()

        integrated.setChecked(self._plugin.network.server_running())
        integrated.triggered.connect(integratedActionTriggered)
        menu.addAction(integrated)

        def create_servers_group(servers):
            serversGroup = QActionGroup(self)
            currentServer = self._plugin.network.server

            for server in servers:
                isConnected = self._plugin.network.connected \
                              and server["host"] == currentServer["host"] \
                              and server["port"] == currentServer["port"]
                serverText = '%s:%d' % (server["host"], server["port"])
                serverAction = QAction(serverText, menu)
                serverAction._server = server
                serverAction.setCheckable(True)
                serverAction.setChecked(isConnected)
                serversGroup.addAction(serverAction)

            def serverActionTriggered(serverAction):
                wasConnected = self._plugin.network.connected \
                    and self._plugin.network.server == server
                self._plugin.network.stop_server()
                self._plugin.network.disconnect()
                if not wasConnected:
                    self._plugin.network.connect(serverAction._server)
            serversGroup.triggered.connect(serverActionTriggered)
            return serversGroup

        # Add the discovered servers
        servers = self._plugin.network.discovery.servers
        if self._plugin.network.server_running() \
                and self._plugin.network.server in servers:
            servers.remove(self._plugin.network.server)
        if servers:
            menu.addSeparator()
            serversGroup = create_servers_group(servers)
            menu.addActions(serversGroup.actions())

        # Add the configured servers
        servers = self._plugin.config["servers"]
        if self._plugin.config["servers"]:
            menu.addSeparator()
            serversGroup = create_servers_group(servers)
            menu.addActions(serversGroup.actions())

        # Show the context menu
        menu.exec_(self.mapToGlobal(point))

    def paintEvent(self, event):
        """
        Called when the widget is painted on the window.
        """
        dpr = self.devicePixelRatioF()
        buffer = QPixmap(self.width() * dpr, self.height() * dpr)
        buffer.setDevicePixelRatio(dpr)
        buffer.fill(Qt.transparent)

        painter = QPainter(buffer)
        region = QRegion(QRect(0, 0, self._textWidget.sizeHint().width(),
                               self._textWidget.sizeHint().height()))
        self._textWidget.render(painter, QPoint(0, 0), region)
        region = QRegion(QRect(0, 0, self._iconWidget.sizeHint().width(),
                               self._iconWidget.sizeHint().height()))
        x = self._textWidget.sizeHint().width() + 3
        self._iconWidget.render(painter, QPoint(x, 0), region)
        painter.end()

        painter = QPainter(self)
        painter.drawPixmap(event.rect(), buffer, buffer.rect())
        painter.end()

    def set_state(self, state):
        """
        Set the state of the connection.

        :param state: the new state
        """
        if state != self._state:
            self._state = state
            self.update_widget()

    def set_server(self, server):
        """
        Set the server we're connected to.

        :param server: the server
        """
        if server != self._server:
            self._server = server
            self.update_widget()
