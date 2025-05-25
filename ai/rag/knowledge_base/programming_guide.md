# プログラミング支援ガイド

## Python開発

### 基本的なPython開発パターン

```python
# クラス定義の基本
class DataProcessor:
    def __init__(self, config):
        self.config = config
        
    async def process(self, data):
        # 非同期処理の実装
        processed = await self._transform_data(data)
        return processed
        
    async def _transform_data(self, data):
        # データ変換ロジック
        return data.strip().lower()
```

### エラーハンドリング

```python
try:
    result = await process_data(input_data)
except ValueError as e:
    logger.error(f"Invalid data: {e}")
    return {"error": "データが不正です"}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"error": "予期しないエラーが発生しました"}
```

### 非同期プログラミング

- `async`/`await`を使用した非同期処理
- `aiohttp`でのHTTPクライアント実装
- `asyncio`でのタスク管理

## Web開発

### RESTful API設計

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class CreateRequest(BaseModel):
    name: str
    data: dict

@app.post("/api/items")
async def create_item(request: CreateRequest):
    try:
        item = await service.create_item(request.name, request.data)
        return {"id": item.id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### フロントエンド（React/TypeScript）

```typescript
interface ApiResponse<T> {
  data: T;
  status: string;
  error?: string;
}

const useApiCall = <T>(url: string) => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch(url);
        const result: ApiResponse<T> = await response.json();
        setData(result.data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchData();
  }, [url]);
  
  return { data, loading, error };
};
```

## データベース操作

### SQLAlchemy (ORM)

```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### クエリの実装

```python
async def get_user_by_email(session: AsyncSession, email: str) -> Optional[User]:
    result = await session.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()
```

## テスト駆動開発

### Pytestを使用したテスト

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_data_processing():
    # Arrange
    mock_service = AsyncMock()
    mock_service.process.return_value = "processed_data"
    
    # Act
    result = await mock_service.process("input_data")
    
    # Assert
    assert result == "processed_data"
    mock_service.process.assert_called_once_with("input_data")
```

### モックとテストダブル

```python
@patch('module.external_service')
async def test_with_external_dependency(mock_service):
    mock_service.call_api.return_value = {"status": "success"}
    
    result = await function_under_test()
    
    assert result["status"] == "success"
```

## パフォーマンス最適化

### 非同期処理の最適化

```python
import asyncio

async def batch_process(items: List[str]) -> List[str]:
    # 並列処理でパフォーマンス向上
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # エラーハンドリング
    processed_results = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Processing failed: {result}")
        else:
            processed_results.append(result)
    
    return processed_results
```

### キャッシュ戦略

```python
from functools import lru_cache
import asyncio

class CacheService:
    def __init__(self):
        self._cache = {}
        self._lock = asyncio.Lock()
    
    async def get_or_compute(self, key: str, compute_func):
        async with self._lock:
            if key in self._cache:
                return self._cache[key]
            
            result = await compute_func()
            self._cache[key] = result
            return result
```
