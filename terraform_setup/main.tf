terraform {
  backend "local" {}
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

locals {
  aws_ecr_repository_name = var.aws_resource_name_prefix
  aws_vpc_stack_name = "${var.aws_resource_name_prefix}-vpc-stack"
  aws_ecs_service_stack_name = "${var.aws_resource_name_prefix}-svc-stack"
  aws_ecs_cluster_name = "${var.aws_resource_name_prefix}-cluster"
  aws_ecs_service_name = "${var.aws_resource_name_prefix}-service"
  aws_ecs_execution_role_name = "${var.aws_resource_name_prefix}-ecs-execution-role"
}

resource "aws_ecr_repository" "demo-app-repository" {
  name = local.aws_ecr_repository_name
}
