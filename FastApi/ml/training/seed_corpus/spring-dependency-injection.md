---
source_url: https://docs.spring.io/spring-framework/reference/core/beans/dependencies/factory-collaborators.html
language: java
framework: spring
artifact_type: concept
---
Dependency injection is a technique where an object receives the objects it depends on instead of creating them. Spring supports constructor injection, setter injection and field injection. Constructor injection is preferred because dependencies are explicit, can be final and are easy to replace with fakes in unit tests. Spring resolves the dependencies from the application context, which contains all the beans. When a class has a single constructor, Spring uses it automatically and the Autowired annotation is not needed.
