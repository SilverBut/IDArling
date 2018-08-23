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
import collections
import logging
import socket
import ssl

from ..module import Module
from .client import Client
from .server import IntegratedServer

logger = logging.getLogger('IDArling.Network')


class Network(Module):
    """
    The network module, responsible for all interactions with the server.
    """

    def __init__(self, plugin):
        super(Network, self).__init__(plugin)
        self._client = None
        self._server = None
        self._integrated = None

    @property
    def server(self):
        """
        Return information about the current server.

        :return: the server we're connected to
        """
        return self._server

    @property
    def connected(self):
        """
        Return if we are connected to any server.

        :return: if connected
        """
        return self._client.connected if self._client else False

    def _install(self):
        return True

    def _uninstall(self):
        self.disconnect()
        return True

    def connect(self, server):
        """
        Connect to the specified server.

        :param server: the server information
        :return: did the operation succeed?
        """
        # Make sure we're not already connected
        if self.connected:
            return False
        logger.info(server)
        self._server = server.copy()  # Copy in case of source being changed
        host = self._server["host"]
        port = self._server["port"]
        server_ssl_mode = self._server["server_ssl_mode"]
        client_ssl_mode = self._server["client_ssl_mode"]
        server_ssl_cert_path = self._server["server_ssl_cert_path"]
        client_ssl_cert_path = self._server["client_ssl_cert_path"]

        # Create a client
        self._client = Client(self._plugin)

        # Do the actual connection process
        logger.info("Connecting to %s:%d,..." %
                    (host, port))
        logger.info("server_ssl_mode=%d, client_ssl_mode=%d..." %
                    (server_ssl_mode, client_ssl_mode))
        # Notify the plugin of the connection
        self._plugin.notify_connecting()

        # Prepare socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        ctx = None

        # Prepare SSL on client side
        if server_ssl_mode == 1:
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                             cafile=server_ssl_cert_path)
            logger.debug("create_default_context(cafile=%s)" %
                         server_ssl_cert_path)
        elif server_ssl_mode == 2:
            # no cafile means use sys chain
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        elif server_ssl_mode != 0:
            raise ValueError("Wrong server_ssl_mode=%d when connect" %
                             server_ssl_mode)

        if ctx:
            if client_ssl_mode == 1:
                ctx.load_cert_chain(certfile=client_ssl_cert_path)
                logger.debug("load_cert_chain(certfile=%s)" %
                             client_ssl_cert_path)
            elif client_ssl_mode != 0:
                raise ValueError("Wrong client_ssl_mode=%d when connect" %
                                 client_ssl_mode)

        # Apply ctx. Client side cert is useless without server side cert.
        if server_ssl_mode:
            sock = ctx.wrap_socket(sock, server_hostname=host)

        try:
            sock.connect((host, port))
        except socket.error as e:
            logger.warning("Connection failed")
            logger.exception(e)
            self._client = None

            # Notify the plugin
            self._plugin.notify_disconnected()
            return False
        sock.settimeout(0)
        sock.setblocking(False)
        self._client.connect(sock)

        # We're connected now
        logger.info("Connected")
        # Notify the plugin
        self._plugin.notify_connected()
        return True

    def disconnect(self):
        """
        Disconnect from the current server.

        :return: did the operation succeed?
        """
        # Make sure we're actually connected
        if not self.connected:
            return False

        # Do the actual disconnection process
        logger.info("Disconnecting...")
        if self._client:
            self._client.disconnect()
        self._client = None
        self._server = None

        # Notify the plugin of the disconnection
        self._plugin.notify_disconnected()
        return True

    def send_packet(self, packet):
        """
        Send a packet to the server.

        :param packet: the packet to send
        :return: a deferred of the reply
        """
        if self.connected:
            return self._client.send_packet(packet)
        return None

    def start_server(self):
        """
        Starts the integrated server.

        :return: did the operation succeed?
        """
        if self._integrated:
            return False
        self.disconnect()

        logger.info("Starting integrated server...")
        server = IntegratedServer()
        if not server.start('0.0.0.0'):
            return False
        self._integrated = server
        integrated_arg = {
            "host": "127.0.0.1",
            "port": server.port,
            "server_ssl_mode": False,
            "client_ssl_mode": False
        }
        return self.connect(integrated_arg)

    def stop_server(self):
        """
        Stops the integrated server.

        :return: did the operation succeed?
        """
        self.disconnect()
        if not self._integrated:
            return False
        logger.info("Stopping integrated server...")
        self._integrated.stop()
        self._integrated = None
        return True

    def server_running(self):
        """
        Returns if the integrated server is running.

        :return: True if running, False otherwise
        """
        return bool(self._integrated)
