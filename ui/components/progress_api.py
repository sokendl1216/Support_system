"""
進行状態通知システム - APIエンドポイント

バックエンドとの通信用APIエンドポイントを提供します。
"""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uuid
import time

from ai.process_monitor import get_process_monitor, ProcessStatus as BackendProcessStatus
from ui.components.progress_notification import (
    get_progress_system, 
    ProgressStatus,
    NotificationType
)

logger = logging.getLogger(__name__)

# データモデル
class ProcessStartRequest(BaseModel):
    title: str = Field(..., description="処理タイトル")
    description: str = Field(..., description="処理説明")
    total_steps: int = Field(default=100, description="総ステップ数")
    category: Optional[str] = Field(None, description="処理カテゴリ")

class ProgressUpdateRequest(BaseModel):
    progress: float = Field(..., ge=0.0, le=1.0, description="進捗（0.0-1.0）")
    current_step: str = Field(..., description="現在のステップ説明")
    step_number: Optional[int] = Field(None, description="ステップ番号")
    metadata: Optional[Dict[str, Any]] = Field(None, description="追加メタデータ")

class ProcessCompleteRequest(BaseModel):
    final_message: str = Field(default="完了しました", description="完了メッセージ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="完了時メタデータ")

class ProcessErrorRequest(BaseModel):
    error_message: str = Field(..., description="エラーメッセージ")
    metadata: Optional[Dict[str, Any]] = Field(None, description="エラー時メタデータ")

class NotificationRequest(BaseModel):
    type: str = Field(..., description="通知タイプ（info/success/warning/error）")
    title: str = Field(..., description="通知タイトル")
    message: str = Field(..., description="通知メッセージ")
    auto_dismiss: bool = Field(default=True, description="自動削除フラグ")

# WebSocket接続管理
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket接続: 総接続数 {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket切断: 総接続数 {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        # 切断されたコネクションを削除
        for connection in disconnected:
            self.disconnect(connection)

# グローバルマネージャー
manager = ConnectionManager()

def create_progress_api(app: FastAPI):
    """FastAPIアプリに進行状態通知APIを追加"""
    
    @app.post("/api/progress/start")
    async def start_process(request: ProcessStartRequest):
        """プロセス開始"""
        try:
            process_id = str(uuid.uuid4())
            progress_system = get_progress_system()
            
            # UIプログレスシステムでプロセス開始
            progress_info = progress_system.start_process(
                process_id=process_id,
                title=request.title,
                description=request.description,
                total_steps=request.total_steps
            )
            
            # バックエンド監視システムでも登録
            backend_monitor = await get_process_monitor()
            await backend_monitor.register_process(
                process_id=process_id,
                process_type=request.category or "general",
                description=request.description,
                metadata={"title": request.title, "total_steps": request.total_steps}
            )
            
            # WebSocket通知
            await manager.broadcast(json.dumps({
                "type": "process_started",
                "process_id": process_id,
                "title": request.title,
                "description": request.description
            }))
            
            return {
                "success": True,
                "process_id": process_id,
                "message": "プロセスが開始されました"
            }
            
        except Exception as e:
            logger.error(f"プロセス開始エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/progress/{process_id}/update")
    async def update_process_progress(process_id: str, request: ProgressUpdateRequest):
        """進捗更新"""
        try:
            progress_system = get_progress_system()
            
            # UIプログレスシステム更新
            success = progress_system.update_progress(
                process_id=process_id,
                progress=request.progress,
                current_step=request.current_step,
                step_number=request.step_number,
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="プロセスが見つかりません")
            
            # バックエンド監視システム更新
            backend_monitor = await get_process_monitor()
            await backend_monitor.update_progress(
                process_id=process_id,
                progress=request.progress,
                metadata_update=request.metadata or {}
            )
            
            # WebSocket通知
            await manager.broadcast(json.dumps({
                "type": "progress_updated",
                "process_id": process_id,
                "progress": request.progress,
                "current_step": request.current_step,
                "step_number": request.step_number
            }))
            
            return {
                "success": True,
                "message": "進捗が更新されました"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"進捗更新エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/progress/{process_id}/complete")
    async def complete_process(process_id: str, request: ProcessCompleteRequest):
        """プロセス完了"""
        try:
            progress_system = get_progress_system()
            
            # UIプログレスシステム完了
            success = progress_system.complete_process(
                process_id=process_id,
                final_message=request.final_message,
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="プロセスが見つかりません")
            
            # バックエンド監視システム完了
            backend_monitor = await get_process_monitor()
            await backend_monitor.complete_process(
                process_id=process_id,
                metadata_update=request.metadata or {}
            )
            
            # WebSocket通知
            await manager.broadcast(json.dumps({
                "type": "process_completed",
                "process_id": process_id,
                "final_message": request.final_message
            }))
            
            return {
                "success": True,
                "message": "プロセスが完了しました"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"プロセス完了エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.put("/api/progress/{process_id}/error")
    async def error_process(process_id: str, request: ProcessErrorRequest):
        """プロセスエラー"""
        try:
            progress_system = get_progress_system()
            
            # UIプログレスシステムエラー
            success = progress_system.fail_process(
                process_id=process_id,
                error_message=request.error_message,
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(status_code=404, detail="プロセスが見つかりません")
            
            # バックエンド監視システムエラー
            backend_monitor = await get_process_monitor()
            await backend_monitor.fail_process(
                process_id=process_id,
                error_message=request.error_message,
                metadata_update=request.metadata or {}
            )
            
            # WebSocket通知
            await manager.broadcast(json.dumps({
                "type": "process_error",
                "process_id": process_id,
                "error_message": request.error_message
            }))
            
            return {
                "success": True,
                "message": "プロセスエラーが記録されました"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"プロセスエラー記録エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.delete("/api/progress/{process_id}")
    async def cancel_process(process_id: str):
        """プロセスキャンセル"""
        try:
            progress_system = get_progress_system()
            
            # UIプログレスシステムキャンセル
            success = progress_system.cancel_process(process_id)
            
            if not success:
                raise HTTPException(status_code=404, detail="プロセスが見つかりません")
            
            # バックエンド監視システムキャンセル
            backend_monitor = await get_process_monitor()
            await backend_monitor.cancel_process(process_id)
            
            # WebSocket通知
            await manager.broadcast(json.dumps({
                "type": "process_cancelled",
                "process_id": process_id
            }))
            
            return {
                "success": True,
                "message": "プロセスがキャンセルされました"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"プロセスキャンセルエラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/progress/{process_id}")
    async def get_process_info(process_id: str):
        """プロセス情報取得"""
        try:
            progress_system = get_progress_system()
            process_info = progress_system.get_process_info(process_id)
            
            if not process_info:
                raise HTTPException(status_code=404, detail="プロセスが見つかりません")
            
            return {
                "success": True,
                "process_info": {
                    "process_id": process_info.process_id,
                    "title": process_info.title,
                    "description": process_info.description,
                    "progress": process_info.progress,
                    "status": process_info.status.value,
                    "current_step": process_info.current_step,
                    "total_steps": process_info.total_steps,
                    "current_step_number": process_info.current_step_number,
                    "estimated_remaining_time": process_info.estimated_remaining_time,
                    "start_time": process_info.start_time,
                    "metadata": process_info.metadata
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"プロセス情報取得エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/api/progress")
    async def get_active_processes():
        """アクティブプロセス一覧取得"""
        try:
            progress_system = get_progress_system()
            active_processes = progress_system.get_active_processes()
            
            return {
                "success": True,
                "active_processes": [
                    {
                        "process_id": process.process_id,
                        "title": process.title,
                        "description": process.description,
                        "progress": process.progress,
                        "status": process.status.value,
                        "current_step": process.current_step,
                        "total_steps": process.total_steps,
                        "current_step_number": process.current_step_number,
                        "estimated_remaining_time": process.estimated_remaining_time,
                        "start_time": process.start_time,
                        "metadata": process.metadata
                    }
                    for process in active_processes
                ],
                "count": len(active_processes)
            }
            
        except Exception as e:
            logger.error(f"アクティブプロセス取得エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.post("/api/notifications")
    async def send_notification(request: NotificationRequest):
        """通知送信"""
        try:
            progress_system = get_progress_system()
            
            # 通知タイプのマッピング
            type_mapping = {
                "info": NotificationType.INFO,
                "success": NotificationType.SUCCESS,
                "warning": NotificationType.WARNING,
                "error": NotificationType.ERROR
            }
            
            notification_type = type_mapping.get(request.type.lower(), NotificationType.INFO)
            
            notification_id = progress_system._add_notification(
                type=notification_type,
                title=request.title,
                message=request.message,
                auto_dismiss=request.auto_dismiss
            )
            
            # WebSocket通知
            await manager.broadcast(json.dumps({
                "type": "notification",
                "notification_type": request.type,
                "title": request.title,
                "message": request.message,
                "notification_id": notification_id
            }))
            
            return {
                "success": True,
                "notification_id": notification_id,
                "message": "通知が送信されました"
            }
            
        except Exception as e:
            logger.error(f"通知送信エラー: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.websocket("/ws/progress")
    async def websocket_endpoint(websocket: WebSocket):
        """進捗通知用WebSocketエンドポイント"""
        await manager.connect(websocket)
        try:
            while True:
                # クライアントからのメッセージを受信（キープアライブ）
                data = await websocket.receive_text()
                if data == "ping":
                    await websocket.send_text("pong")
                    
        except WebSocketDisconnect:
            manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocketエラー: {e}")
            manager.disconnect(websocket)

# 使用例とテスト用関数
async def demo_api_usage():
    """API使用例のデモ"""
    import httpx
    
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # プロセス開始
        response = await client.post(f"{base_url}/api/progress/start", json={
            "title": "APIテストプロセス",
            "description": "API経由での進捗管理テスト",
            "total_steps": 10,
            "category": "test"
        })
        
        if response.status_code == 200:
            result = response.json()
            process_id = result["process_id"]
            print(f"プロセス開始: {process_id}")
            
            # 進捗更新
            for i in range(1, 11):
                await client.put(f"{base_url}/api/progress/{process_id}/update", json={
                    "progress": i / 10,
                    "current_step": f"ステップ {i} を実行中",
                    "step_number": i,
                    "metadata": {"step_data": f"data_{i}"}
                })
                print(f"進捗更新: {i/10:.1%}")
                
                await asyncio.sleep(1)  # 1秒待機
            
            # プロセス完了
            await client.put(f"{base_url}/api/progress/{process_id}/complete", json={
                "final_message": "APIテストが完了しました",
                "metadata": {"test_result": "success"}
            })
            print("プロセス完了")

if __name__ == "__main__":
    # FastAPIアプリ作成例
    app = FastAPI(title="進行状態通知API")
    create_progress_api(app)
    
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
