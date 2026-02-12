# S3 backend for production state — encrypted and versioned.
# Create the bucket manually before first init:
#   aws s3api create-bucket --bucket atm-simulator-terraform-state --region us-east-1
#   aws s3api put-bucket-versioning --bucket atm-simulator-terraform-state \
#     --versioning-configuration Status=Enabled
#   aws s3api put-bucket-encryption --bucket atm-simulator-terraform-state \
#     --server-side-encryption-configuration \
#     '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'

terraform {
  backend "s3" {
    bucket = "atm-simulator-terraform-state"
    key    = "production/terraform.tfstate"
    region = "us-east-1"
  }
}
