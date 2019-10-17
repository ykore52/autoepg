# -*- encoding: utf-8 -*-

import os
import subprocess
import json
import redis
import requests
import datetime

from errbot import BotPlugin, botcmd, arg_botcmd

REDIS_SERVER = 'localhost'
REDIS_PORT = 6379

REC_DIR = '/tmp'

def get_redis():
    try:
        return redis.Redis(host=REDIS_SERVER, port=REDIS_PORT, db=0, decode_responses=True)
    except:
        raise Exception('Cannot connect to the Redis service. host={}:{}'.format(REDIS_SERVER, REDIS_PORT))

redis_client = get_redis()

class Recbot(BotPlugin):
    '''
    Errbot 経由でPT2録画管理するためのプラグインです.
    '''

    def usage(self):
        return '''
        機能:
        * 番組情報の検索
                !search 鉄腕ＤＡＳＨ         (基本)
                !search /title 鉄腕ＤＡＳＨ
                !search /detail 鉄腕ＤＡＳＨ
                !search /category バラエティ
        * 録画キューの表示
                !recq show
        * 録画キューの登録
                !recq add 鉄腕ＤＡＳＨ
                !recq add 23 2019/10/17 1:00 [1:30]
                !recq add /title 鉄腕ＤＡＳＨ
                !recq add /category バラエティ
        * 録画キューの自動録画登録
                !recq autoadd 鉄腕ＤＡＳＨ
        * 録画キューの削除
                !recq del 1
        '''

    @botcmd
    def search(self, msg, args):
        args = args.split(' ')
        if len(args) == 0:

            return self.usage()

        elif len(args) == 1:

            keys_title = redis_client.keys('autoepg:title:*{}*'.format(args[0]))
            keys_detail = redis_client.keys('autoepg:detail:*{}*'.format(args[0]))
            keys = set(keys_title)
            keys |= set(keys_detail)
            ret = '検索結果: {} 件ヒットしました.\n'.format(len(keys))
            for i, key in enumerate(keys):
                if i > 0:
                    ret += '------\n'
                r = json.loads(redis_client.get(redis_client.get(key)))
                dts = datetime.datetime.fromtimestamp(int(r['start']/1000))
                dte = datetime.datetime.fromtimestamp(int(r['end']/1000))

                ret += '放送日時: {} ～ {}\n'.format(dts.strftime('%m-%d %H:%M'), dte.strftime('%m-%d %H:%M'))
                ret += 'タイトル: {}\n'.format(r['title'])
                ret += '説明: {}\n'.format(r['detail'])
            return ret

        elif len(args) >= 2:

            if args[1] == '/title':
            
                keys = redis_client.keys('autoepg:title:*{}*'.format(args[0]))

                ret = '検索結果: {} 件ヒットしました.\n'.format(len(keys))
                for i, key in enumerate(keys):
                    if i > 0:
                        ret += '------\n'
                    r = json.loads(redis_client.get(redis_client.get(key)))
                    dts = datetime.datetime.fromtimestamp(int(r['start']/1000))
                    dte = datetime.datetime.fromtimestamp(int(r['end']/1000))

                    ret += '放送日時: {} ～ {}\n'.format(dts.strftime('%m-%d %H:%M'), dte.strftime('%m-%d %H:%M'))
                    ret += 'タイトル: {}\n'.format(r['title'])
                    ret += '説明: {}\n'.format(r['detail'])
                return ret

            elif args[1] == '/detail':

                keys = redis_client.keys('autoepg:detail:*{}*'.format(args[0]))

                ret = '検索結果: {} 件ヒットしました.\n'.format(len(keys))
                for i, key in enumerate(keys):
                    if i > 0:
                        ret += '------\n'
                    r = json.loads(redis_client.get(redis_client.get(key)))
                    dts = datetime.datetime.fromtimestamp(int(r['start']/1000))
                    dte = datetime.datetime.fromtimestamp(int(r['end']/1000))

                    ret += '放送日時: {} ～ {}\n'.format(dts.strftime('%m-%d %H:%M'), dte.strftime('%m-%d %H:%M'))
                    ret += 'タイトル: {}\n'.format(r['title'])
                    ret += '説明: {}\n'.format(r['detail'])
                return ret

            elif args[1] == '/category':

                keys = redis_client.keys('autoepg:category:*{}*'.format(args[0]))
                
                ret = '検索結果: {} 件ヒットしました.\n'.format(len(keys))
                for i, key in enumerate(keys):
                    if i > 0:
                        ret += '------\n'
                    r = json.loads(redis_client.get(redis_client.get(key)))
                    dts = datetime.datetime.fromtimestamp(int(r['start']/1000))
                    dte = datetime.datetime.fromtimestamp(int(r['end']/1000))

                    ret += '放送日時: {} ～ {}\n'.format(dts.strftime('%m-%d %H:%M'), dte.strftime('%m-%d %H:%M'))
                    ret += 'タイトル: {}\n'.format(r['title'])
                    ret += '説明: {}\n'.format(r['detail'])
                return ret

            else:
                return self.usage()

        return self.usage()

    @botcmd
    def recq(self, msg, args):
        if len(args) == 0:
            return self.usage()
        elif len(args) == 1:
            if args[0] == 'show':
                return self._recq_show(msg, args)
        elif len(args) == 2:
            if args[0] == 'add':
                return self._recq_add(msg, args)
        return self.usage()
    
    def _recq_show(self, msg, args):
        queue = redis_client.keys('autoepg:record'.format(args[0]))
        return ''.join(queue)

    def _recq_add(self, msg, args):
        try:
            timestamp = datetime.datetime.strptime
            key = redis_client.get()
            dt = datetime.datetime.strptime(args[1], '%Y/%m/%d %H:%M')
            ch = 0
            duration = 0
            subprocess.run(
                ['at',
                 '{0:2d}:{0:2d}'.format(dt.hour(), dt.minute()),
                 '{0:2d}{0:2d}{0:4d}'.format(dt.day(), dt.month(), dt.year()),
                 'recpt1', '--b25', '--strip', str(ch), str(duration),
                 os.path.join(REC_DIR, '')
                ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

            return '録画予約しました.'
        except:
            return '日付形式が不正です. : {}'.format(args[1])
