
terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

# Enable required APIs
resource "google_project_service" "required_apis" {
  for_each = toset([
    "cloudbuild.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "sqladmin.googleapis.com",
    "firebase.googleapis.com"
  ])
  
  service = each.value
  disable_on_destroy = false
}

# Cloud SQL instance
resource "google_sql_database_instance" "main" {
  name             = "ai-assistant-db"
  database_version = "POSTGRES_15"
  region           = var.region
  
  settings {
    tier = "db-f1-micro"
    
    database_flags {
      name  = "max_connections"
      value = "100"
    }
  }
  
  deletion_protection = false
}

resource "google_sql_database" "database" {
  name     = "ai_assistant"
  instance = google_sql_database_instance.main.name
}

resource "google_sql_user" "user" {
  name     = "ai_assistant_user"
  instance = google_sql_database_instance.main.name
  password = "your-secure-password"
}

# Secrets
resource "google_secret_manager_secret" "firebase_project_id" {
  secret_id = "firebase-project-id"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "firebase_private_key" {
  secret_id = "firebase-private-key"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "firebase_client_email" {
  secret_id = "firebase-client-email"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "database_url" {
  secret_id = "database-url"
  
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "openai-api-key"
  
  replication {
    auto {}
  }
}

output "database_connection_name" {
  value = google_sql_database_instance.main.connection_name
}
