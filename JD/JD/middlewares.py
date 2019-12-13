# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import random
from scrapy import signals
from fake_useragent import UserAgent,FakeUserAgentError
import requests
from bs4 import BeautifulSoup


class RandomUserAgent(object):

    def process_request(self, request, spider):
        user_agent = UserAgent(verify_ssl=False).random
        request.headers['User-Agent'] = user_agent
        # print(request.headers)


class MyProxyMiddleware(object):

    def process_request(self, request, spider):
        r = requests.get('http://127.0.0.1:5000/get')
        proxy = BeautifulSoup(r.text, "lxml").get_text()
        request.meta["proxy"] = 'http://' + r.text
