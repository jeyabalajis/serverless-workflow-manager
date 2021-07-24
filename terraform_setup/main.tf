terraform {
  backend "remote" {
    organization = "jeyasandbox"
    workspaces {
      name = "serverless-workflow-manager"
    }
  }
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 3.27"
    }
  }

  required_version = ">= 0.14.9"
}

provider "aws" {
  profile = "default"
  region  = "ap-south-1"
}

resource "aws_ecr_repository" "demo-app-repository" {
  name = var.aws_resource_name_prefix
}
