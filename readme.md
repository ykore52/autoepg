# autoepg について

## Redis キー一覧

| Key Name | Value | Type | Description |
| --- | --- | --- | --- |
| autoepg:program:{ch}:{timestamp} | String | epgdump から抽出した番組情報の JSON データ | |
| autoepg:title:{ch}:{timestamp}:{title} | String | 番組情報 | 検索用キー:タイトル |
| autoepg:detail:{ch}:{detail} | String | 番組情報 | 検索用キー:詳細 |
| autoepg:category:large:{category} | String | 番組情報 | 検索用キー:カテゴリ(大分類) |
| autoepg:category:middle:{category} | String | 番組情報 | 検索用キー:カテゴリ(小分類) |
| autoepg:record:queue | List | 録画キュー | |

### Redisキーの有効期限

放送終了時刻まで
