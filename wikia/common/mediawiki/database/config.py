"""Implements reading and interpreting YAML configuration file for MediaWiki database load balancer"""

import os
import os.path
import yaml

builtin_type = type

class Config(object):
    """
    Config reader for MediaWiki database load balancer
    """
    SLAVE = -1
    MASTER = -2

    SECTIONS_BY_DB = 'sectionsByDB'
    SECTION_LOADS = 'sectionLoads'
    GROUP_LOADS_BY_SECTION = 'groupLoadsBySection'
    SERVER_TEMPLATE = 'serverTemplate'
    HOSTS_BY_NAME = 'hostsByName'
    EXTERNAL_LOADS = 'externalLoads'
    TEMPLATE_OVERRIDES_BY_CLUSTER = 'templateOverridesByCluster'
    TEMPLATE_OVERRIDES_BY_SERVER = 'templateOverridesByServer'

    TYPE_MASTERS = 'masters'
    TYPE_SLAVES = 'slaves'

    DEFAULT_MYSQL_PORT = 3306

    ENV_VAR_DATABASE_YAML = 'WIKIA_DB_YML'

    def __init__(self, config_file=None):
        self.config_file = config_file
        if not self.config_file:
            self.config_file = os.environ[self.ENV_VAR_DATABASE_YAML]

        self.__load()

    def __load(self):
        with open(self.config_file) as f:
            data = yaml.safe_load(f)

        self.config = data[0]
        self.sections = data[1]
        self.externals = data[2]

    def get_section_by_db(self, dbname):
        """
        Get a section for a specified database if it is found in config. Otherwise None is returned.
        """
        return self.config[self.SECTIONS_BY_DB].get(dbname)

    def get_section_servers(self, section, type = SLAVE, groups = None):
        """
        Get a list of servers for the specified criteria in the main pool of databases.
        """
        self.__fix_section_format(section)

        loads = self.__get_section_loads(section, type, groups)

        servers = {}
        for name, load in loads.items():
            servers[name] = self.__build_server_info(section, name, load)

        return servers

    def get_external_section_servers(self, section, type = SLAVE, groups = None):
        """
        Get a list of servers for the specified criteria in the external pool of databases.
        """
        self.__fix_external_section_format(section)

        loads = self.__get_external_section_loads(section, type, groups)

        servers = {}
        for name, load in loads.items():
            servers[name] = self.__build_server_info(section, name, load)

        return servers

    def __get_section_loads(self, section, type = SLAVE, groups = None):
        """
        Get a list of server names and loads for the specified criteria in the main pool.
        """
        key = None
        if type == self.MASTER:
            key = self.TYPE_MASTERS
        elif type == self.SLAVE:
            key = self.TYPE_SLAVES
        loads = self.config[self.SECTION_LOADS][section][key]

        if type == self.SLAVE and groups is not None:
            group_loads = self.__get_section_groups_loads(section,groups)
            loads = group_loads or loads

        return loads

    def __get_section_groups_loads(self, section, groups):
        """
        Get a list of server names and loads if any group matches the arguments. Otherwise return None.
        """
        if type(groups) is not list:
            groups = [groups]

        for group in groups:
            if group in self.config[self.GROUP_LOADS_BY_SECTION][section]:
                return self.config[self.GROUP_LOADS_BY_SECTION][section][group]

        return None

    def __get_external_section_loads(self, section, type = SLAVE, groups = None):
        """
        Get a list of server names and loads for the specified criteria in the external pool.
        """
        key = None
        if type == self.MASTER:
            key = self.TYPE_MASTERS
        elif type == self.SLAVE:
            key = self.TYPE_SLAVES
        loads = self.config[self.EXTERNAL_LOADS][section][key]

        return loads

    def __build_server_info(self, section, name, load):
        """
        Get a ServerInfo object for the specified server.
        """
        params = self.config[self.SERVER_TEMPLATE].copy()
        if section in self.config[self.TEMPLATE_OVERRIDES_BY_CLUSTER]:
            params.update(self.config[self.TEMPLATE_OVERRIDES_BY_CLUSTER][section])
        if name in self.config[self.TEMPLATE_OVERRIDES_BY_SERVER]:
            params.update(self.config[self.TEMPLATE_OVERRIDES_BY_SERVER][name])

        ip, port = self.__resolve_name(name)
        params.update({
            'name': name,
            'ip': ip,
            'port': port,
            'load': load,
        })
        return ServerInfo(**params)

    def __resolve_name(self, name):
        """
        Resolve a server name into ip and port
        """
        hostname = name
        port = self.DEFAULT_MYSQL_PORT
        if ':' in name:
            hostname, port = name.split(':',2)
            port = int(port)

        ip = self.config[self.HOSTS_BY_NAME][hostname]
        return ip, port

    def __fix_section_format(self, section):
        """
        Fix the specified section in configuration file if it uses an old format.
        """
        if self.TYPE_MASTERS not in self.config[self.SECTION_LOADS][section]:
            loads = self.config[self.SECTION_LOADS][section]

            master_name = self.sections[section][0]
            masters = {
                master_name: loads[master_name]
            }

            slaves = loads
            slaves.pop(master_name)

            self.config[self.SECTION_LOADS][section] = {
                self.TYPE_MASTERS: masters,
                self.TYPE_SLAVES: slaves
            }

    def __fix_external_section_format(self, section):
        """
        Fix the specified section in configuration file if it uses an old format (external pool).
        """
        if self.TYPE_MASTERS not in self.config[self.EXTERNAL_LOADS][section]:
            loads = self.config[self.EXTERNAL_LOADS][section]

            master_name = self.externals[section][0]
            masters = {
                master_name: loads[master_name]
            }

            slaves = loads
            slaves.pop(master_name)

            self.config[self.EXTERNAL_LOADS][section] = {
                self.TYPE_MASTERS: masters,
                self.TYPE_SLAVES: slaves
            }

class ServerInfo(object):
    def __init__(self, name, ip, port, dbname, user, password, type, flags, utf8, load, **kwargs):
        self.name = name
        self.ip = ip
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.type = type
        self.flags = flags
        self.max_lag = kwargs['max lag']
        self.utf8 = utf8
        self.load = load
