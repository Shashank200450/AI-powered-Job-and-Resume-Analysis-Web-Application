import pandas as pd
from pymongo import MongoClient
import os
import re

MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = 'jobsinline'
COLLECTION_NAME = 'job_roles_data'
EXCEL_FILE_PATH = 'jobrolespskillsframeworks.xlsx'  # Update this to your actual file path

def standardize_job_name(job_name):
    """Standardize job names for better matching"""
    # Convert to lowercase and remove special characters
    standardized = re.sub(r'[^\w\s]', '', job_name.lower().strip())
    # Remove common suffixes/prefixes
    standardized = re.sub(r'\b(senior|junior|lead|principal)\b', '', standardized)
    standardized = re.sub(r'\b(i|ii|iii|iv)\b', '', standardized)
    # Remove extra spaces
    standardized = re.sub(r'\s+', ' ', standardized).strip()
    return standardized

def migrate_data():
    try:
        df = pd.read_excel(EXCEL_FILE_PATH, sheet_name='Sheet1')
        print("Excel file loaded successfully.")

        client = MongoClient(MONGO_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]

        if COLLECTION_NAME in db.list_collection_names():
            collection.drop()
            print(f"Existing collection '{COLLECTION_NAME}' dropped.")

        # Standardize job names and add a searchable version
        df['standardized_job_role'] = df['JOB ROLES'].apply(standardize_job_name)
        
        # Clean skills and frameworks
        if 'PROGRAMMING SKILLS' in df.columns:
            df['PROGRAMMING SKILLS'] = df['PROGRAMMING SKILLS'].str.strip()
        if 'FRAMEWORKS' in df.columns:
            df['FRAMEWORKS'] = df['FRAMEWORKS'].str.strip()

        data_to_insert = df.to_dict('records')

        result = collection.insert_many(data_to_insert)
        print(f"Successfully inserted {len(result.inserted_ids)} documents.")
        print("Data migration complete.")

        # Print sample data for verification
        print("\nSample job roles in database:")
        for i, doc in enumerate(collection.find().limit(5)):
            print(f"{i+1}. Original: {doc['JOB ROLES']} -> Standardized: {doc['standardized_job_role']}")

    except FileNotFoundError:
        print(f"Error: The file '{EXCEL_FILE_PATH}' was not found.")
    except Exception as e:
        print(f"An error occurred during migration: {e}")
    finally:
        if 'client' in locals():
            client.close()
            print("MongoDB connection closed.")

if __name__ == '__main__':
    migrate_data()