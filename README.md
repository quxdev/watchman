# Watchman

This project contains an AWS Lambda function that checks server statuses on a scheduled basis. The function's source code and configuration are managed within the `./lambda` directory and deployed using the AWS Serverless Application Model (SAM) CLI, which automates the deployment process.

## Directory Structure

- **./lambda**: Contains all the code related to the Lambda function.
  - **mail.py**: Handles email-related functionalities.
  - **template.yml**: Defines the AWS resources and configurations for the Lambda function.
  - **lambda_function.py**: The main entry point for the Lambda function logic.

## Deployment Instructions

To deploy the Lambda function, follow these steps:

1. Ensure you have the AWS SAM CLI installed. You can download it from the [AWS SAM CLI installation page](https://aws.amazon.com/serverless/sam/).

2. Open your terminal and navigate to the root directory of the project.

3. Run the following command to build and deploy the Lambda function:
   ```bash
   ./deploy.sh
   ```

## Additional Information

- The deployment process is fully automated and relies on the `template.yml` file to configure and deploy the necessary AWS resources.
- Ensure your AWS credentials are configured correctly on your machine to allow the deployment process to access your AWS account.

## Prerequisites

- **AWS SAM CLI**: Required for building and deploying the serverless application. Make sure it is installed and configured on your system.

## Troubleshooting

- If you encounter any issues during deployment, verify that your AWS credentials are set up correctly and that you have the necessary permissions to deploy resources in your AWS account.
- Consult the AWS SAM CLI documentation for additional troubleshooting steps and information. 
