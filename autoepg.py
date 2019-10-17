# -*- encoding: utf-8 -*-
'''
epgdump を実行して Redis に登録する
番組情報が変更されている場合は上書きする
'''

import os
import subprocess
import json
import redis
import slack

# EPG取得に使用する TS の一時保存先
TEMP_DIR = '/tmp'
TEMP_FILE = 'temp.ts'

REC_SECONDS = 10

CHANNEL_FILE = 'channels.json'

REDIS_SERVER = 'localhost'
REDIS_PORT = 6379

try:
    redis_client = redis.Redis(host=REDIS_SERVER, port=REDIS_PORT, db=0)
except:
    print('Cannot connect to the Redis service. host={}:{}'.format(REDIS_SERVER, REDIS_PORT))
    exit(1)

def get_epg_data(ch, name):
    '''
    チャンネル個別の EPG を TS を録画した上で取得
    '''

    print('{}(ch={}) の EPGデータを取得します。'.format(name, ch))

    try:
        subprocess.run(['recpt1', '--b25', '--strip', str(ch), str(REC_SECONDS), os.path.join(TEMP_DIR, TEMP_FILE)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = subprocess.run(['epgdump', 'json', os.path.join(TEMP_DIR, TEMP_FILE), '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        print('{}(ch={}) の EPGデータ取得完了。'.format(name, ch))
        return json.loads(res.stdout.decode('utf-8'))
        
    except Exception as exception:
        print('{}(ch={}) の EPGデータ取得でエラー発生。'.format(name, ch))
        print(exception)
        return None


def set_to_redis(epg_array, ch, name):
    '''
    EPG をシリアライズして Redis に保存する
    '''

    for epg in epg_array:
        for prog in epg.programs:
            try:
                if not 'start' in prog or not 'end' in prog:
                    raise Exception('EPG が不完全')

                prog_seliarized = json.dump(prog)
                pk = 'program:{}:{}'.format(ch, prog['start'][0:-3])

                redis_client.set(pk, prog_seliarized)

                # キーの有効期限を放送終了時間に設定
                redis_client.expireat(pk, int(prog['end'][0:-3]))

            except Exception as exception:
                pass


def autoepg():
    '''
    全チャンネルを録画して EPG を取得する.
    取得できなかったチャンネルは更新しない.
    '''

    with open(CHANNEL_FILE) as fp:
        channels = json.load(fp)
        for ch, name in channels.items():
            epg = get_epg_data(ch, name)
            if epg is None:
                continue
            
            set_to_redis(epg, ch, name)


if __name__ == "__main__":
    autoepg()
