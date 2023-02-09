# NotionAPI
Implementation of Notion API to make automatic actions over a Notion DB.

There is a Lambda for each functionality and they are build in docker.
AWS SAM is used to deploy all the infrastructure automatically: 
 - API Gateway
 - Lambda function
 - IAM & policies
 - ECR Docker image

## Functionality
### 1. Add to DB
Sending a simple JSON to the gateway, the funtion build a complex body based on Notion DB schema previusly defined. The function is in charge of re-send the request to Notion API.

### 2. Query DB
Receive the date to make the query, and it build the message to send to Notion API. Besides, filter data and create simple reports base on the schema.

### AUTH
Token security to access through Notion API is store en AWS Secrets Manager

## License
Distributed under the MIT License.


