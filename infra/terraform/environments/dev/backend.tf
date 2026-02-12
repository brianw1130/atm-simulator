# Local backend for dev environment.
# For production, switch to S3 backend:
#   terraform {
#     backend "s3" {
#       bucket = "atm-simulator-terraform-state"
#       key    = "production/terraform.tfstate"
#       region = "us-east-1"
#     }
#   }

terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
