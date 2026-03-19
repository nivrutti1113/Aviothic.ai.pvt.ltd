// MongoDB initialization script for Aviothic AI Platform
// Creates required collections and indexes

print("Initializing Aviothic AI MongoDB database...");

// Create users collection with proper indexes
db.createCollection("users");
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.users.createIndex({ "is_active": 1 });

// Create inferences collection with proper indexes
db.createCollection("inferences");
db.inferences.createIndex({ "case_id": 1 }, { unique: true });
db.inferences.createIndex({ "timestamp": -1 });
db.inferences.createIndex({ "model_version": 1 });
db.inferences.createIndex({ "prediction": 1 });
db.inferences.createIndex({ 
    "timestamp": -1, 
    "model_version": 1 
});

// Create audit logs collection
db.createCollection("audit_logs");
db.audit_logs.createIndex({ "timestamp": -1 });
db.audit_logs.createIndex({ "user_id": 1 });
db.audit_logs.createIndex({ "action": 1 });

print("Database initialization completed successfully!");