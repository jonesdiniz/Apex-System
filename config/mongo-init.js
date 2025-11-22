// MongoDB Initialization Script for APEX System

db = db.getSiblingDB('apex_system');

// Create collections with validation schemas
db.createCollection('services', {
    validator: {
        $jsonSchema: {
            bsonType: 'object',
            required: ['name', 'version', 'status', 'created_at'],
            properties: {
                name: { bsonType: 'string' },
                version: { bsonType: 'string' },
                port: { bsonType: 'int' },
                url: { bsonType: 'string' },
                status: { enum: ['healthy', 'degraded', 'unhealthy', 'unknown'] },
                created_at: { bsonType: 'date' },
                updated_at: { bsonType: 'date' }
            }
        }
    }
});

db.createCollection('metrics');
db.createCollection('predictions');
db.createCollection('actions');
db.createCollection('events');
db.createCollection('decisions');
db.createCollection('audit_logs');
db.createCollection('tokens');

// Create indexes for better performance
db.services.createIndex({ 'name': 1 }, { unique: true });
db.services.createIndex({ 'status': 1 });
db.services.createIndex({ 'created_at': -1 });

db.metrics.createIndex({ 'service_name': 1, 'timestamp': -1 });
db.metrics.createIndex({ 'timestamp': -1 });

db.predictions.createIndex({ 'service_name': 1, 'predicted_at': -1 });
db.predictions.createIndex({ 'prediction_type': 1 });
db.predictions.createIndex({ 'predicted_for': 1 });

db.actions.createIndex({ 'service_name': 1, 'triggered_at': -1 });
db.actions.createIndex({ 'action_type': 1 });
db.actions.createIndex({ 'status': 1 });

db.events.createIndex({ 'service_name': 1, 'occurred_at': -1 });
db.events.createIndex({ 'event_type': 1 });

db.decisions.createIndex({ 'service_name': 1, 'created_at': -1 });

db.audit_logs.createIndex({ 'timestamp': -1 });
db.audit_logs.createIndex({ 'service_name': 1, 'timestamp': -1 });
db.audit_logs.createIndex({ 'action': 1 });

db.tokens.createIndex({ 'user_id': 1, 'platform': 1 }, { unique: true });
db.tokens.createIndex({ 'expires_at': 1 }, { expireAfterSeconds: 0 });

print('APEX System MongoDB initialization completed successfully');
