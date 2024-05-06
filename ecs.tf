resource "aws_ecs_cluster" "spamoverflow" {
  name = "spamoverflow"
}

resource "aws_ecs_task_definition" "spamoverflow" {
  family                   = "spamoverflow"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = 4096
  memory                   = 16384
  execution_role_arn       = data.aws_iam_role.lab.arn
  depends_on               = [docker_image.spamoverflow]

  container_definitions = <<DEFINITION
 [ 
   { 
    "image": "${docker_registry_image.spamoverflow.name}", 
    "cpu": 4096, 
    "memory": 16384, 
    "name": "spamoverflow", 
    "networkMode": "awsvpc", 
    "portMappings": [ 
      { 
       "containerPort": 8080, 
       "hostPort": 8080 
      } 
    ], 
    "environment": [ 
      { 
       "name": "SQLALCHEMY_DATABASE_URI", 
       "value": "postgresql://${local.database_username}:${local.database_password}@${aws_db_instance.database.address}:${aws_db_instance.database.port}/${aws_db_instance.database.db_name}" 
      } 
    ], 
    "logConfiguration": { 
      "logDriver": "awslogs", 
      "options": { 
       "awslogs-group": "/spamoverflow/api", 
       "awslogs-region": "us-east-1", 
       "awslogs-stream-prefix": "ecs", 
       "awslogs-create-group": "true" 
      } 
    } 
   } 
 ] 
 DEFINITION 
}


resource "aws_ecs_service" "spamoverflow" {
  name            = "spamoverflow"
  cluster         = aws_ecs_cluster.spamoverflow.id
  task_definition = aws_ecs_task_definition.spamoverflow.arn
  desired_count   = 2
  launch_type     = "FARGATE"
  depends_on      = [aws_ecs_task_definition.spamoverflow]

  network_configuration {
    subnets          = data.aws_subnets.private.ids
    security_groups  = [aws_security_group.spamoverflow.id]
    assign_public_ip = true
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.spamoverflow.arn
    container_name   = "spamoverflow"
    container_port   = 8080
  }

}

resource "aws_security_group" "spamoverflow" {
  name        = "spamoverflow"
  description = "TaskOverflow Security Group"

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ingress {
  #   from_port   = 22
  #   to_port     = 22
  #   protocol    = "tcp"
  #   cidr_blocks = ["0.0.0.0/0"]
  # }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 200
  min_capacity       = 2
  resource_id        = "service/${aws_ecs_cluster.spamoverflow.name}/${aws_ecs_service.spamoverflow.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"

  depends_on = [ aws_ecs_service.spamoverflow ]
}

resource "aws_appautoscaling_policy" "ecs_policy" {
  name               = "cpu20"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }

    target_value = 20
  }
}