terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
  }
}

data "aws_ecr_authorization_token" "ecr_token" {}

provider "docker" {
  registry_auth {
    address  = data.aws_ecr_authorization_token.ecr_token.proxy_endpoint
    username = data.aws_ecr_authorization_token.ecr_token.user_name
    password = data.aws_ecr_authorization_token.ecr_token.password
  }
}


provider "aws" {
  region                   = "us-east-1"
  shared_credentials_files = ["./credentials"]
  default_tags {
    tags = {
      Course       = "CSSE6400"
      Name         = "SpamOverflow"
      Automation   = "Terraform"
      Student_Name = "Nimesh Garg"
      Student_ID   = "47285398"
    }
  }
}

resource "local_file" "url" {
  content    = "http://${aws_lb.spamoverflow.dns_name}:8080/api/v1" # replace this with a URL from your terraform
  filename   = "./api.txt"
  depends_on = [aws_lb.spamoverflow]
}

data "aws_iam_role" "lab" {
  name = "LabRole"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "private" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

locals {
  database_password = "passwordNimesh"
  database_username = "adminNimesh"
}
