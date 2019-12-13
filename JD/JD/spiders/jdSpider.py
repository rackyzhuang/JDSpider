# -*- coding: utf-8 -*-
import json
import re
import time

import scrapy

# 分佈式爬蟲
from scrapy_redis.spiders import RedisSpider
from JD.items import JdItem


class JdspiderSpider(RedisSpider):
    # name = 'jd'
    allowed_domains = ['jd.com', 'dc.3.cn']
    # start_urls = ['https://dc.3.cn/category/get?']
    name = 'jd'
    redis_key = 'jd:start_urls'

    def __init__(self, *args, **kwargs):
        # Dynamically define the allowed domains list.
        domain = kwargs.pop('domain', '')
        self.allowed_domains = list(filter(None, domain.split(',')))
        super(JdspiderSpider, self).__init__(*args, **kwargs)

    def parse(self, response):
        type_json = json.loads(str(response.body, encoding='gbk'))
        type_list = []
        # print(type_json)
        for i in type_json['data']:
            type_all_detail = {}
            # 获取banner类型
            type_all_detail['banner'] = self.extract_banner(i['b'], i['p'])
            type_all_detail['type'] = self.extract_type(i['s'])
            type_list.append(type_all_detail)
        url_list = self.get_slave3(type_list)
        for i in url_list:
            yield scrapy.Request(
                i['url'],
                callback=self.extract_product_url,
                dont_filter=True
            )
            # break

    def extract_product_url(self, response):
        max_page = response.xpath('//span[@class="p-skip"]/em/b/text()').extract_first()
        # print(max_page)
        if max_page:
            max_page = int(max_page[0])
        url_list = response.xpath('//div[contains(@class, "p-name")]//a[1]/@href').extract()
        for i in range(len(url_list)):
            product = {}
            if url_list[i].index('//') == 0:
                url_list[i] = 'https:' + url_list[i]
                sku = self._get_url_id(url_list[i])
                if sku:
                    product['sku'] = sku
                    yield scrapy.Request(
                        # url_list[i],
                        'https://item.jd.com/7269559.html',
                        meta={'product': product},
                        callback=self.extract_product_detail,
                        dont_filter=True
                    )
            # break

        next_page = response.xpath('//a[@class="pn-next"]/@href').extract_first('')
        if next_page:
            # print(next_page)
            yield scrapy.Request(
                'https://list.jd.com' + next_page,
                callback=self.extract_product_url
            )


    def extract_product_detail(self, response):
        """
        獲取商品詳細內容
        :param response:
        :return:
        """
        product = response.meta['product']
        try:
            response_text = response.body.decode('gbk')
        except Exception as e:
            try:
                response_text = response.body.decode('utf8')
            except Exception as e:
                response_text = response.body
        name_ele = response.xpath('//div[@class="sku-name"]/text()').extract()
        if len(name_ele) > 0:
            product["name"] = name_ele[0].replace(" ", "").replace("\n", "")
        if product["name"] == "":
            product["name"] = name_ele[1].replace(" ", "").replace("\n", "")
        product["detail"] = self.get_detail(response)
        product['image'] = self.get_image(response)
        product['other_type'] = self.get_other_size(response_text)
        product['sku_slave_typeid'] = self._get_sku_slave_type(response_text)
        p_type = self.get_product_type(response)
        product['p_type'] = p_type if p_type else ''
        product['crawl_date'] = time.strftime('%Y-%m-%d',time.localtime(time.time()))

        price_url = 'https://p.3.cn/prices/mgets?skuIds=J_%s'
        yield scrapy.Request(
            price_url % product['sku'],
            meta={'product': product},
            callback=self.extract_product_price,
            dont_filter=True
        )

    def extract_product_coupon(self, response):
        product = response.meta['product']
        response_json = json.loads(str(response.body, encoding='utf8'))
        skuCoupon = response_json['skuCoupon']
        skuPromote = response_json['prom']['pickOneTag']
        skuCoupon_list = []
        skuPromote_list = []
        print(skuCoupon)
        for i in skuCoupon:
            counpon = {}
            # 配額
            counpon['quota'] = i['quota']
            # 減免
            counpon['trueDiscount'] = i['trueDiscount']
            # 限制
            counpon['limit'] = i['name']
            counpon['beginTime'] = i['beginTime']
            counpon['endTime'] = i['endTime']
            skuCoupon_list.append(counpon)
        for i in skuPromote:
            prom = {}
            prom['content'] = i['content']
            prom['name'] = i['name']
            try:
                prom['adurl'] = i['adurl']
            except Exception:
                pass
            skuPromote_list.append(prom)
        product['jetso'] = {'product_coupon': skuCoupon_list, 'skuPromote': skuPromote_list}
        item = JdItem()
        item['sku'] = product['sku']
        item['name'] = product['name']
        item['detail'] = product['detail']
        item['image'] = product['image']
        item['other_type'] = product['other_type']
        item['price'] = product['price']
        item['p_type'] = product['p_type']
        item['crawl_date'] = product['crawl_date']
        item['sku_slave_typeid'] = product['sku_slave_typeid']
        item['jetso'] = product['jetso']
        print(product)
        yield item

    def extract_product_price(self, response):
        """
        獲取商品價格
        :param response:
        :return:
        """
        product = response.meta['product']
        price_json = json.loads(str(response.body, encoding='utf8'))
        ret_json = {}
        try:
            ret_json["old_price"] = price_json[0]["op"]
        except:
            pass
        ret_json["price"] = price_json[0]["p"]
        # 尝试获取是否有京东会员价格
        if "tpp" in price_json[0].keys():
            ret_json["vip"] = price_json[0]["tpp"]
        product['price'] = ret_json
        cumpon_url = 'https://cd.jd.com/promotion/v2?skuId=%s&area=19_1609_41655_0&cat=%s' % (
        product['sku'], product['sku_slave_typeid'])
        print(cumpon_url)
        if product['sku_slave_typeid']:
            # cumpon_url = 'https://cd.jd.com/promotion/v2?skuId=%s&area=19_1609_41655_0&cat=%s' % (product['sku'], product['sku_slave_typeid'])
            yield scrapy.Request(
                cumpon_url,
                meta={'product': product},
                callback=self.extract_product_coupon,
                dont_filter=True
            )
        else:
            item = JdItem()
            item['sku'] = product['sku']
            item['name'] = product['name']
            item['detail'] = product['detail']
            item['image'] = product['image']
            item['other_type'] = product['other_type']
            item['price'] = product['price']
            item['p_type'] = product['p_type']
            item['crawl_date'] = product['crawl_date']
            item['sku_slave_typeid'] = product['sku_slave_typeid']
            item['product_coupon'] = ''
            yield item

    def get_product_type(self, dom):
        p_type = []
        slave_list = dom.xpath('//*[@id="crumb-wrap"]/div/div[1]/div[@class="item"]/a/text()').extract()
        for i in slave_list:
            print(i)
            # p_type.append(i.xpath('//a/text()').extract_first())
            p_type.append(i)
        return p_type

    def get_other_size(self, dom):
        """
        獲取其他規格
        :param dom:
        :return:
        """
        try:
            regix = re.compile("colorSize:(.*}]?)")
            ret = regix.findall(dom)[0]
            return eval(ret)
        except Exception as e:
            return ret

    def get_image(self, dom):
        """
        获取商品的展示图
        :param dom:
        :return:
        """
        img_list = dom.xpath('//a[@id="spec-forward"]/following-sibling::div[1]/ul[@class="lh"]/li/img/@data-url').extract()
        img_list = ['http://img14.360buyimg.com/n0/' + i for i in img_list]
        # print(['https:' + i for i in img_list])
        return img_list

    def get_detail(self, dom):
        """
        获取商品的详情信息
        :param dom:
        :return:
        """
        # 详情标题
        key = dom.xpath('//div[@class="Ptable"]/div["@class=Ptable-item"]/dl/dl/dt/text()').extract()
        # 值列表
        value = dom.xpath('//div[@class="Ptable"]/div["@class=Ptable-item"]/dl/dl/dd/text()').extract()
        detail_list = []
        for i in range(len(key)):
            detail_list.append((key[i], re.sub('[\n\s]*', '', value[i])))
        package_dom = dom.xpath('//div[@class="Ptable"]/following-sibling::div[1]')
        package_title = package_dom[0].xpath('./h3/text()').extract()[0]
        package_value = package_dom[0].xpath('./p/text()').extract()[0]
        detail_list.append((package_title, package_value))
        # for i in detail_list:
        #     print(i)
        return detail_list

    def extract_banner(self, list_1, list_2=[]):
        """
        提取分类列表中的banner
        """
        list_1 = self.extract_str_to_dict(list_1)
        if list_2:
            list_2 = self.extract_str_to_dict(list_2)
        return list_1 + list_2

    def extract_str_to_dict(self, detail_list):
        """
        把字符串中的字符提取出来
        """
        ret_list = []
        for detail in detail_list:
            ret = self.extract_str(detail)
            ret_list.append({'name': ret[1], 'url': ret[0]})
        return ret_list

    def extract_str(self, detail):
        ret = re.split('\|', detail)
        ret = [i for i in ret if i]
        return ret[:2]

    def pretty_url(self, cat):
        """
        补全url地址
        :param cat:
        :return:
        """
        if cat[0].isdigit():
            cat = cat.replace('-', ',')
            return 'https://list.jd.com/list.html?cat=' + cat
        else:
            if '//' not in cat:
                cat = 'https://' + cat
            return cat

    def slave2(self, slave2_detail):
        """
        获取第三级类型
        """
        cate_list = []
        for cate in slave2_detail:
            cate_name = self.extract_str(cate['n'])
            cate_name = {'name': cate_name[1], 'url': self.pretty_url(cate_name[0])}
            cate_list.append(cate_name)
        if cate_list:
            return cate_list

    def slave1(self, slave_detail):
        """
        获取第二级类型
        """
        cate_list = []
        for cate in slave_detail:
            cate_name = self.extract_str(cate['n'])
            cate_name = {'name': cate_name[1], 'url': cate_name[0]}
            # print(cate_name['url'])
            cate_name['slave2'] = self.slave2(cate['s'])
            cate_list.append(cate_name)
        if cate_list:
            return cate_list

    def extract_type(self, content_list):
        """
        获取jd类型
        """
        data = []
        for content in content_list:
            cate_type = {}
            con_name = self.extract_str(content['n'])
            cate_type['top'] = {'name': con_name[1], 'url': con_name[0]}
            cate_type['slave1'] = self.slave1(content['s'])
            data.append(cate_type)
        return data

    def get_slave3(self, info_list=[]):
        """
        遍历出第三级的类型名称，路径
        :param info_list: 默认过去全部第三分类，如果传入指定的顶级类别名数组，会进行筛选
        :return:
        """
        ret_list = []
        for i in info_list:
            for k in i['type']:
                if k['slave1']:
                    for j in k['slave1']:
                        for f in j['slave2']:
                            ret_list.append(f)
        return ret_list

    def _get_url_id(self, url):
        """获取url中的商品id"""
        try:
            id = (re.findall(".*/(.*)\.html", url))[0]
            if id:
                return id
            return None
        except Exception:
            raise Exception("get_url_id() : re no find the url id")

    def _get_sku_slave_type(self, response_text):
        """獲取sku所屬類別id"""
        try:
            regix = re.compile('cat:\s*\[(.*)\]')
            ret = regix.findall(response_text)
            print(ret)
            return ret[0]
        except Exception:
            return ''
