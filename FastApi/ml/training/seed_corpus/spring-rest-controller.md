---
source_url: https://docs.spring.io/spring-framework/reference/web/webmvc/mvc-controller.html
language: java
framework: spring
artifact_type: controller
---
A REST controller in Spring is a class annotated with RestController. It handles incoming HTTP requests and returns data that is written straight to the response body. Map the class to a base path with RequestMapping, and map each method to an HTTP verb with GetMapping, PostMapping, PutMapping or DeleteMapping. A controller should stay thin: it validates input, calls a service and returns the result. To create a controller, write a public class, add the RestController annotation, inject the service through the constructor and add one handler method per endpoint.
