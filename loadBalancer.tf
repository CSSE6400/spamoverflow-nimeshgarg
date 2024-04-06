resource "aws_lb_target_group" "spamoverflow" { 
  name          = "spamoverflow" 
  port          = 8080 
  protocol      = "HTTP" 
  vpc_id        = aws_security_group.spamoverflow.vpc_id 
  target_type   = "ip" 
 
  health_check { 
    path                = "/api/v1/health" 
    port                = "8080" 
    protocol            = "HTTP" 
    healthy_threshold   = 2 
    unhealthy_threshold = 2 
    timeout             = 5 
    interval            = 10 
  } 
}

resource "aws_lb" "spamoverflow" {
  name               = "spamoverflow"
  internal           = false
  load_balancer_type = "application"
  subnets            = data.aws_subnets.private.ids
  security_groups    = [aws_security_group.spamoverflow.id]
}

resource "aws_lb_listener" "spamoverflow" {
  load_balancer_arn = aws_lb.spamoverflow.arn
  port              = "8080"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.spamoverflow.arn
  }
}
