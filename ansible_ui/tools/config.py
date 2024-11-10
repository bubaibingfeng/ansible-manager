
result_db = 4
ansible_remote_user = 'root'
ansible_result_redis_db  = 10
inventory = 'scripts/inventory'
# BROKER = "redis://:%s@127.0.0.1:6379/3" % REDIS_PD
# BACKEND = "redis://:%s@127.0.0.1:6379/4" % REDIS_PD
# REDIS_ADDR = '127.0.0.1'
# REDIS_PORT = 6379
# REDIS_PD = ''
REDIS_PD ="9d6TlWfyxM7tu91P4y91"
BROKER = "redis://:%s@172.20.134.74:31595/3" % REDIS_PD
BACKEND = "redis://:%s@172.20.134.74:31595/4" % REDIS_PD
REDIS_PORT = 31595
REDIS_ADDR = '172.20.134.74'