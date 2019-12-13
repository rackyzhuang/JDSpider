# -*- coding: utf-8 -*-


BOT_NAME = 'JD'

SPIDER_MODULES = ['JD.spiders']
NEWSPIDER_MODULE = 'JD.spiders'


# LOG_LEVEL = 'WARNING'
# 打開代理
HTTPPROXY_ENABLED = True
RETRY_ENABLED = True
RETRY_TIMES = 5
# 禁止重定向
REDIRECT_ENABLED = False

# 配置分佈式
# 1. 替换原来的请求调度器的实现类，使用 scrapy-redis 中请求调度器
SCHEDULER = "scrapy_redis.scheduler.Scheduler"
# 2. 设置去重类，实现去重的代码规则，会生成 去重指纹 存在 redis 中
DUPEFILTER_CLASS = "scrapy_redis.dupefilter.RFPDupeFilter"
# 3. 开启增量式
SCHEDULER_PERSIST = True
# 4. 配置redis
REDIS_URL = "redis://127.0.0.1:6379"

#  設置mysql存儲
MYSQL_HOST = '127.0.0.1'
MYSQL_DBNAME = 'jd_data'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '9694'

# 配置hbase
HBASE_HOST='172.16.254.129'
HBASE_TABLE='jd'

# 設置每秒發起請求數
DOWNLOAD_DELAY = 5

DOWNLOADER_MIDDLEWARES = {
   # 'scrapy.contrib.downloadermiddleware.httpproxy.HttpProxyMiddleware':543,
   'JD.middlewares.RandomUserAgent': 543,
   # 'JD.middlewares.MyProxyMiddleware': 543,
}

ITEM_PIPELINES = {
   # 'scrapy_redis.pipelines.RedisPipeline': 400,
   # 'JD.pipelines.JdAsyncpeline': 400,
   # 'JD.pipelines.JDHbasepipelines': 400
}
