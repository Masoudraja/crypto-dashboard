#!/usr/bin/env python3
"""
Database Migration Script for Enhanced Crypto Dashboard
Adds new columns for advanced technical indicators and market data
"""

import psycopg2
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

def get_db_connection():
    """Establish database connection"""
    try:
        return psycopg2.connect(
            host=DB_HOST, 
            port=DB_PORT, 
            dbname=DB_NAME, 
            user=DB_USER, 
            password=DB_PASSWORD
        )
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

def migrate_database():
    """Add new columns for enhanced indicators and market data"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        
        print("🔄 Starting database migration...")
        
        # List of new columns to add
        new_columns = [
            # Market data
            ("market_cap", "BIGINT"),
            ("volume_24h", "BIGINT"), 
            ("change_24h", "DECIMAL(10,4)"),
            
            # Additional SMAs
            ("sma_100", "DECIMAL(20,8)"),
            ("sma_200", "DECIMAL(20,8)"),
            
            # Additional EMAs  
            ("ema_12", "DECIMAL(20,8)"),
            ("ema_26", "DECIMAL(20,8)"),
            
            # Stochastic RSI
            ("stochrsi_k", "DECIMAL(10,4)"),
            ("stochrsi_d", "DECIMAL(10,4)"),
            
            # Advanced indicators
            ("williams_r_14", "DECIMAL(10,4)"),
            ("cci_20", "DECIMAL(10,4)"),
            ("atr_14", "DECIMAL(20,8)"),
            
            # Parabolic SAR
            ("psar_long", "DECIMAL(20,8)"),
            ("psar_short", "DECIMAL(20,8)"),
        ]
        
        # Check existing columns first
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'crypto_prices'
        """)
        existing_columns = {row[0] for row in cur.fetchall()}
        
        # Add new columns if they don't exist
        added_columns = 0
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    alter_query = f"ALTER TABLE crypto_prices ADD COLUMN {column_name} {column_type};"
                    cur.execute(alter_query)
                    print(f"✅ Added column: {column_name} ({column_type})")
                    added_columns += 1
                except Exception as e:
                    print(f"⚠️  Failed to add column {column_name}: {e}")
            else:
                print(f"⏭️  Column {column_name} already exists")
        
        # Create indexes for better query performance
        indexes_to_create = [
            ("idx_crypto_prices_coin_timestamp", "crypto_prices", "coin_id, timestamp DESC"),
            ("idx_crypto_prices_timestamp", "crypto_prices", "timestamp DESC"),
            ("idx_crypto_prices_market_cap", "crypto_prices", "market_cap DESC"),
        ]
        
        for index_name, table_name, columns in indexes_to_create:
            try:
                # Check if index exists
                cur.execute("""
                    SELECT indexname FROM pg_indexes 
                    WHERE tablename = %s AND indexname = %s
                """, (table_name, index_name))
                
                if not cur.fetchone():
                    create_index_query = f"CREATE INDEX {index_name} ON {table_name} ({columns});"
                    cur.execute(create_index_query)
                    print(f"✅ Created index: {index_name}")
                else:
                    print(f"⏭️  Index {index_name} already exists")
            except Exception as e:
                print(f"⚠️  Failed to create index {index_name}: {e}")
        
        conn.commit()
        cur.close()
        
        print(f"\n🎉 Database migration completed successfully!")
        print(f"📊 Added {added_columns} new columns")
        print(f"🔍 Indexes optimized for enhanced queries")
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def verify_migration():
    """Verify the migration was successful"""
    conn = get_db_connection()
    if conn is None:
        return False
    
    try:
        cur = conn.cursor()
        
        # Get current table structure
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'crypto_prices'
            ORDER BY ordinal_position
        """)
        
        columns = cur.fetchall()
        
        print("\n📋 Current crypto_prices table structure:")
        print("=" * 50)
        for column_name, data_type in columns:
            print(f"  {column_name:<25} {data_type}")
        
        print(f"\n📊 Total columns: {len(columns)}")
        
        cur.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("🚀 Enhanced Crypto Dashboard - Database Migration")
    print("=" * 60)
    
    if migrate_database():
        verify_migration()
        print("\n✅ Migration completed successfully!")
        print("🎯 Your database is now ready for advanced indicators!")
    else:
        print("\n❌ Migration failed. Please check the errors above.")