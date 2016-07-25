wikia.common.mw_database
========================

Mediawiki database connector

Basic Usage
-----------

Creating LoadBalancer instance:

```
from wikia.common.mw_database import LoadBalancer

load_balancer = LoadBalancer(service_name="my-awesome-service")
```

Connecting to global or wiki database:

```
muppet_conn = load_balancer.connect('muppet')
muppet_conn_master = load_balancer.connect('muppet', master=True)
```

Connecting to blobs cluster:

```
blobs_conn = load_balancer.connect_external('archive1')
```

Executing a SELECT query. All of those below have the same effect:

```
result = muppet_conn.query.select('page', '*', {'page_id': 2000})
result = muppet_conn.query('SELECT * FROM page WHERE page_id = 2000')
result = muppet_conn.query('SELECT * FROM page WHERE page_id = %(page_id)s', args={'page_id': 2000})
result = muppet_conn.query('SELECT * FROM page WHERE page_id = %s', args=[2000])
```

Inspecting SELECT query results:

```
print result.affected
-- 1L
print result.all_rows
-- ((2000L, 0L, 'Vaudeville_Statler_and_Waldorf_Action_Figures', '', 28L, 0, 0, 0.292251140939, '20160603161844', 840088L, 1170L),)
print result.to_dicts
-- [{'page_counter': 28L,
--   'page_id': 2000L,
--   'page_is_new': 0,
--   'page_is_redirect': 0,
--   'page_latest': 840088L,
--   'page_len': 1170L,
--   'page_namespace': 0L,
--   'page_random': 0.292251140939,
--   'page_restrictions': '',
--   'page_title': 'Vaudeville_Statler_and_Waldorf_Action_Figures',
--   'page_touched': '20160603161844'}]

for row in result:
    print row
-- (2000L, 0L, 'Vaudeville_Statler_and_Waldorf_Action_Figures', '', 28L, 0, 0, 0.292251140939, '20160603161844', 840088L, 1170L)
```

Shortcut for executing SELECT query and getting rows as dictionaries:

```
print muppet_conn.query.select_as_dicts('page', '*', {'page_id': 2000})
```

Shortcut for getting a single field from single row:

```
print muppet_conn.query.select_field('page', 'page_title', {'page_id': 2000})
```

Executing an INSERT query:

```
result = muppet_conn_master.query.insert('log', {'log_text': 'asd', 'log_something': True})
result = muppet_conn_master.query('INSERT INTO log(log_text, log_something) VALUES ('asd', true)')
```

Inspecting INSERT query results:

```
print result.affected
-- 1L
print muppet_conn.last_insert_id()
-- 1724L
```

Executing an UPDATE query:

```
result = muppet_conn_master.query.update('page', {'page_title': 'New title'}, {'page_id': 2790})
result = muppet_conn_master.query('UPDATE page SET page_title = "New title" WHERE page_id = 2790')
```

Executing a DELETE query:

```
result = muppet_conn_master.query.delete('ipblocks', {'ipb_id': 1479})
result = muppet_conn_master.query('DELETE FROM ipblocks WHERE ipb_id = 1479')
```

Executing arbitrary SQL query:

```
result = muppet_conn.query('SHOW TABLES')
```

Using SqlLiteral (for specifying values):

```
from wikia.common.mw_database import SqlLiteral, SqlCondition

wikicities_conn = load_balancer.connect('muppet')
result = wikicities_conn.query.select('city_list', '*', {'city_last_timestamp': SqlLiteral('now() - interval 3 day')})
-- SELECT * FROM city_list WHERE city_last_timestamp = now() - interval 3 day
```

Using SqlCondition (for specifying conditions):

```
from wikia.common.mw_database import SqlLiteral, SqlCondition

result = muppet_conn.query.select('page', '*', {'anything': SqlCondition('page_id < %s', args=[100])})
result = muppet_conn.query.select('page', '*', {'anything': SqlCondition('page_id < %(page_id)s', args={'page_id':100})})
-- SELECT * FROM page WHERE page_id < 100
```
