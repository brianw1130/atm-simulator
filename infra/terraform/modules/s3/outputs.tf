output "bucket_name" {
  description = "Name of the statements S3 bucket"
  value       = aws_s3_bucket.statements.bucket
}

output "bucket_arn" {
  description = "ARN of the statements S3 bucket"
  value       = aws_s3_bucket.statements.arn
}
