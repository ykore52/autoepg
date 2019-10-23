# -*- encoding: utf-8 -*-
'''
epgdump を実行して Redis に登録する
番組情報が変更されている場合は上書きする
'''

import os
import subprocess
import json
import redis
import requests
import slack
import traceback

# EPG取得に使用する TS の一時保存先
TEMP_DIR = '/tmp'
TEMP_FILE = 'temp.ts'

REC_SECONDS = 10

CHANNEL_FILE = 'channels.json'

REDIS_SERVER = 'localhost'
REDIS_PORT = 6379

if 'SLACK_WEBHOOK_URL' in os.environ:
    SLACK_SUPPORT = True
    SLACK_WEBHOOK_URL = os.environ['SLACK_WEBHOOK_URL']
    print('Enable Slack support: DISABLED')
else:
    SLACK_SUPPORT = False
    SLACK_WEBHOOK_URL = ''
    print('Enable Slack support: ENABLED')

try:
    redis_client = redis.Redis(host=REDIS_SERVER, port=REDIS_PORT, db=0)
except:
    print('Cannot connect to the Redis service. host={}:{}'.format(REDIS_SERVER, REDIS_PORT))
    exit(1)

def slack_post(text):
    if SLACK_SUPPORT:
        requests.post(SLACK_WEBHOOK_URL, params={'text': text})
    else:
        print(text)


def get_epg_data(ch, name):
    '''
    チャンネル個別の EPG を TS を録画した上で取得
    '''

    print('{}(ch={}) の EPGデータを取得します。'.format(name, ch))

    try:
        cmd = 'recpt1 --b25 --strip {} {} {}'.format(ch, REC_SECONDS, os.path.join(TEMP_DIR, TEMP_FILE))
        res_recpt1 = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res_recpt1.returncode != 0:
            raise 'recpt1 の実行に失敗'

        cmd = 'epgdump json {} -'.format(os.path.join(TEMP_DIR, TEMP_FILE))
        res_epgdump = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res_epgdump != 0:
            raise 'epgdump の実行に失敗'

        cmd = 'rm -f {}'.format(os.path.join(TEMP_DIR, TEMP_FILE))
        res_rm = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if res_rm.returncode != 0:
            raise 'ファイル削除に失敗'

        print('{}(ch={}) の EPGデータ取得完了。'.format(name, ch))
        return json.loads(res_epgdump.stdout.decode('utf-8'))
        
    except Exception as exception:
        print('{}(ch={}) の EPGデータ取得でエラー発生。'.format(name, ch))
        print(exception)
        return None


def set_to_redis(epg_array, ch, name):
    '''
    EPG をシリアライズして Redis に保存する
    '''
    print('EPG データを Redis に保存')
    is_succeeded = True
    for epg in epg_array:
        for prog in epg['programs']:
            try:
                prog_serialized = json.dumps(prog)
                pk = 'autoepg:program:{}:{}'.format(ch, int(prog['start']/1000))
                redis_client.set(pk, prog_serialized)

                title_key = 'autoepg:title:{}:{}:{}'.format(ch, int(prog['start']/1000), prog['title'])
                redis_client.set(title_key, pk)

                detail_key = 'autoepg:detail:{}:{}'.format(ch, prog['detail'])
                redis_client.set(detail_key, pk)

                for cat in prog['category']:
                    category_large_key = 'autoepg:category:large:{}:{}:{}'.format(ch, int(prog['start']/1000), cat['large']['ja_JP'])
                    redis_client.set(category_large_key, pk)
                    category_middle_key = 'autoepg:category:middle:{}:{}:{}'.format(ch, int(prog['start']/1000), cat['middle']['ja_JP'])
                    redis_client.set(category_middle_key, pk)

                # キーの有効期限を放送終了時間に設定
                redis_client.expireat(pk, int(prog['end']/1000))
                redis_client.expireat(title_key, int(prog['end']/1000))
                redis_client.expireat(detail_key, int(prog['end']/1000))
                redis_client.expireat(category_large_key, int(prog['end']/1000))
                redis_client.expireat(category_middle_key, int(prog['end']/1000))

            except Exception as exception:
                print(exception)
                print(traceback.format_tb(e.__traceback__))
                is_succeeded = False
    return is_succeeded


def autoepg():
    '''
    全チャンネルを録画して EPG を取得する.
    取得できなかったチャンネルは更新しない.
    '''

    try:
        is_succeeded = True
        with open(CHANNEL_FILE) as fp:
            channels = json.load(fp)

        for ch, name in channels.items():
            epg = get_epg_data(ch, name)
            if epg is None:
                continue
                
            if not set_to_redis(epg, ch, name):
                is_succeeded = False
        
        if not is_succeeded:
            raise Exception

        slack_post('EPG の取得が完了しました。')
    except:
        slack_post('EPG の取得に失敗しました。')


if __name__ == "__main__":
    autoepg()
