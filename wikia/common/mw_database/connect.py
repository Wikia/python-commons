__author__ = 'garth'

from config import Config
from sqlalchemy import create_engine
import random
from phpserialize import unserialize


class Connect(object):
    def __init__(self):
        self.config = Config()

    def global_master(self, dbname):
        """
        Connect to the master side of a global database
        :param dbname:
        :return: A DB handle
        """
        section = self.config.get_global_db_section(dbname)
        server_info = self.global_master_info(section)

        return self.engine_from_info(dbname, server_info)

    def global_slave(self, dbname):
        """
        Connect to a slave of a global database
        :param dbname:
        :return: A DB handle
        """
        section = self.config.get_global_db_section(dbname)
        server_info = self.global_slave_info(section)

        return self.engine_from_info(dbname, server_info)

    def cluster_master(self, dbname):
        """
        Connect to the master side of a (clustered) wiki DB
        :param dbname:
        :return: A DB handle
        """
        section = self.section_for_clustered_db(dbname)
        server_info = self.global_master_info(section)

        return self.engine_from_info(dbname, server_info)

    def cluster_slave(self, dbname):
        """
        Connect to a slave of a (clustered) wiki DB
        :param dbname:
        :return: A DB handle
        """
        section = self.section_for_clustered_db(dbname)
        server_info = self.global_slave_info(section)

        return self.engine_from_info(dbname, server_info)

    def global_master_info(self, section):
        servers = self.config.get_section_servers(section)

        # Get the master DB info
        server_info = None
        for info in servers:
            if info.master:
                server_info = info
                break

        return server_info

    def global_slave_info(self, section):
        servers = self.config.get_section_servers(section)

        # Get the slaves and figure out load balancing.  We do this by first filling the weights list with indexes into
        # the slaves list.  Each index will appear a number of times equal to that slaves load.  For example, if a
        # slave was appended at index 2 has a load of 5, we'll insert 2, five times.  Then we'll pick a random item
        # from the weights list and use that to pick the slave we'll make a connection to.
        slaves = []
        weights = []
        for info in servers:
            # If there's only one server or if there are more, select only slaves
            if len(servers) == 1 or not info.master:
                slaves.append(info)
                weights = weights + [len(slaves)-1 for x in range(info.load)]

        slave_idx = random.choice(weights)
        return servers[slave_idx]

    def section_for_clustered_db(self, dbname):
        """

        :param dbname:
        :return:
        """

        engine = self.global_slave('wikicities')
        conn = engine.connect()

        sql = """
              SELECT cv_value
                FROM city_variables
               WHERE cv_variable_id = (SELECT cv_id FROM city_variables_pool WHERE cv_name='wgDBcluster' )
                 AND cv_city_id = ( SELECT city_id FROM city_list WHERE city_dbname = '{0}' order by city_id limit 1 )
              """.format(dbname)

        result = conn.execute(sql)
        section = ''
        for row in result:
            section = unserialize(row['cv_value'])
        conn.close()
        return section

    @staticmethod
    def engine_from_info(dbname, info):
        """

        :string param dbname: Database name to connect to
        :ServerInfo param info: Server information
        :return:
        """
        if info is None:
            raise StandardError("Could not find connection info for db '{0}'".format(dbname))

        connect_str = "mysql+mysqldb://{0}:{1}@{2}/{3}?charset=utf8&use_unicode=0".format(info.username,
                                                                                          info.password,
                                                                                          info.ip,
                                                                                          dbname)
        engine = create_engine(connect_str)
        return engine
