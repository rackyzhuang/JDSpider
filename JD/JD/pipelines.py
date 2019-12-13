# -*- coding: utf-8 -*-
import datetime
import json
from hashlib import md5

import pymysql
from .settings import *
import happybase


class JdPipeline(object):
    def process_item(self, item, spider):
        return item


class JdAsyncpeline(object):

    def __init__(self):
        # connection database
        self.connect = pymysql.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD,
                                       db=MYSQL_DBNAME)  # 后面三个依次是数据库连接名、数据库密码、数据库名称
        # get cursor
        self.cursor = self.connect.cursor()
        print("连接数据库成功")

    def process_item(self, item, spider):
        insert_sql = """
        insert into jdspider_data(sku, p_name, detail,image,other_type,price,p_type,crawl_data) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """
        self.cursor.execute(insert_sql, (str(item['sku']), item['name'], str(item['detail']),
                                         str(item['image']), str(item['other_type']), str(item['price']),
                                         str(item['p_type']), item['crawl_date']))
        self.connect.commit()

    def close_spider(self, spider):
        # 关闭游标和连接
        self.cursor.close()
        self.connect.close()


class JDHbasepipelines(object):
    def __init__(self):
        host = HBASE_HOST
        table_name = HBASE_TABLE
        connection = happybase.Connection(host)
        table = connection.table(table_name)
        self.table = table

    def process_item(self, item, spider):
        sku = str(item['sku'])
        name = item['name']
        detail = str(item['detail'])
        image = str(item['image'])
        other_type = str(item['other_type'])
        price = str(item['price'])
        p_type = str(item['p_type'])
        crawl_date = item['crawl_date']
        self.table.put(sku,
                       {'cf1:sku': sku,
                        'cf1:detail': name,
                        'cf1:detail': detail,
                        'cf1:image': image,
                        'cf1:other_type': other_type,
                        'cf1:price': price,
                        'cf1:p_type': p_type,
                        'cf1:crawl_date': crawl_date,})

