#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '#' | xargs)
else
    echo "Error: .env file not found"
    exit 1
fi

echo "creating lambda_package directory ..."
rm -R lambda_package
mkdir -p lambda_package
echo "installing dependencies in lambda_package ..."
pip install --target lambda_package -r ./lambda/requirements.txt
echo "copying lambda code to lambda_package ..."
cp ./lambda/* ./lambda_package
echo "building and deploying lambda ..."
cd lambda_package || exit 1
sam build
sam package \
    --template-file template.yaml \
    --output-template-file packaged.yaml \
    --s3-bucket "${S3_BUCKET}" \
    --region "${LAMBDA_REGION}"
sam deploy \
    --template-file packaged.yaml \
    --stack-name "${STACK_NAME}" \
    --capabilities CAPABILITY_IAM \
    --region "${LAMBDA_REGION}"

cd ..
echo "Lambda code successfully, built, packaged and deployed"
