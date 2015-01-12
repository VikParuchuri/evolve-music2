# Scrapy settings for crawler project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/topics/settings.html
#
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

SPIDER_MODULES = ['crawler.spiders']
NEWSPIDER_MODULE = 'crawler.spiders'

CONCURRENT_REQUESTS_PER_DOMAIN=1
CONCURRENT_REQUESTS=1
BOT_NAME = "musicstats"

DEPTH_LIMIT = 2
DOWNLOAD_DELAY = 1

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'crawler (+http://www.yourdomain.com)'

ITEM_PIPELINES = {
    'scrapy.contrib.pipeline.files.FilesPipeline': 1,
    'crawler.pipelines.JsonWriterPipeline': 2
}

FILES_STORE = os.path.join(BASE_DIR, "data", "midi")
JSON_PATH = os.path.join(BASE_DIR, "data", "full.json")