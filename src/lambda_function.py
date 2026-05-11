from src.ingest import main

def lambda_handler(event, context):
    try:
        main() 
        print("Success in lambda_handler.")
        return {"statusCode": 200} # return 200 means success
    except Exception as e:
        print(f"Error in lambda_handler: {e}")
        return {"statusCode": 500, "body": str(e)} # return 500 means error