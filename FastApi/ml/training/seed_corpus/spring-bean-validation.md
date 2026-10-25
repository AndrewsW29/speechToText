---
source_url: https://docs.spring.io/spring-framework/reference/core/validation/beanvalidation.html
language: java
framework: spring
artifact_type: validation
---
Bean Validation lets you declare constraints on a DTO with annotations such as NotNull, NotBlank, Size, Email and Min. Add the Valid annotation to the controller method parameter so Spring validates the request body before the handler runs. When validation fails Spring raises a MethodArgumentNotValidException, which you can translate into a 400 response with a ControllerAdvice. To add validation to a DTO, put the constraint annotations on its fields and mark the parameter with Valid.
