# Press Release Feed API

プレスリリースなどのサイトURLを登録して、フィード形式で提供するAPIを提供するコンテナ

## 技術スタック

- Docker
- FastAPI
- Python
- SQLite

## エンドポイント

- GET /feed
  - 新着順でフィードを取得する
  - `curl http://localhost:9000/feed`
- POST /feed
  - 新しいサイトを登録する
  - パラメータ(JSON): `{"url": "登録したいサイトのURL"}`
  - `curl -X POST -H "Content-Type: application/json" -d '{"url": "https://example.com"}' http://localhost:9000/feed`
- DELETE /feed/{feed_id}
  - 指定されたフィードIDのフィードを削除する
  - `curl -X DELETE http://localhost:9000/feed/1`

## フォルダ構成

- app/
  - main.py
  - database.py
  - models.py
  - schemas.py
  - services.py
  - utils.py
- data/
  - feeds.db
- requirements.txt
- Dockerfile
- compose.yml

## 実行方法

```bash
podman compose up --build -d
```

## 停止方法

```bash
podman compose down
```

## データベース

