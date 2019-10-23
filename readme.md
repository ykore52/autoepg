# autoepg について

実装途中 Work in progress

## Redis キー一覧

| Key Name | Type | Value | Description |
| --- | --- | --- | --- |
| `autoepg:program:{ch}:{timestamp}` | String | 番組情報の JSON データ | epgdump から抽出したもの |
| `autoepg:title:{ch}:{timestamp}:{title}` | String | 番組情報へのキー | 検索用キー:タイトル |
| `autoepg:detail:{ch}:{detail}` | String | 番組情報へのキー | 検索用キー:詳細 |
| `autoepg:category:large:{category}` | String | 番組情報へのキー | 検索用キー:カテゴリ(大分類) |
| `autoepg:category:middle:{category}` | String | 番組情報へのキー | 検索用キー:カテゴリ(小分類) |
| `autoepg:record:queue` | List | 録画キュー | |

### Redisキーの有効期限

放送終了時刻まで
