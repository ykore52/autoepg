# -*- encoding: utf-8 -*-

import os
import subprocess
import json
import redis
import requests
import datetime
import re

from errbot import BotPlugin, botcmd, arg_botcmd

CHANNEL_FILE = 'channels.json'

REDIS_SERVER = 'localhost'
REDIS_PORT = 6379

REC_DIR = '/tmp'

PYTHON_CMD = '/usr/bin/python3'
AUTOEPG_PATH = '/home/ykore52/autoepg/autoepg.py'

# 放送開始時間の N秒前に録画を開始する
REC_START_OFFSET_SEC = 15

# 放送終了時間の N秒前に録画を終了する
REC_END_OFFSET_SEC = 30

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
        channels = {}
        with open(CHANNEL_FILE) as fp:
            channels = json.load(fp)

        return '''
        機能:
        * 番組情報の検索
            !recbot search 鉄腕ＤＡＳＨ         (基本)
            !recbot search /title 鉄腕ＤＡＳＨ
            !recbot search /detail 鉄腕ＤＡＳＨ
            !recbot search /category バラエティ
        * 録画キューの表示
            !recbot show
        * 録画キューの登録
            * 開始時間のみが指定された場合は、番組表に番組が存在した場合のみキュー登録
            * 年指定は省略可(次年1月も省略OK)
            !recbot add 23 [2019/]10/17 1:00 [60]
        * 録画キューの削除
            !recbot delete 1
        * EPG データの更新
            !recbot update
        * 録画キューの自動録画登録(未実装)
            !recbot autoadd 鉄腕ＤＡＳＨ
            !recbot autoadd /title 鉄腕ＤＡＳＨ
            !recbot autoadd /category バラエティ
        * 放送局コード表
                {}
        '''.format(json.dump(channels))
    
    def recbot_search_response(self, keys):
        '''
        Errbot が返す文面を作成する
        '''
        ret = '検索結果: {} 件ヒットしました.\n'.format(len(keys))
        for i, key in enumerate(keys):
            if i > 0:
                ret += '---\n'
            prog = json.loads(redis_client.get(key))
            dts = datetime.datetime.fromtimestamp(int(prog['start']/1000))
            dte = datetime.datetime.fromtimestamp(int(prog['end']/1000))

            ret += '{} - {}\n'.format(dts.strftime('%m/%d %H:%M'), dte.strftime('%H:%M'))
            ret += '{}\n'.format(prog['title'])
            ret += '{}\n'.format(prog['detail'])
        return ret
    
    def recbot_delete_response(self):
        return subprocess.run('at -l', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).stdout

    @botcmd
    def recbot_search(self, msg, args):
        args = args.split(' ')
        if len(args) == 0:

            return self.usage()

        elif len(args) == 1:

            keys = set()
            for key in redis_client.keys('autoepg:title:*{}*'.format(args[0])):
                keys.add(redis_client.get(key))
            for key in redis_client.keys('autoepg:detail:*{}*'.format(args[0])):
                keys.add(redis_client.get(key))
            
            return self.recbot_search_response(keys)

        elif len(args) >= 2:

            if args[1] == '/title':

                keys = set()
                for key in redis_client.keys('autoepg:title:*{}*'.format(args[0])):
                    keys.add(redis_client.get(key))

                return self.recbot_search_response(keys)

            elif args[1] == '/detail':

                keys = set()
                for key in redis_client.keys('autoepg:detail:*{}*'.format(args[0])):
                    keys.add(redis_client.get(key))

                return self.recbot_search_response(keys)

            elif args[1] == '/category':

                keys = set()
                for key in redis_client.keys('autoepg:category:*{}*'.format(args[0])):
                    keys.add(redis_client.get(key))

                return self.recbot_search_response(keys)

            else:
                return self.usage()

        return self.usage()
    
    @botcmd
    def recbot_searc(self, msg, args):
        return self.recbot_search(msg, args)

    @botcmd
    def recbot_sear(self, msg, args):
        return self.recbot_search(msg, args)

    @botcmd
    def recbot_sea(self, msg, args):
        return self.recbot_search(msg, args)

    @botcmd
    def recbot_se(self, msg, args):
        return self.recbot_search(msg, args)
    
    
    @botcmd 
    def recbot_show(self, msg, args):
        args = args.split(' ')

        ret = '録画キューを表示します.\n'
        qkeys = redis_client.lrange('autoepg:record:queue', 0, -1)
        for i, key in enumerate(qkeys):
            prog = redis_client.get(key)
            dts = datetime.datetime.fromtimestamp(int(prog['start']/1000))
            dte = datetime.datetime.fromtimestamp(int(prog['end']/1000))

            ret += '{}) {}-{}: {}\n'.format(
                i, dts.strftime('%m/%d %H:%M'), dts.strftime('%H:%M'), prog['title']
            )
        return ret
    
    @botcmd
    def recbot_sho(self, msg, args):
        return self.recbot_show(msg, args)
    
    @botcmd
    def recbot_sh(self, msg, args):
        return self.recbot_show(msg, args)
    
    
    @botcmd
    def recbot_delete(self, msg, args):
        args = args.split(' ')
        if len(args) == 0:
            return self.recbot_delete_response()
        elif len(args) == 1:
            try:
                cmd = 'atrm {}'.format(args[0])
                ret = subprocess.run('atrm {}'.format(args[0]), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if ret.returncode != 0:
                    return 'コマンド実行に失敗しました. {}'.format(cmd)
                return '録画キューを削除しました.'
            except Exception as e:
                return e

    @botcmd
    def recbot_delet(self, msg, args):
        return self.recbot_delete(msg, args)
    
    @botcmd
    def recbot_dele(self, msg, args):
        return self.recbot_delete(msg, args)
        
    @botcmd
    def recbot_del(self, msg, args):
        return self.recbot_delete(msg, args)
    
    @botcmd
    def recbot_de(self, msg, args):
        return self.recbot_delete(msg, args)


    @botcmd
    def recbot_add(self, msg, args):
        if not self._check_storage_at_least_one():
            return '保存先ストレージを少なくとも1つ追加してください.'

        args = args.split(' ')
        try:
            if len(args) != 3 and len(args) != 4:
                return self.usage()

            # validation

            if not re.match('[0-9]+', args[0]):
                return 'チャンネル番号が不正です: {}'.format(args[0])
            ch = int(args[0])

            if re.match('[0-9]+\/[0-9]+\/[0-9]', args[1]):
                pdate = datetime.datetime.strptime(args[1], '%Y/%m/%d')
            elif re.match('[0-9]+\/[0-9]', args[1]):
                pdate = datetime.datetime.strptime(args[1], '%m/%d')

                # 来年1月以降の番組予約のときに,いちいち来年の年を入力する必要をなくす
                year = datetime.datetime.now().year
                if datetime.datetime.now().month >= 9 and pdate.month <= 6:
                    year += 1
                
                pdate = datetime.datetime(year, pdate.month, pdate.day)
            else:
                return '日付形式の指定が不正です: {}'.format(args[1])
            
            if re.match('[0-9]+:[0-9]+', args[2]):
                ptime = datetime.datetime.strptime(args[2], '%H:%M')
                pdate += datetime.timedelta(hours=ptime.hour, minutes=ptime.minute)
            else:
                return '時間形式の指定が不正です: {}'.format(args[2])

            if len(args) == 4 and not re.match('[0-9]+', args[3]):
                return '録画時間の指定が不正です: {}'.format(args[3])


            if len(args) == 3:
                # EPGを検索し duration を得る
                prog = redis_client.get('autoepg:program:{}:{}'.format(ch, dt.timestamp()))
                if prog is None:
                    return 'EPGから番組を見つけられませんでした.'
                duration = prog['duration']
            elif len(args) == 4:
                duration = int(args[3])


            # 録画開始時間の調整
            if REC_START_OFFSET_SEC >= 0:
                dt = dt + datetime.timedelta(minutes=-int(REC_START_OFFSET_SEC/60)+1)
                sleep_sec = 60 - REC_START_OFFSET_SEC
            else:
                dt = dt + datetime.timedelta(minutes=int(REC_START_OFFSET_SEC/60))
                sleep_sec = REC_START_OFFSET_SEC


            rec_dir = self._select_storage()
            if rec_dir is None:
                return '選択できるストレージがありません.'
            ts_fullpath = os.path.join(rec_dir, 'record-{}-{}.ts'.format(dt.strftime('%Y%m%d%H%M'), str(ch)))

            cmd = 'echo "sleep {}; recpt1 --b25 --strip {} {} {}" | at {0:2d}:{0:2d} {0:2d}{0:2d}{0:4d}'.format(sleep_sec, str(ch), str(duration - REC_END_OFFSET_SEC), ts_fullpath, dt.hour(), dt.minute(), dt.day(), dt.month(), dt.year())
            ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if ret.returncode != 0:
                return 'コマンド実行に失敗しました. {}'.format(cmd)

            if re.search('^job ([0-9]+) at .*?', ret.stdout, re.MULTILINE) is None:
                raise 'at コマンドの実行に失敗'
            
            return '録画予約しました.\n{}'.format(subprocess.run('at -l', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT))

        except Exception as e:
            return e

    @botcmd
    def recbot_update(self, msg, args):
        cmd = 'echo "{} {}" | at now'.format(PYTHON_CMD, AUTOEPG_PATH)
        ret = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if ret.returncode != 0:
            return 'コマンド実行に失敗しました. {}'.format(cmd)
        return 'EPG データ即時更新を予約しました: {}'.format(cmd)
    
    @botcmd
    def recbot_updat(self, msg, args):
        return self.recbot_update(msg, args)
    
    @botcmd
    def recbot_upda(self, msg, args):
        return self.recbot_update(msg, args)
    
    @botcmd
    def recbot_upd(self, msg, args):
        return self.recbot_update(msg, args)
    
    @botcmd
    def recbot_up(self, msg, args):
        return self.recbot_update(msg, args)
    

    @botcmd
    def recbot_storage(self, msg, args):
        args = args.split(' ')
        if len(args) == 0:
            ls = redis_client.lrange('autoepg:storage', 0, -1)
            response = 'TS 保存先を表示します.\n'
            for i, path in enumerate(ls):
                response += '{}. {}\n'.format(i+1, path)
            return response
        elif len(args) >= 2:
            if args[1] == 'add':
                return self.recbot_storage_add(msg, args[1:])
        return self.usage()

    @botcmd
    def recbot_storag(self, msg, args):
        return self.recbot_storage(msg, args)

    @botcmd
    def recbot_stora(self, msg, args):
        return self.recbot_storage(msg, args)

    @botcmd
    def recbot_stor(self, msg, args):
        return self.recbot_storage(msg, args)

    @botcmd
    def recbot_sto(self, msg, args):
        return self.recbot_storage(msg, args)

    @botcmd
    def recbot_st(self, msg, args):
        return self.recbot_storage(msg, args)


    def recbot_storage_add(self, msg, args):
        if len(args) != 1:
            return 'パラメータが不正です.'
        try:
            redis_client.rpush(os.path.normpath(args[1]))
            return '保存先一覧へ追加しました.'
        except:
            return 'Redis への書き込みに失敗.'
    

    def _check_storage_at_least_one(self):
        try:
            ls = redis_client.lrange('autoepg:storage', 0, -1)
            if len(ls) == 0:
                return False
            return True
        except:
            return False
    
    def _check_storage_capacity(self, path):
        try:
            import shutil
            if shutil.disk_usage(path).used / shutil.disk_usage(path).total >= 0.95: # disk limit の数値は適当
                return False
            return True
        except:
            return False

    def _select_storage(self):
        ls = redis_client.lrange('autoepg:storage', 0, -1)
        for path in ls:
            if not self._check_storage_capacity(path):
                continue
            return path
        return None
