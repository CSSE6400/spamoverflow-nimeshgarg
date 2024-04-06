resource "docker_image" "spamoverflow" {
  name = "${aws_ecr_repository.spamoverflow.repository_url}:latest"
  build {
    context = "."
  }
}

resource "docker_registry_image" "spamoverflow" {
  name = docker_image.spamoverflow.name
}

resource "aws_ecr_repository" "spamoverflow" {
  name = "spamoverflow"
}
