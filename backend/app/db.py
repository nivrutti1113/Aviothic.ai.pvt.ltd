import datetime
import logging
from typing import Any, Dict, Optional, List

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
from pymongo import ASCENDING, DESCENDING

from .config import settings

logger = logging.getLogger(__name__)


class Database:
    """Production-ready MongoDB database service for Aviothic AI Platform.
    
    Medical audit compliant database operations with proper error handling,
    indexing, and ObjectId conversion for API responses.
    
    Single record per prediction storage with all required fields:
    - case_id
    - timestamp
    - prediction
    - probabilities
    - gradcam_path
    - model_version
    """
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self._indexes_created = False

    async def connect(self):
        """Connect to MongoDB and initialize collections.
        
        Production-ready connection with proper error handling
        and automatic index creation.
        """
        try:
            logger.info(f"Connecting to MongoDB: {settings.MONGO_URI}")
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000
            )
            self.db = self.client[settings.MONGO_DB]
            
            # Test connection
            await self.client.admin.command('ping')
            logger.info("MongoDB connection successful")
            
            # Create indexes for optimal query performance
            await self._create_indexes()
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    async def close(self):
        """Close MongoDB connection gracefully."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    async def _create_indexes(self):
        """Create database indexes for optimal performance.
        
        Medical audit friendly indexing strategy.
        """
        if self._indexes_created or not self.db:
            return
            
        try:
            # Index for time-based queries
            await self.db.inferences.create_index([("timestamp", DESCENDING)])
            
            # Index for case lookups
            await self.db.inferences.create_index([("case_id", ASCENDING)], unique=True)
            
            # Index for model version queries
            await self.db.inferences.create_index([("model_version", ASCENDING)])
            
            # Compound index for common query patterns
            await self.db.inferences.create_index([
                ("timestamp", DESCENDING),
                ("model_version", ASCENDING)
            ])
            
            self._indexes_created = True
            logger.info("Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")

    def _convert_object_id(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string for API responses.
        
        Medical audit compliant data serialization.
        """
        if not doc:
            return {}
        
        # Create a copy to avoid modifying original
        result = dict(doc)
        
        # Convert ObjectId to string
        if "_id" in result:
            result["_id"] = str(result["_id"])
        
        # Convert datetime to ISO format for consistency
        if "timestamp" in result and isinstance(result["timestamp"], datetime.datetime):
            result["timestamp"] = result["timestamp"].isoformat()
            
        return result

    async def insert_inference(self, record: Dict[str, Any]) -> str:
        """Insert one inference record into MongoDB.
        
        Production-ready single insert operation with proper validation.
        No duplicate insert functions - this is the only insert method.
        
        Args:
            record: Inference record with required fields:
                   case_id, timestamp, prediction, probabilities, 
                   gradcam_path, model_version
                    
        Returns:
            Inserted document ID as string
        
        Medical audit requirements:
        - One record per prediction
        - All required fields stored
        - ObjectId converted to string for API
        """
        if not self.db:
            raise RuntimeError("Database not connected")
            
        # Ensure required fields are present
        required_fields = ['case_id', 'user_id', 'prediction', 'confidence', 'risk_score', 'explanation', 'image_url', 'gradcam_path', 'report_path', 'model_version']
        missing_fields = [field for field in required_fields if field not in record]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        
        # Add timestamp if not provided
        if 'timestamp' not in record:
            record['timestamp'] = datetime.datetime.utcnow()
        
        # Ensure record is a clean copy
        clean_record = dict(record)
        
        try:
            logger.debug(f"Inserting inference record for case: {record.get('case_id')}")
            result = await self.db.inferences.insert_one(clean_record)
            logger.info(f"Successfully inserted inference record: {result.inserted_id}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Failed to insert inference record: {e}")
            raise

    async def get_inference_by_case_id(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve inference record by case ID.
        
        Args:
            case_id: Unique case identifier
            
        Returns:
            Inference record with ObjectId converted to string, or None
        """
        if not self.db:
            raise RuntimeError("Database not connected")
            
        try:
            doc = await self.db.inferences.find_one({"case_id": case_id})
            return self._convert_object_id(doc) if doc else None
        except Exception as e:
            logger.error(f"Failed to retrieve inference record {case_id}: {e}")
            raise

    async def get_recent_inferences(self, limit: int = 100, model_version: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent inference records for monitoring and audit.
        
        Args:
            limit: Maximum number of records to return
            model_version: Optional filter by model version
            
        Returns:
            List of inference records with ObjectId converted to string
        
        Medical audit friendly with proper pagination and filtering.
        """
        if not self.db:
            raise RuntimeError("Database not connected")
            
        try:
            query = {}
            if model_version:
                query["model_version"] = model_version
            
            cursor = self.db.inferences.find(query).sort("timestamp", DESCENDING).limit(int(limit))
            
            records = []
            async for doc in cursor:
                records.append(self._convert_object_id(doc))
            
            logger.debug(f"Retrieved {len(records)} recent inference records")
            return records
            
        except Exception as e:
            logger.error(f"Failed to retrieve recent inferences: {e}")
            raise

    async def get_inference_statistics(self) -> Dict[str, Any]:
        """Get inference statistics for monitoring and reporting.
        
        Returns:
            Dictionary with total count, model versions, and recent activity
        
        Medical audit friendly reporting capabilities.
        """
        if not self.db:
            raise RuntimeError("Database not connected")
            
        try:
            # Get total count
            total_count = await self.db.inferences.count_documents({})
            
            # Get recent count (last 24 hours)
            twenty_four_hours_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
            recent_count = await self.db.inferences.count_documents({"timestamp": {"$gte": twenty_four_hours_ago}})
            
            # Get model version distribution
            pipeline = [
                {"$group": {"_id": "$model_version", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}}
            ]
            model_stats_cursor = self.db.inferences.aggregate(pipeline)
            model_stats = []
            async for doc in model_stats_cursor:
                model_stats.append({
                    "model_version": doc["_id"],
                    "count": doc["count"]
                })
            
            return {
                "total_inferences": total_count,
                "recent_24h_count": recent_count,
                "model_version_distribution": model_stats,
                "timestamp": datetime.datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get inference statistics: {e}")
            raise


# Global database instance
db = Database()

__all__ = ["db"]
