# ==============================================================================
# IAM Role for Step Functions State Machine
# ==============================================================================
resource "aws_iam_role" "step_function_role" {
  name = "${var.project_name}-step-function-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "step_function_policy" {
  name        = "${var.project_name}-step-function-policy"
  description = "Policy for Step Functions state machine to invoke Lambda functions"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "InvokeLambda"
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          "${aws_lambda_function.extract.arn}:*",
          "${aws_lambda_function.extract.arn}",
          "${aws_lambda_function.transcribe.arn}:*",
          "${aws_lambda_function.transcribe.arn}",
          "${aws_lambda_function.enrich.arn}:*",
          "${aws_lambda_function.enrich.arn}",
          aws_lambda_function.vector.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "step_function_attach" {
  role       = aws_iam_role.step_function_role.name
  policy_arn = aws_iam_policy.step_function_policy.arn
}

# ==============================================================================
# Extract State Machine (Step Function)
# ==============================================================================
resource "aws_sfn_state_machine" "extract_state_machine" {
  name       = "c23-podex-ai-state-machine"
  role_arn   = aws_iam_role.step_function_role.arn
  type       = "STANDARD"
  definition = jsonencode({
    Comment       = "extract"
    StartAt       = "extract"
    QueryLanguage = "JSONata"
    States = {
      extract = {
        Type     = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Output   = "{% $states.result.Payload %}"
        Arguments = {
          Payload      = "{% $states.input %}"
          FunctionName = aws_lambda_function.extract.arn
        }
        Retry = [
          {
            ErrorEquals = [
              "Lambda.ServiceException",
              "Lambda.AWSLambdaException",
              "Lambda.SdkClientException",
              "Lambda.TooManyRequestsException"
            ]
            IntervalSeconds = 1
            MaxAttempts     = 3
            BackoffRate     = 2
            JitterStrategy  = "FULL"
          }
        ]
        Next = "Map"
      }
      Map = {
        Type         = "Map"
        MaxConcurrency = 30
        ItemProcessor = {
          ProcessorConfig = {
            Mode = "INLINE"
          }
          StartAt = "Transcribe"
          States = {
            Transcribe = {
              Type     = "Task"
              Resource = "arn:aws:states:::lambda:invoke"
              Arguments = {
                FunctionName = aws_lambda_function.transcribe.arn
                Payload = {
                  episode_s3_url = "$states.input"
                }
              }
              Output = "$states.result.Payload"
              Next   = "Parallel"
            }
            Parallel = {
              Type = "Parallel"
              End  = true
              Branches = [
                {
                  StartAt = "Enrich"
                  States = {
                    Enrich = {
                      Type     = "Task"
                      Resource = "arn:aws:states:::lambda:invoke"
                      Output   = "$states.result.Payload"
                      Arguments = {
                        Payload = {
                          episode_uri = "$states.input.episode_uri"
                        }
                        FunctionName = aws_lambda_function.enrich.arn
                      }
                      Retry = [
                        {
                          ErrorEquals = [
                            "Lambda.ServiceException",
                            "Lambda.AWSLambdaException",
                            "Lambda.SdkClientException",
                            "Lambda.TooManyRequestsException"
                          ]
                          IntervalSeconds = 1
                          MaxAttempts     = 3
                          BackoffRate     = 2
                          JitterStrategy  = "FULL"
                        }
                      ]
                      End = true
                    }
                  }
                },
                {
                  StartAt = "vector"
                  States = {
                    vector = {
                      Type     = "Task"
                      Resource = "arn:aws:states:::lambda:invoke"
                      Output   = "$states.result.Payload"
                      Arguments = {
                        Payload = {
                          episode_uri = "$states.input.episode_uri"
                        }
                        FunctionName = aws_lambda_function.vector.arn
                      }
                      Retry = [
                        {
                          ErrorEquals = [
                            "Lambda.ServiceException",
                            "Lambda.AWSLambdaException",
                            "Lambda.SdkClientException",
                            "Lambda.TooManyRequestsException"
                          ]
                          IntervalSeconds = 1
                          MaxAttempts     = 3
                          BackoffRate     = 2
                          JitterStrategy  = "FULL"
                        }
                      ]
                      End = true
                    }
                  }
                }
              ]
            }
          }
        }
        Items = "$states.input.uploaded_paths"
        End   = true
      }
    }
  })
}
