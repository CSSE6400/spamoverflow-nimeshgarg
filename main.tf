terraform {
    required_providers {
        aws = {
            source  = "hashicorp/aws"
            version = "~> 4.0"
        }
    }
}

provider "aws" {
    region = "us-east-1"
    shared_credentials_files = ["./credentials"]
    default_tags {
        tags = {
            Course       = "CSSE6400"
            Name         = "SpamOverflow"
            Automation   = "Terraform"
        }
    }
}

resource "local_file" "url" {
    content  = "http://my-url/" # replace this with a URL from your terraform
    filename = "./api.txt"
}