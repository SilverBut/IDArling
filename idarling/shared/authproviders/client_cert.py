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

from .base import AuthProvider


class AuthProviderClientCert(AuthProvider):
    mode = "client_cert"

    def __init__(self):
        self._cfg = None

    def on_connect_create(self, sock):
        return True

    def on_auth_try(self, data):
        return True

    def on_connect_close(self, sock):
        return True

    def on_sock_close(self, sock):
        return True

    def load(self, cfg):
        self._cfg = cfg
        return True


class ClientSide(AuthProviderClientCert):
    def __init__(self):
        self.id = 1

    def on_socket_create(self, sock):
        return True


class ServerSide(AuthProviderClientCert):
    def __init__(self):
        self.id = 1

    def on_socket_create(self, sock):
        return True
