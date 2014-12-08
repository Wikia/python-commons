"""Implements connection manager for MediaWiki databases"""

import logging
import random

import phpserialize
import sqlalchemy

from config import Config

logger = logging.getLogger('wikia.common.mediawiki.database')


class LoadBalancer(object):
    """
    MediaWiki database load balancer
    """
    MASTER = Config.MASTER
    SLAVE = Config.SLAVE

    def __init__(self, config=None):
        self.config = config or Config()

    def get_connection(self, dbname, type=SLAVE, groups=None):
        """
        Create a connection to target database and return the connection
        """
        logger.debug("get_connection(): connecting: dbname={} type={} groups={}".format(
            dbname, self.__format_type(type), groups))
        section = self.config.get_section_by_db(dbname)
        if not section:
            section = self.__get_section_from_wiki_factory(dbname)
        servers = self.config.get_section_servers(section, type, groups)
        for server in servers.values():
            server.dbname = dbname
        connection = self.__connect_any(servers)
        logger.debug("get_connection(): connected: dbname={} type={} groups={}".format(
            dbname, self.__format_type(type), groups))
        return connection

    def get_external_connection(self, section, type=SLAVE, groups=None):
        """
        Create a connection to external database with blobs and return the connection
        """
        logger.debug("get_external_connection(): connecting: section={} type={} groups={}".format(
            section, self.__format_type(type), groups))
        servers = self.config.get_external_section_servers(section, type, groups)
        connection = self.__connect_any(servers)
        logger.debug("get_external_connection(): connected: section={} type={} groups={}".format(
            section, self.__format_type(type), groups))
        return connection

    def __get_section_from_wiki_factory(self, dbname):
        """
        Find a section/cluster that the specified wiki is in or fall back to "central" if not found
        """
        logger.debug("__get_section_from_wiki_factory(): looking for {}".format(dbname))
        connection = self.get_connection('wikicities')
        sql = sqlalchemy.text("""
            SELECT cv_value
            FROM city_variables
            WHERE cv_variable_id = (SELECT cv_id FROM city_variables_pool WHERE cv_name='wgDBcluster' )
            AND cv_city_id = ( SELECT city_id FROM city_list WHERE city_dbname = :dbname order by city_id limit 1 )
            """)
        result = connection.execute(sql, dbname=dbname)
        section = 'central'
        for row in result:
            section = phpserialize.unserialize(row['cv_value'])
            logger.debug("__get_section_from_wiki_factory(): found entry with cluster {}".format(section))
        connection.close()
        logger.debug("__get_section_from_wiki_factory(): result = {}".format(section))
        return section

    def __connect_any(self, servers):
        """
        Connect to any of the given servers. Search randomly through the list to find a working one.
        Return first working connection. Otherwise raise an exception.
        """
        logger.debug("__connect_any(): got {} server(s): [{}]".format(len(servers),
                                                                      ', '.join([server for server in servers.keys()])))
        servers = servers.copy()
        weights = dict([(server.name, server.load) for server in servers.values()])

        while len(weights) > 0:
            name = self.__weighted_random(weights)
            server = servers[name]
            try:
                connection = self.__connect(server)
                return connection
            except Exception as e:
                servers.pop(name)
                weights.pop(name)

        logger.debug("__connect_any(): no working server found")
        raise RuntimeError("No working server found")

    def __connect(self, server):
        """
        Connect to get given server and return the connection if successful. Otherwise an exception is thrown.
        """
        logger.debug("__connect(): trying to connect to {} ({}:{}/{})".format(
            server.name, server.ip, server.port, server.dbname))
        charset = 'latin1' if not server.utf8 else 'utf8'
        connect_str = "mysql+mysqldb://{user}:{password}@{ip}/{dbname}?charset={charset}&use_unicode=0".format(
            user=server.user, password=server.password, ip=server.ip, dbname=server.dbname,
            charset=charset)
        try:
            engine = sqlalchemy.create_engine(connect_str)
            connection = engine.connect()
            logger.debug("__connect(): connected to {}".format(server.name))
        except Exception as e:
            logger.debug("__connect(): failed to connect to {}".format(server.name))
            raise e
        return connection

    def __weighted_random(self, choices):
        """
        Return a random choice taking weights into account. Expects dict where keys are choices and values are weights.
        """
        total = sum(choices.values())
        r = int(random.uniform(0, total))
        if r >= total:
            r -= 1
        up_to = 0
        for choice, weight in choices.items():
            if up_to + weight > r:
                return choice
            up_to += weight

    def __format_type(self, type):
        if type == self.MASTER:
            return 'MASTER'
        elif type == self.SLAVE:
            return 'SLAVE'
        else:
            return str(type)
