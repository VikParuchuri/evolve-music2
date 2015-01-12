from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from crawler.items import MIDIFile
import re
import os
import requests

import logging
log = logging.getLogger(__name__)

class MWSpider(BaseSpider):
    name = "mws"
    ltype = "classical"
    allowed_domains = ["www.midiworld.com","midiworld.com"]
    start_urls = ["http://www.midiworld.com/classic.htm"]

    def parse(self, response):
        x = HtmlXPathSelector(response)
        links = []
        url = response.url
        music_links = x.select('//ul/li/a/@href').extract()
        music_links = [m for m in music_links if m.endswith(".mid")]
        for l in music_links:
            link = MIDIFile()
            link['url'] = url
            link['ltype'] = self.ltype
            link['link'] = l
            link["file_urls"] = [l]
            links.append(link)
        return links

class MASpider(BaseSpider):
    name = "mas"
    ltype = "modern"
    allowed_domains = ["midi-archive.com","www.midi-archive.com"]
    start_urls = ["http://midi-archive.com/"]

    def parse(self, response):
        x = HtmlXPathSelector(response)
        links = []
        url = response.url
        music_links = x.select("//td/a/@href").extract()
        music_links = [m for m in music_links if m.endswith(".mid")]
        for l in music_links:
            link = MIDIFile()
            link['url'] =  url
            link['ltype'] = self.ltype
            link['link'] = "http://midi-archive.com/" + l
            link["file_urls"] = [link['link']]
            links.append(link)
        return links
