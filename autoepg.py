# -*- encoding: utf-8 -*-

#
# epgdump を実行して Redis に登録する
# 番組情報が変更されている場合は上書きする
#

import os
import subprocess
import json
import redis

# EPG取得に使用する TS の一時保存先
TEMP_DIR = '/tmp'
TEMP_FILE = 'temp.ts'

REC_SECONDS = 10

CHANNEL_FILE = 'channels.json'

REDIS_SERVER = 'localhost'
REDIS_PORT = 6379

r = redis.Redis(host=REDIS_SERVER, port=REDIS_PORT, db=0)

def get_epg_data(ch, name):

    print('{}(ch={}) の EPGデータを取得します。'.format(name, ch))

    try:
        subprocess.run(['recpt1', '--b25', '--strip', str(ch), str(REC_SECONDS), os.path.join(TEMP_DIR, TEMP_FILE)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        res = subprocess.run(['epgdump', 'json', os.path.join(TEMP_DIR, TEMP_FILE), '-'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        print('{}(ch={}) の EPGデータ取得完了。'.format(name, ch))
        return res.stdout.decode('utf-8')
    except Exception as e:
        print('{}(ch={}) の EPGデータ取得でエラー発生。'.format(name, ch))
        print(e)


    

def save_epg():
    '''
    全チャンネルを録画して EPG を取得する.
    取得できなかったチャンネルは更新しない.
    '''

    with open(CHANNEL_FILE) as fp:
        channels = json.load(fp)
        for ch, name in channels.items():
            get_epg_data(ch, name)


def main():
    save_epg()

if __name__ == "__main__":
    main()