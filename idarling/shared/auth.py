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

from .authproviders import (
    ClientAuthProviderClientCert,
    ServerAuthProviderClientCert,
)


__client_provider_list = {"client_cert": ClientAuthProviderClientCert}

__server_provider_list = {"client_cert": ServerAuthProviderClientCert}


def get_server_auth_provider(method):
    return __server_provider_list[method]


def get_client_auth_provider(method):
    return __client_provider_list[method]
