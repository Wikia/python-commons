__author__ = 'garth'

import os
import os.path
import yaml


class Config(object):
    """
    A class to read the DB.yml file provided by Wikia and provide a layer of abstraction to its hideousness

    A note about the nomenclature used in the DB config and thus in this module:

    * section : A 'section' is a named set of master + slave DBs.  For example, the section 'c1' is the first user
                cluster, section 'datawarehouse' is used for analytics data.
    * cluster : A cluster is a section that is used for sharding by wiki.
    * host    : A specific machine referred to by name or IP.  The host 'db-sa1' is a slave in section c1.
    * server  : A running instance of MySQL.  This will include host information (hostname or IP) as well as
                connection information (un, pw, port, etc)
    """

    config_path = ''

    conf = {}
    sections = {}
    externals = {}

    def __init__(self, config_path=''):
        # Use a passed in path if it exists
        if config_path:
            if os.path.exists(config_path):
                self.config_path = config_path
            else:
                raise IOError("Config file '{0}' does not exist".format(config_path))
        else:
            self.config_path = os.environ['WIKIA_DB_YML']

        self.read_config()

    def read_config(self):
        """
        Read the YAML contents of the config file found during intialization
        """

        f = open(self.config_path, 'r')
        yaml_data = f.read()
        data = yaml.load(yaml_data)

        self.conf = data[0]
        self.sections = data[1]
        self.externals = data[2]

    def get_global_db_section(self, name):
        """
        Given a global DB name, return the name of the section it resides in
        """
        if name in self.conf['sectionsByDB']:
            return self.conf['sectionsByDB'][name]

    def get_host_load(self, section, host):
        """
        Given a section and host, return the load for that host

        :param section: The section to return load information for
        :param host: The host in that section to return load
        :return: An integer representing the load
        """
        loads = self.conf['sectionLoads']

        # If this is a non-existent session, raise an exception
        if section not in loads:
            raise KeyError("Section '{0}' not defined in config".format(section))

        # If the host we're looking for isn't in this section, raise an exception
        if host not in loads[section]:
            raise KeyError("Host '{0}' has no defined load in section {1}".format(host, section))

        return loads[section][host]

    def get_host_ip(self, hostname):
        """
        Return the IP for the host given

        :param hostname: A hostname
        :return: An IP
        """
        if hostname not in self.conf['hostsByName']:
            raise KeyError("No IP found for host '{0}'".format(hostname))

        return self.conf['hostsByName'][hostname];

    def get_server_detail(self, hostname, key):
        """
        Get a connection detail for a server given a hostname and the detail needed.  This will check
        host specific details first then fallback to defaults.

        :param hostname: The hostname to retrieve details for
        :param key: The key to lookup (valid keys are user, password, type, flags, max lag, utf8)
        :return: The value for the key given
        """
        # See if this is defined in the overrides for this host
        if hostname in self.conf['templateOverridesByServer']:
            if key in self.conf['templateOverridesByServer'][hostname]:
                return self.conf['templateOverridesByServer'][hostname][key]

        # Return some default (keys are not always defined in the config)
        if key not in self.conf['serverTemplate']:
            return ''

        # And return it
        return self.conf['serverTemplate'][key]

    def get_section_servers(self, section):
        """
        Return a list of server info for a given section.

        :param section: A section name
        :return: A list of ServerInfo objects
        :rtype: list[ServerInfo]
        """

        if section not in self.sections:
            raise KeyError("Section '{0}' not defined in config".format(section))

        servers = []
        master = True
        for hostname in self.sections[section]:
            info = ServerInfo()
            info.master = master
            info.hostname = hostname
            info.ip = self.get_host_ip(hostname)
            info.username = self.get_server_detail(hostname, 'user')
            info.password = self.get_server_detail(hostname, 'password')
            info.max_lag = self.get_server_detail(hostname, 'max lag')
            info.utf8 = self.get_server_detail(hostname, 'utf8')
            info.flags = self.get_server_detail(hostname, 'flags')
            info.load = self.get_host_load(section, hostname)

            servers.append(info)

            # All further hosts are slaves
            master = False

        return servers


class ServerInfo:
    """
    A class to encapsulate the information about a DB server
    """

    hostname = ''
    ip = ''
    username = ''
    password = ''
    max_lag = 0
    utf8 = False
    flags = 0
    load = 0
    master = False

    def __init__(self):
        pass
