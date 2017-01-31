﻿# -*- coding: utf-8 -*-

import base64
import cStringIO
import json
import re

import redis
import requests

import CQImgReader
from BaseProcessModule import *
from RedisSession import redisPool
from Sender import *

redisConnection = redis.Redis(connection_pool=redisPool)


class RateAppearanceModule(BaseProcessModule):
    CONTEXT = "RATE"
    COOLQ_IMAGE_PATH = u"C:\\Users\Administrator\\Desktop\\{0}\\酷Q Pro\\data\\image\\"
    PICTURE_PATTERN = r"\[CQ:image,file=(.+)\]"
    UPLOAD_URL = "http://kan.msxiaobing.com/Api/Image/UploadBase64"
    RANK_URL = "http://kan.msxiaobing.com/Api/ImageAnalyze/Process?service=yanzhi"
    _RANK_URL = "http://kan.msxiaobing.com/Api/ImageAnalyze/Process?service=yanzhi&tid=4a3de9b27e5b4624b35a941669fdc57c"

    name = "UploadImageModule"

    @staticmethod
    def is_rate_appearance(message):
        if message.getContent().find(u"测颜值") == 0:
            return True
        else:
            return False

    @staticmethod
    def is_picture(message):
        if re.search(RateAppearanceModule.PICTURE_PATTERN, message.getContent()):
            return True
        else:
            return False

    @staticmethod
    def rate(url):
        pass

    @staticmethod
    def process(message):
        print "[" + RateAppearanceModule.name + "]"
        try:
            context = redisConnection.hget(REDIS_CONTEXT_CACHE_HASH_NAME, message.getPersonQQ())
            if message.getSubType() == 1 and RateAppearanceModule.is_rate_appearance(message):
                redisConnection.hset(REDIS_CONTEXT_CACHE_HASH_NAME, message.getPersonQQ(), RateAppearanceModule.CONTEXT)
                message.setContent(u"测颜值是吧，直接发图片給微微好啦~")
                send(message, True)
            elif message.getSubType() == 1 and RateAppearanceModule.is_picture(
                    message) and context == RateAppearanceModule.CONTEXT:
                name = re.search(RateAppearanceModule.PICTURE_PATTERN, message.getContent()).group(1)
                print name
                print RateAppearanceModule.COOLQ_IMAGE_PATH.format(message.getTargetQQ()) + name + ".cqimg"
                buffer = cStringIO.StringIO()
                CQImgReader.CQImgReader(
                    RateAppearanceModule.COOLQ_IMAGE_PATH.format(
                        message.getTargetQQ()) + name + ".cqimg").get_pil_img().save(
                    buffer, format="JPEG")
                response = requests.post(RateAppearanceModule.UPLOAD_URL, base64.b64encode(buffer.getvalue()))
                args = json.loads(response.text)
                response = requests.post(RateAppearanceModule._RANK_URL,
                                         {"Content[imageUrl]": args["Host"] + args["Url"]})
                args = json.loads(response.text)
                redisConnection.hdel(REDIS_CONTEXT_CACHE_HASH_NAME, message.getPersonQQ())
                print args
                message.setContent(args["content"]["text"])
                send(message, True)
            else:
                return
        except Exception as e:
            if isinstance(e,Block):
                raise Block()
            traceback.print_exc()
            return

    # def upload(self):
    #     buffer = cStringIO.StringIO()
    #     self.image.save(buffer, format="JPEG")
    #     img_str = base64.b64encode(buffer.getvalue())
    #     response = requests.post(RateAppearanceModule.UPLOAD_URL, img_str)
    #     response_args = json.loads(response.text)
    #     self.args = response_args["Host"] + response_args["Url"]
    #     print self.args
    #     return self
    #
    # def rank(self):
    #     # req = {u"MsgId": str(int(time.time())).decode("utf-8") + u"063", u"CreateTime": int(time.time()),
    #     #       u"Content%5BimageUrl%5D": self.args.decode("utf-8")}
    #     req = {"Content[imageUrl]": self.args}
    #     res = requests.post(RateAppearanceModule._RANK_URL, req)
    #     print res.text


if __name__ == "__main__":
    res = requests.post(RateAppearanceModule._RANK_URL, {
        "Content[imageUrl]": "https://ss2.baidu.com/6ONYsjip0QIZ8tyhnq/it/u=2955981818,1202135661&fm=58"})
    print res.text