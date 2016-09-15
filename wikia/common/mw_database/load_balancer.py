import MySQLdb

from .dbconfig import ConnectionDetails
from .connection import Connection
from .dbconfig import DatabaseConfig


class LoadBalancer(object):
    CONNECTION_CLASS = Connection

    def __init__(self, db_config_file=None, service_name=None, override_consul_dc=None):
        self.db_config_file = db_config_file
        self.db_config = DatabaseConfig(self.db_config_file,
                                        self._raw_connect, self._replace_consul_dc, service_name)
        self.override_consul_dc = override_consul_dc

    def get_connection_details(self, *args, **kwargs):
        external = kwargs.pop('external', False)
        if not external:
            conn_details = self.db_config.get_connection_details(*args, **kwargs)
        else:
            conn_details = self.db_config.get_external_connection_details(*args, **kwargs)

        return conn_details

    def connect(self, *args, **kwargs):
        conn_details = self.get_connection_details(*args, **kwargs)
        return self._create_connection(self._raw_connect(conn_details), conn_details)

    def _replace_consul_dc(self, conn_details):
        if self.override_consul_dc is not None:
            conn_details = conn_details._replace(
                hostname=conn_details.hostname.replace(
                    '.service.consul',
                    '.service.{}.consul'.format(self.override_consul_dc)))
        return conn_details

    def _create_connection(self, *args, **kwargs):
        return self.CONNECTION_CLASS(*args, **kwargs)

    def _raw_connect(self, conn_details):
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