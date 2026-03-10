# -*- coding: utf-8 -*-
"""
===================================
分析相關模型
===================================

職責：
1. 定義分析請求和響應模型
2. 定義任務狀態模型
3. 定義非同步任務佇列相關模型
"""

from typing import Optional, List, Any
from enum import Enum

from pydantic import BaseModel, Field


class TaskStatusEnum(str, Enum):
    """任務狀態列舉"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalyzeRequest(BaseModel):
    """分析請求模型"""
    
    stock_code: Optional[str] = Field(
        None, 
        description="單隻股票程式碼", 
        example="AAPL"
    )
    stock_codes: Optional[List[str]] = Field(
        None,
        description="多隻股票程式碼（與 stock_code 二選一）",
        example=["AAPL", "TSLA"]
    )
    report_type: str = Field(
        "detailed", 
        description="報告型別",
        pattern="^(simple|detailed)$"
    )
    force_refresh: bool = Field(
        True,
        description="是否強制重新整理（忽略快取）"
    )
    async_mode: bool = Field(
        False,
        description="是否使用非同步模式"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "stock_code": "AAPL",
                "report_type": "detailed",
                "force_refresh": False,
                "async_mode": False
            }
        }


class AnalysisResultResponse(BaseModel):
    """分析結果響應模型"""
    
    query_id: str = Field(..., description="分析記錄唯一標識")
    stock_code: str = Field(..., description="股票程式碼")
    stock_name: Optional[str] = Field(None, description="股票名稱")
    report: Optional[Any] = Field(None, description="分析報告")
    created_at: str = Field(..., description="建立時間")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query_id": "abc123def456",
                "stock_code": "AAPL",
                "stock_name": "貴州茅臺",
                "report": {
                    "summary": {
                        "sentiment_score": 75,
                        "operation_advice": "持有"
                    }
                },
                "created_at": "2024-01-01T12:00:00"
            }
        }


class TaskAccepted(BaseModel):
    """非同步任務接受響應"""
    
    task_id: str = Field(..., description="任務 ID，用於查詢狀態")
    status: str = Field(
        ..., 
        description="任務狀態",
        pattern="^(pending|processing)$"
    )
    message: Optional[str] = Field(None, description="提示資訊")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "pending",
                "message": "Analysis task accepted"
            }
        }


class TaskStatus(BaseModel):
    """任務狀態模型"""
    
    task_id: str = Field(..., description="任務 ID")
    status: str = Field(
        ..., 
        description="任務狀態",
        pattern="^(pending|processing|completed|failed)$"
    )
    progress: Optional[int] = Field(
        None, 
        description="進度百分比 (0-100)",
        ge=0,
        le=100
    )
    result: Optional[AnalysisResultResponse] = Field(
        None, 
        description="分析結果（僅在 completed 時存在）"
    )
    error: Optional[str] = Field(
        None, 
        description="錯誤資訊（僅在 failed 時存在）"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task_abc123",
                "status": "completed",
                "progress": 100,
                "result": None,
                "error": None
            }
        }


class TaskInfo(BaseModel):
    """
    任務詳情模型
    
    用於任務列表和 SSE 事件推送
    """
    
    task_id: str = Field(..., description="任務 ID")
    stock_code: str = Field(..., description="股票程式碼")
    stock_name: Optional[str] = Field(None, description="股票名稱")
    status: TaskStatusEnum = Field(..., description="任務狀態")
    progress: int = Field(0, description="進度百分比 (0-100)", ge=0, le=100)
    message: Optional[str] = Field(None, description="狀態訊息")
    report_type: str = Field("detailed", description="報告型別")
    created_at: str = Field(..., description="建立時間")
    started_at: Optional[str] = Field(None, description="開始執行時間")
    completed_at: Optional[str] = Field(None, description="完成時間")
    error: Optional[str] = Field(None, description="錯誤資訊（僅在 failed 時存在）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "abc123def456",
                "stock_code": "AAPL",
                "stock_name": "貴州茅臺",
                "status": "processing",
                "progress": 50,
                "message": "正在分析中...",
                "report_type": "detailed",
                "created_at": "2026-02-05T10:30:00",
                "started_at": "2026-02-05T10:30:01",
                "completed_at": None,
                "error": None
            }
        }


class TaskListResponse(BaseModel):
    """任務列表響應模型"""
    
    total: int = Field(..., description="任務總數")
    pending: int = Field(..., description="等待中的任務數")
    processing: int = Field(..., description="處理中的任務數")
    tasks: List[TaskInfo] = Field(..., description="任務列表")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total": 3,
                "pending": 1,
                "processing": 2,
                "tasks": []
            }
        }


class DuplicateTaskErrorResponse(BaseModel):
    """重複任務錯誤響應模型"""
    
    error: str = Field("duplicate_task", description="錯誤型別")
    message: str = Field(..., description="錯誤資訊")
    stock_code: str = Field(..., description="股票程式碼")
    existing_task_id: str = Field(..., description="已存在的任務 ID")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "duplicate_task",
                "message": "股票 AAPL 正在分析中",
                "stock_code": "AAPL",
                "existing_task_id": "abc123def456"
            }
        }
