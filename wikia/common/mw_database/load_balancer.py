import MySQLdb

from .dbconfig import ConnectionDetails
from .connection import Connection
from .dbconfig import DatabaseConfig


class LoadBalancer(object):
    def __init__(self, db_config_file=None, service_name=None, override_consul_dc=None):
        self.db_config_file = db_config_file
        self.db_config = DatabaseConfig(self.db_config_file, self._raw_connect, service_name)
        self.override_consul_dc = override_consul_dc

    def connect(self, *args, **kwargs):
        external = kwargs.pop('external', False)
        if not external:
            conn_details = self.db_config.get_connection_details(*args, **kwargs)
        else:
            conn_details = self.db_config.get_external_connection_details(*args, **kwargs)

        return Connection(self._raw_connect(conn_details))

    def _raw_connect(self, conn_details):
        if self.override_consul_dc is not None:
            conn_details_dict = dict(conn_details.__dict__)
            conn_details_dict['hostname'] = conn_details.hostname.replace(
                '.service.consul',
                '.service.{}.consul'.format(self.override_consul_dc))
            conn_details = ConnectionDetails(**conn_details_dict)

        raw_connection = MySQLdb.connect(
            conn_details.hostname,
            conn_details.username,
            conn_details.password,
            conn_details.dbname)
        return raw_connection

    def connect_wikicities(self, *args, **kwargs):
        return self.connect('wikicities', *args, **kwargs)

    def connect_external(self, *args, **kwargs):
        return self.connect(*args, external=True, **kwargs)