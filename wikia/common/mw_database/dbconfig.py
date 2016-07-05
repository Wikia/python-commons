import collections
import random
import yaml


ConnectionDetails = collections.namedtuple('ConnectionDetails', ['hostname', 'username', 'password', 'dbname'])


class DatabaseConfig(object):
    def __init__(self, config_file, connect_fn, service_name=None):
        with open(config_file) as fp:
            ds_conf = yaml.load(fp)
        self.mw_config = ds_conf[0]
        self.mw_config["templateOverridesByCluster"] = self.mw_config.get("templateOverridesByCluster", {})
        self.mw_config["templateOverridesByServer"] = self.mw_config.get("templateOverridesByServer", {})
        self.mw_config["templateOverridesByService"] = self.mw_config.get("templateOverridesByService", {})
        self.cluster_config = ds_conf[1]
        self.external_cluster_config = ds_conf[2]
        self.connect_fn = connect_fn
        self.service_name = service_name

    def get_connection_details(self, dbname, master=False, wc_master=False, override_db_name=None, username=None,
                               password=None):
        cluster = self.cluster_from_dbname(dbname, master or wc_master)
        hostname = self.host_from_cluster_and_type(cluster, master=master)
        hostname, dbname, username, password = self.expand_credentials(hostname, dbname, cluster, username, password)

        if override_db_name is not None:
            dbname = override_db_name

        return ConnectionDetails(hostname=hostname, username=username, password=password, dbname=dbname)

    def get_external_connection_details(self, dbname, master=False, wc_master=False, override_db_name=None, username=None,
                                           password=None):
        hostname = self.host_from_external_cluster_and_type(dbname, master=master)
        hostname, dbname, username, password = self.expand_credentials(hostname, dbname, dbname, username, password)

        if override_db_name is not None:
            dbname = override_db_name

        return ConnectionDetails(hostname=hostname, username=username, password=password, dbname=dbname)

    def cluster_from_dbname(self, dbname, master):
        if dbname in self.mw_config['sectionsByDB']:
            cluster = self.mw_config['sectionsByDB'][dbname]
        else:
            cluster = self.cluster_from_wiki_dbname(dbname, master)
        return cluster

    def cluster_from_wiki_dbname(self, dbname, master):
        if dbname == 'wikicities':  # sanity check
            raise RuntimeError('Invalid db config - no wikicities entry')

        wikicities_details = self.get_connection_details('wikicities', master=master)
        connect_fn = self.connect_fn
        wikicities_conn = connect_fn(wikicities_details)
        cursor = wikicities_conn.cursor()
        cursor.execute('SELECT city_cluster FROM city_list WHERE city_dbname = %(db_name)s', args={
            'db_name': dbname
        })
        row = cursor.fetchone()
        if row is None:
            raise RuntimeError('Could not find wiki database: {}'.format(dbname))
        cluster = row[0]
        cursor.close()
        wikicities_conn.close()

        return cluster

    def host_from_external_cluster_and_type(self, cluster, master=False):
        return self.host_from_cluster_data_and_type(self.external_cluster_config[cluster], master=master)

    def host_from_cluster_and_type(self, cluster, master=False):
        return self.host_from_cluster_data_and_type(self.cluster_config[cluster], master=master)

    def host_from_cluster_data_and_type(self, cluster_data, master=False):
        if master is True or len(cluster_data) <= 1:
            index = 0
        else:
            index = random.randrange(1, len(cluster_data))
        return cluster_data[index]

    def expand_credentials(self, hostname, dbname, cluster=None, username=None, password=None):
        if username is None or password is None:
            username = self.mw_config["serverTemplate"]["user"]
            password = self.mw_config["serverTemplate"]["password"]

            cluster_override = self.mw_config["templateOverridesByCluster"].get(cluster, False)
            if cluster_override is not False:
                username = cluster_override.get("user", username)
                password = cluster_override.get("password", password)
                dbname = cluster_override.get("dbname", dbname)

            host_override = self.mw_config["templateOverridesByServer"].get(hostname, False)
            if host_override is not False:
                username = host_override.get("user", username)
                password = host_override.get("password", password)
                dbname = host_override.get("dbname", dbname)

            service_override = self.mw_config["templateOverridesByService"].get(self.service_name, False)
            if host_override is not False:
                username = service_override.get("user", username)
                password = service_override.get("password", password)

        return hostname, dbname, username, password
