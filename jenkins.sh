#!/usr/bin/env bash

set -eu

# configuration
AWS_DEFAULT_REGION="eu-west-1"
STACK_NAME="awslimitchecker"
PYTHON_VERSION="python3.6"
DEPENDENCIES="env/lib/${PYTHON_VERSION}/site-packages/"
ROOT_PWD=$(pwd)
ZIP="${ROOT_PWD}/build.zip"
S3_BUCKET="your-deployment-bucket"
S3_KEY="lambda/${STACK_NAME}.zip"
S3_PATH=s3://${S3_BUCKET}/${S3_KEY}

echo "validating cloudformation"
aws cloudformation validate-template --template-body file://${STACK_NAME}.cf.yaml

echo "installing dependencies"
export PS1="$ "
virtualenv -p ${PYTHON_VERSION} env
source env/bin/activate
pip install -r requirements.txt

echo "zipping dependencies"
(cd ${DEPENDENCIES} && zip -r ${ZIP} ./)

echo "adding code to dependencies zip: ${ZIP}"
zip -g ${ZIP} *.py

echo "copying to S3..."
aws s3 cp ${ZIP} ${S3_PATH}

echo "updating cloudformation"
aws cloudformation deploy                       \
    --template-file ${STACK_NAME}.cf.yaml       \
    --no-fail-on-empty-changeset                \
    --capabilities CAPABILITY_IAM               \
    --stack-name ${STACK_NAME}

echo "update function..."
aws --region ${AWS_DEFAULT_REGION}      \
    lambda update-function-code         \
    --function-name ${STACK_NAME}       \
    --s3-bucket ${S3_BUCKET}            \
    --s3-key ${S3_KEY}
