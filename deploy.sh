#!/bin/bash
set -e

FUNCTION_NAME="finance-pipeline"
HANDLER="src.lambda_function.lambda_handler"
ROLE_ARN="arn:aws:iam::477913828854:role/finance-pipeline-lambda-role"
RUNTIME="python3.12"
REGION="us-east-1"
SCHEDULE="rate(1 day)"

# 1. Package
echo "Packaging..."
rm -rf package lambda.zip
pip3 install -r requirements.txt -t package/ --quiet
cp -r src/ package/src/
cd package && zip -r ../lambda.zip . --quiet && cd ..
echo "Zip: $(du -sh lambda.zip | cut -f1)"

# 2. Create or update Lambda
if aws lambda get-function --function-name $FUNCTION_NAME --region $REGION &>/dev/null; then
    echo "Updating..."
    aws lambda update-function-code \
        --function-name $FUNCTION_NAME \
        --zip-file fileb://lambda.zip \
        --region $REGION
else
    echo "Creating..."
    aws lambda create-function \
        --function-name $FUNCTION_NAME \
        --runtime $RUNTIME \
        --role $ROLE_ARN \
        --handler $HANDLER \
        --zip-file fileb://lambda.zip \
        --timeout 300 \
        --memory-size 256 \
        --region $REGION
fi

# 3. CloudWatch daily schedule
RULE_ARN=$(aws events put-rule \
    --name finance-pipeline-daily \
    --schedule-expression "$SCHEDULE" \
    --state ENABLED \
    --region $REGION \
    --query 'RuleArn' --output text)

LAMBDA_ARN=$(aws lambda get-function \
    --function-name $FUNCTION_NAME \
    --region $REGION \
    --query 'Configuration.FunctionArn' --output text)

# Allow EventBridge to invoke Lambda (fails silently if already exists)
aws lambda add-permission \
    --function-name $FUNCTION_NAME \
    --statement-id finance-pipeline-schedule \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $RULE_ARN \
    --region $REGION 2>/dev/null || true

aws events put-targets \
    --rule finance-pipeline-daily \
    --targets "Id=1,Arn=$LAMBDA_ARN" \
    --region $REGION

echo "Done. Scheduled: $SCHEDULE"
